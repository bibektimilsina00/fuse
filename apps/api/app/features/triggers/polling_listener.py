"""Polling-trigger Listen-mode driver.

When the editor clicks "Listen" on a Gmail / Calendar trigger node,
the HTTP layer creates a waiting Execution row and opens a
PollingListenSlot. This module's Celery task `poll_listen_slot` then
drives the actual wait: it loops calling the trigger's poller every
few seconds with the cursor we snapshotted at slot open, and the
first event that arrives gets dispatched into the waiting Execution
via `execution_engine.dispatch_existing`.

Lifecycle:

  - Snapshot was taken synchronously in the HTTP handler so the cursor
    is already advanced to "now" before this task starts polling. That
    keeps the wait honest — we only surface events that arrive *after*
    the user clicked Listen, not the backlog.
  - The task polls every `LISTEN_POLL_INTERVAL_SECONDS` (5 s) — much
    faster than the production cadence so the editor feels responsive.
  - Each tick checks the Redis cancel flag first so a cancel click
    short-circuits before the next provider HTTP call.
  - On match: advance the cursor (same transaction that dispatches),
    delete the slot, hand off to `dispatch_existing`.
  - On deadline: mark the Execution `timeout` and publish
    `execution_timeout` so the editor's WS state machine can show
    "Listen window expired".
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

from apps.api.app.core.celery import celery_app
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


LISTEN_POLL_INTERVAL_SECONDS = 5


@celery_app.task(name="poll_listen_slot")
def poll_listen_slot(
    execution_id: str,
    workflow_id: str,
    node_id: str,
    deadline_iso: str,
) -> None:
    """Entry point Celery hands the task. Wraps `_run` in `asyncio.run`
    because Celery tasks are sync; everything downstream is async."""
    try:
        asyncio.run(_run(execution_id, workflow_id, node_id, deadline_iso))
    except Exception as exc:  # noqa: BLE001
        logger.error(f"poll_listen_slot crashed: {exc}", exc_info=True)


async def _run(
    execution_id: str,
    workflow_id: str,
    node_id: str,
    deadline_iso: str,
) -> None:
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine import execution_engine
    from apps.api.app.execution_engine.scheduler.integration_polling import (
        get_entry_for_provider,
    )
    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.executions.repository import ExecutionRepository
    from apps.api.app.features.triggers.listen_service import (
        find_polling_slot,
        is_polling_cancelled,
    )
    from apps.api.app.features.triggers.repository import (
        IntegrationTriggerStateRepository,
    )
    from apps.api.app.features.workflows.repository import WorkflowRepository

    try:
        deadline = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
    except ValueError:
        deadline = datetime.now(UTC)

    while True:
        if datetime.now(UTC) >= deadline:
            await _expire(execution_id)
            return

        if await is_polling_cancelled(workflow_id, node_id):
            # `/listen/cancel` already published execution_cancelled and
            # flipped the row — nothing more to do here.
            return

        slot = await find_polling_slot(workflow_id, node_id)
        if slot is None:
            # Slot vanished (cancel, TTL, or someone else claimed). No
            # progress to report.
            return
        if slot.execution_id != execution_id:
            # A newer Listen click overwrote our slot. Hand off cleanly.
            return

        # One poll iteration — fully self-contained DB session so a
        # transient failure doesn't poison the next tick.
        try:
            async with AsyncSessionLocal() as db:
                wf = await WorkflowRepository(db).get_by_id(uuid.UUID(workflow_id))
                if wf is None:
                    await _expire(execution_id, status="failed")
                    return

                entry = get_entry_for_provider(slot.provider)
                if entry is None:
                    logger.warning(
                        "poll_listen_slot: no poller registered for provider %r",
                        slot.provider,
                    )
                    await _expire(execution_id, status="failed")
                    return

                node = _find_node(wf.graph, node_id)
                if node is None:
                    await _expire(execution_id, status="failed")
                    return
                props = (node.get("data") or {}).get("properties") or {}

                cred_service = CredentialService(db)
                token = await _resolve_token(cred_service, slot.credential_id, slot.workspace_id)
                if not token:
                    await _expire(execution_id, status="failed")
                    return

                state_repo = IntegrationTriggerStateRepository(db)
                state = await state_repo.get(wf.id, node_id)
                cursor = state.cursor if state else {}

                matches, new_cursor = await entry.poller(token, cursor, props)

                # Always advance the cursor — even on a no-match tick —
                # so the production scheduler resumes from the same
                # boundary when listen finishes.
                if state is not None:
                    await state_repo.upsert(
                        workflow_id=wf.id,
                        workspace_id=wf.workspace_id,
                        node_id=node_id,
                        provider=slot.provider,
                        cursor=new_cursor,
                        next_poll_at=state.next_poll_at,
                        last_error=None,
                    )
                    await db.commit()

                if matches:
                    # Hand off the first match — Listen is single-shot.
                    payload = matches[0]
                    node_type = str(node.get("type") or "")
                    # Close the slot before dispatching so a retry in
                    # dispatch_existing can't re-fire it.
                    from apps.api.app.features.triggers.listen_service import (
                        close_polling_slot,
                    )

                    await close_polling_slot(workflow_id, node_id)
                    await execution_engine.dispatch_existing(
                        execution_id=uuid.UUID(execution_id),
                        workflow_id=wf.id,
                        graph=wf.graph,
                        trigger_type=node_type or "listen",
                        input_data=payload,
                    )
                    await _publish(
                        execution_id,
                        {
                            "type": "execution_listen_matched",
                            "execution_id": execution_id,
                            "node_id": node_id,
                            "timestamp": _iso_now(),
                        },
                    )
                    return
        except Exception as exc:  # noqa: BLE001
            # Don't kill the listen loop on a transient API hiccup;
            # surface to logs and keep polling until deadline.
            logger.warning(f"poll_listen_slot tick failed: {exc}")

        # Sleep is capped by the remaining deadline so the last tick
        # doesn't oversleep past the timeout window.
        remaining = (deadline - datetime.now(UTC)).total_seconds()
        if remaining <= 0:
            await _expire(execution_id)
            return
        await asyncio.sleep(min(LISTEN_POLL_INTERVAL_SECONDS, max(1.0, remaining)))

        # Bail if the row was cancelled out from under us between ticks.
        async with AsyncSessionLocal() as db:
            row = await ExecutionRepository(db).get_by_id(uuid.UUID(execution_id))
            if row is None or row.status not in ("waiting",):
                return


async def _expire(execution_id: str, status: str = "timeout") -> None:
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.features.executions.repository import ExecutionRepository

    try:
        async with AsyncSessionLocal() as db:
            await ExecutionRepository(db).update_status(uuid.UUID(execution_id), status)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"poll_listen_slot: failed to mark {execution_id} {status}: {exc}")

    await _publish(
        execution_id,
        {
            "type": "execution_timeout" if status == "timeout" else "execution_failed",
            "execution_id": execution_id,
            "status": status,
            "message": (
                "Listen window expired — no event arrived. Try again."
                if status == "timeout"
                else "Listen failed."
            ),
            "timestamp": _iso_now(),
        },
    )


async def _publish(execution_id: str, payload: dict) -> None:
    from apps.api.app.core.redis import get_redis

    try:
        redis = await get_redis()
        await redis.publish(f"execution:{execution_id}", json.dumps(payload))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"poll_listen_slot pubsub failed for {execution_id}: {exc}")


async def _resolve_token(cred_service, credential_id: str, workspace_id: str) -> str | None:
    if not credential_id or not workspace_id:
        return None
    try:
        cred_uuid = uuid.UUID(credential_id)
        ws_uuid = uuid.UUID(workspace_id)
    except (ValueError, TypeError):
        return None
    cred = await cred_service.repo.get_by_id_and_workspace(cred_uuid, ws_uuid)
    if cred is None:
        return None
    data = await cred_service.get_decrypted_credential(cred)
    if not isinstance(data, dict):
        return None
    token = data.get("access_token")
    return str(token) if isinstance(token, str) else None


def _find_node(graph: dict | None, node_id: str) -> dict | None:
    for node in (graph or {}).get("nodes") or []:
        if isinstance(node, dict) and str(node.get("id") or "") == node_id:
            return node
    return None


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")

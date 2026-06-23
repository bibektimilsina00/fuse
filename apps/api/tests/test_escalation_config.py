"""Workspace escalation config tests — repository + HTTP route + escalate_from_run."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from apps.api.app.features.escalation import (
    EscalationConfig,
    escalate_from_run,
    load_workspace_config,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ── load_workspace_config / escalate_from_run ──────────────────────


@pytest.mark.anyio
async def test_load_workspace_config_returns_none_when_missing():
    fake_db = MagicMock()
    with patch(
        "apps.api.app.features.escalation.repository.EscalationConfigRepository.get_for_workspace",
        new=AsyncMock(return_value=None),
    ):
        result = await load_workspace_config(fake_db, uuid4())
    assert result is None


@pytest.mark.anyio
async def test_load_workspace_config_maps_row_to_schema():
    row = MagicMock(
        workspace_id=uuid4(),
        slack_webhook_url="https://hooks.slack.com/x",
        email_to=None,
        webhook_url=None,
        enabled=True,
    )
    with patch(
        "apps.api.app.features.escalation.repository.EscalationConfigRepository.get_for_workspace",
        new=AsyncMock(return_value=row),
    ):
        cfg = await load_workspace_config(MagicMock(), row.workspace_id)
    assert isinstance(cfg, EscalationConfig)
    assert cfg.slack_webhook_url == "https://hooks.slack.com/x"
    assert cfg.enabled is True


@pytest.mark.anyio
async def test_escalate_from_run_silent_when_no_config():
    with patch(
        "apps.api.app.features.escalation.service.load_workspace_config",
        new=AsyncMock(return_value=None),
    ):
        result = await escalate_from_run(
            db=MagicMock(),
            workspace_id=uuid4(),
            workflow_id=uuid4(),
            workflow_name="x",
            run_id=uuid4(),
            status="failed",
            failure_reason="x",
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            trace=None,
            usage=None,
        )
    assert result["sent"] is False
    assert result["error"] == "no_config"


@pytest.mark.anyio
async def test_escalate_from_run_dispatches_when_configured():
    ws_id = uuid4()
    cfg = EscalationConfig(workspace_id=ws_id, webhook_url="https://example.com/hook")
    dispatch_mock = AsyncMock(return_value={"sent": True, "channel": "webhook", "error": None})
    with (
        patch(
            "apps.api.app.features.escalation.service.load_workspace_config",
            new=AsyncMock(return_value=cfg),
        ),
        patch(
            "apps.api.app.features.escalation.service.EscalationService.dispatch",
            new=dispatch_mock,
        ),
    ):
        result = await escalate_from_run(
            db=MagicMock(),
            workspace_id=ws_id,
            workflow_id=uuid4(),
            workflow_name="x",
            run_id=uuid4(),
            status="failed",
            failure_reason="x",
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            trace=None,
            usage=None,
        )
    assert result["sent"] is True
    dispatch_mock.assert_awaited_once()


@pytest.mark.anyio
async def test_escalate_from_run_swallows_config_load_errors():
    with patch(
        "apps.api.app.features.escalation.service.load_workspace_config",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        result = await escalate_from_run(
            db=MagicMock(),
            workspace_id=uuid4(),
            workflow_id=uuid4(),
            workflow_name="x",
            run_id=uuid4(),
            status="failed",
            failure_reason="x",
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            trace=None,
            usage=None,
        )
    assert result["sent"] is False
    assert "config_load_failed" in (result["error"] or "")

"""HTTP surface for the workspace escalation config.

Routes:
- ``GET /workspaces/{workspace_id}/escalation-config`` → current row or null
- ``PUT /workspaces/{workspace_id}/escalation-config`` → upsert
- ``DELETE /workspaces/{workspace_id}/escalation-config`` → remove

Workspace membership is enforced by ``WorkspaceService.require_member``
so non-members get a 404 before they can probe.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.shared.dependencies import get_current_user

from .repository import EscalationConfigRepository

router = APIRouter()


class EscalationConfigOut(BaseModel):
    workspace_id: uuid.UUID
    enabled: bool
    slack_webhook_url: str | None
    email_to: str | None
    webhook_url: str | None


class EscalationConfigIn(BaseModel):
    enabled: bool = True
    slack_webhook_url: str | None = None
    email_to: str | None = None
    webhook_url: str | None = None


@router.get(
    "/{workspace_id}/escalation-config",
    response_model=EscalationConfigOut | None,
)
async def get_escalation_config(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the workspace's escalation config or ``null`` when unset."""
    await WorkspaceService(db).require_member(workspace_id, current_user)
    row = await EscalationConfigRepository(db).get_for_workspace(workspace_id)
    if row is None:
        return None
    return EscalationConfigOut(
        workspace_id=row.workspace_id,
        enabled=row.enabled,
        slack_webhook_url=row.slack_webhook_url,
        email_to=row.email_to,
        webhook_url=row.webhook_url,
    )


@router.put(
    "/{workspace_id}/escalation-config",
    response_model=EscalationConfigOut,
)
async def put_escalation_config(
    workspace_id: uuid.UUID,
    body: EscalationConfigIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or replace the workspace's escalation config row."""
    await WorkspaceService(db).require_member(workspace_id, current_user)
    row = await EscalationConfigRepository(db).upsert(
        workspace_id,
        enabled=body.enabled,
        slack_webhook_url=_norm(body.slack_webhook_url),
        email_to=_norm(body.email_to),
        webhook_url=_norm(body.webhook_url),
    )
    return EscalationConfigOut(
        workspace_id=row.workspace_id,
        enabled=row.enabled,
        slack_webhook_url=row.slack_webhook_url,
        email_to=row.email_to,
        webhook_url=row.webhook_url,
    )


@router.delete(
    "/{workspace_id}/escalation-config",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_escalation_config(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove the workspace's escalation config row (returns to silent)."""
    await WorkspaceService(db).require_member(workspace_id, current_user)
    await EscalationConfigRepository(db).delete(workspace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _norm(value: str | None) -> str | None:
    """Treat empty / whitespace-only strings as None — the UI sends ``""``
    when the user clears a field, and we don't want to record empty
    strings as valid channels."""
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None

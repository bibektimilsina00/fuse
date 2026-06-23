"""Repository for the workspace escalation config table.

Single-row-per-workspace, so all operations key on ``workspace_id``.
Upsert keeps the row mutation atomic — the router never has to
decide create-vs-update.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import WorkspaceEscalationConfig


class EscalationConfigRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_for_workspace(self, workspace_id: UUID) -> WorkspaceEscalationConfig | None:
        stmt = select(WorkspaceEscalationConfig).where(
            WorkspaceEscalationConfig.workspace_id == workspace_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        workspace_id: UUID,
        *,
        enabled: bool,
        slack_webhook_url: str | None,
        email_to: str | None,
        webhook_url: str | None,
    ) -> WorkspaceEscalationConfig:
        row = await self.get_for_workspace(workspace_id)
        if row is None:
            row = WorkspaceEscalationConfig(
                workspace_id=workspace_id,
                enabled=enabled,
                slack_webhook_url=slack_webhook_url,
                email_to=email_to,
                webhook_url=webhook_url,
            )
            self.db.add(row)
        else:
            row.enabled = enabled
            row.slack_webhook_url = slack_webhook_url
            row.email_to = email_to
            row.webhook_url = webhook_url
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def delete(self, workspace_id: UUID) -> bool:
        row = await self.get_for_workspace(workspace_id)
        if row is None:
            return False
        await self.db.delete(row)
        await self.db.commit()
        return True

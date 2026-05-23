import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.features.logs.models import AuditLog


class AuditLogRepository:
    """Repository for handling database operations on AuditLog models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entry: AuditLog) -> AuditLog:
        """Persist a new audit log entry."""
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        resource_type: str | None = None,
        limit: int = 50,
    ) -> list[AuditLog]:
        """List audit logs in a workspace with optional resource type filter."""
        q = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.workspace_id == workspace_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        if resource_type:
            q = q.where(AuditLog.resource_type == resource_type)
        result = await self.db.execute(q)
        return list(result.scalars().all())

import uuid
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.executions.repository import ExecutionRepository
from apps.api.app.features.logs.models import AuditLog
from apps.api.app.features.logs.repository import AuditLogRepository
from apps.api.app.features.logs.schemas import ExecutionLogOut


class LogsService:
    """Service layer executing business logic for logs and audit logging."""

    def __init__(self, db: AsyncSession):
        self.repository = AuditLogRepository(db)
        self.execution_repository = ExecutionRepository(db)

    async def log(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        resource_name: str,
        meta: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Create and persist a new audit log entry."""
        entry = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            meta=meta,
        )
        return await self.repository.create(entry)

    async def list_for_workspace(
        self,
        workspace_id: uuid.UUID,
        resource_type: str | None = None,
        limit: int = 50,
    ) -> list[AuditLog]:
        """List audit logs in a workspace."""
        return await self.repository.list_by_workspace(
            workspace_id=workspace_id,
            resource_type=resource_type,
            limit=limit,
        )

    async def get_workspace_logs(
        self, workspace_id: uuid.UUID, limit: int = 100, level: str | None = None
    ) -> list[ExecutionLogOut]:
        """Retrieve execution logs for a workspace."""
        db_level = None
        if level:
            if level == "err":
                db_level = "error"
            elif level in ("info", "warn"):
                db_level = level

        logs = await self.execution_repository.get_logs_by_workspace(
            workspace_id=workspace_id,
            limit=limit,
            level=db_level,
        )
        return [ExecutionLogOut(**log) for log in logs]


def get_logs_service(db: AsyncSession = Depends(get_db)) -> LogsService:
    """Dependency helper for LogsService."""
    return LogsService(db)

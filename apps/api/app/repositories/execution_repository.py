import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.models import Execution, ExecutionLog


class ExecutionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, execution: Execution) -> Execution:
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    async def get_by_id(self, execution_id: uuid.UUID) -> Execution | None:
        result = await self.db.execute(
            select(Execution)
            .where(Execution.id == execution_id)
            .options(selectinload(Execution.logs))
        )
        return result.scalar_one_or_none()

    async def list_by_workflow(self, workflow_id: uuid.UUID) -> list[Execution]:
        result = await self.db.execute(
            select(Execution)
            .where(Execution.workflow_id == workflow_id)
            .order_by(Execution.started_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        execution_id: uuid.UUID,
        status: str,
        output_data: dict | None = None,
    ) -> None:
        result = await self.db.execute(select(Execution).where(Execution.id == execution_id))
        execution = result.scalar_one_or_none()
        if execution:
            execution.status = status
            if status == "running":
                execution.started_at = datetime.now(UTC)
            elif status in ("completed", "failed"):
                execution.finished_at = datetime.now(UTC)
            if output_data is not None:
                execution.output_data = output_data
            await self.db.commit()

    async def add_log(
        self,
        execution_id: uuid.UUID,
        message: str,
        level: str = "info",
        node_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        log = ExecutionLog(
            execution_id=execution_id,
            node_id=node_id,
            level=level,
            message=message,
            payload=payload,
        )
        self.db.add(log)
        await self.db.commit()

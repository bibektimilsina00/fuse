import uuid

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.core.logger import get_logger
from apps.api.app.features.executions.models import Execution

logger = get_logger(__name__)


class ExecutionEngine:
    async def trigger_workflow(
        self,
        workflow_id: uuid.UUID,
        graph: dict,
        trigger_type: str = "manual",
        input_data: dict | None = None,
    ) -> uuid.UUID:
        async with AsyncSessionLocal() as db:
            # Create Execution record (status: pending)
            execution = Execution(
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                status="pending",
                input_data=input_data or {},
            )
            db.add(execution)
            await db.commit()
            await db.refresh(execution)

            execution_id = execution.id

        # Enqueue Celery task AFTER DB commit (so worker can query it)
        from apps.worker.app.jobs.tasks import execute_workflow

        execute_workflow.delay(
            execution_id=str(execution_id),
            workflow_id=str(workflow_id),
            graph=graph,
            trigger_data=input_data or {},
        )

        logger.info(f"Enqueued execution {execution_id} for workflow {workflow_id}")
        return execution_id


execution_engine = ExecutionEngine()

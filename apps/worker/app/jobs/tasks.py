import asyncio
import uuid
from typing import Any

from apps.api.app.core.celery import celery_app
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="execute_workflow")
def execute_workflow(execution_id: str, workflow_id: str, graph: dict, trigger_data: dict):
    """Main workflow execution task. Runs async WorkflowRunner in sync Celery context."""
    try:
        asyncio.run(_run_workflow(execution_id, workflow_id, graph, trigger_data))
    except Exception as e:
        logger.error(f"execute_workflow task failed: {e}", exc_info=True)


async def _run_workflow(execution_id: str, workflow_id: str, graph: dict, trigger_data: dict):
    import json

    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.credential_manager.encryption.aes import encryption_service
    from apps.api.app.execution_engine.engine.event_emitter import RedisEventEmitter
    from apps.api.app.execution_engine.engine.workflow_runner import WorkflowRunner
    from apps.api.app.repositories.credential_repository import CredentialRepository
    from apps.api.app.repositories.execution_repository import ExecutionRepository
    from apps.api.app.repositories.workflow_repository import WorkflowRepository

    emitter = RedisEventEmitter(execution_id)
    credentials_list = []
    async with AsyncSessionLocal() as db:
        exec_repo = ExecutionRepository(db)
        wf_repo = WorkflowRepository(db)
        cred_repo = CredentialRepository(db)

        await exec_repo.update_status(uuid.UUID(execution_id), "running")
        await exec_repo.add_log(uuid.UUID(execution_id), "Workflow execution started", level="info")

        await emitter.emit("execution_started", {})

        # Fetch user_id from workflow
        workflow = await wf_repo.get_by_id(uuid.UUID(workflow_id))
        if workflow:
            logger.info(
                f"Fetching credentials for user {workflow.user_id} (workflow {workflow_id})"
            )
            # Fetch and decrypt all credentials for this user
            user_credentials = await cred_repo.list_by_user(workflow.user_id)
            logger.info(f"Found {len(user_credentials)} credentials for user {workflow.user_id}")

            for cred in user_credentials:
                try:
                    decrypted_data = json.loads(encryption_service.decrypt(cred.encrypted_data))
                    logger.info(
                        f"Loaded credential: ID={cred.id}, Type={cred.type}, Name={cred.name}"
                    )
                    credentials_list.append(
                        {"id": str(cred.id), "type": cred.type, "data": decrypted_data}
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to decrypt credential {cred.id} ({cred.type}). "
                        "This usually means the ENCRYPTION_KEY has changed. "
                        "Please delete and re-add this Slack account in the settings. "
                        f"Error: {str(e)}"
                    )
        else:
            logger.error(f"Workflow {workflow_id} not found when fetching credentials")

    # 2. Execution Phase: Run the runner
    try:

        async def on_log(
            message: str, level: str = "info", node_id: str | None = None, payload: Any = None
        ):
            async with AsyncSessionLocal() as db:
                repo = ExecutionRepository(db)
                await repo.add_log(
                    uuid.UUID(execution_id), message, level=level, node_id=node_id, payload=payload
                )

        async with AsyncSessionLocal() as db:
            runner = WorkflowRunner(
                workflow_id=workflow_id,
                execution_id=execution_id,
                graph=graph,
                db=db,
                on_log=on_log,
                credentials=credentials_list,
                emitter=emitter,
            )
            output = await runner.run(trigger_data)

        # 3. Finish Phase: Mark completed
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.update_status(uuid.UUID(execution_id), "completed", output_data=output)
            await repo.add_log(
                uuid.UUID(execution_id), "Workflow execution completed", level="info"
            )
            await emitter.emit("execution_completed", {"status": "completed", "output": output})

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Workflow {workflow_id} failed: {error_msg}")
        async with AsyncSessionLocal() as db:
            repo = ExecutionRepository(db)
            await repo.update_status(uuid.UUID(execution_id), "failed")
            await repo.add_log(uuid.UUID(execution_id), error_msg, level="error")
            await emitter.emit("execution_failed", {"status": "failed", "error": error_msg})
        raise

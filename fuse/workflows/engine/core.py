import uuid
from typing import Any, Dict, Optional
from fuse.workflows.engine.scheduler import WorkflowScheduler
from fuse.workflows.engine.state import WorkflowState

class WorkflowEngine:
    """
    Core entry point for workflow execution.
    Rule 1: Library-like behavior, callable via plain Python functions.
    Rule 3: Extracted into a separate service later without refactoring.
    """
    
    @staticmethod
    def start_execution(workflow_id: uuid.UUID, trigger_data: Optional[Dict[str, Any]] = None) -> uuid.UUID:
        """Starts a new workflow execution."""
        from fuse.workflows.models import WorkflowExecution
        import json
        from fuse.database import engine as db_engine
        from sqlmodel import Session

        # Create execution record
        with Session(db_engine) as session:
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                status="pending",
                trigger_data=json.dumps(trigger_data) if trigger_data else None
            )
            session.add(execution)
            session.commit()
            session.refresh(execution)
            execution_id = execution.id

        scheduler = WorkflowScheduler(workflow_id, execution_id)
        scheduler.start_workflow(trigger_data)
        return execution_id

    @staticmethod
    async def run_node_sync(execution_id: uuid.UUID, node_execution_id: uuid.UUID):
        """Executes a single node synchronously (but awaited)."""
        from fuse.workflows.engine.executor import run_node_logic
        await run_node_logic(execution_id, node_execution_id)

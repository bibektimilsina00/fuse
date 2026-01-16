import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlmodel import Session, select
from src.database import engine as db_engine
from src.workflows.models import Workflow, WorkflowExecution, NodeExecution
from src.workflows.engine.errors import WorkflowNotFoundError, ExecutionNotFoundError

from src.workflows.engine.constants import ExecutionStatus

VALID_TRANSITIONS = {
    ExecutionStatus.PENDING.value: {ExecutionStatus.RUNNING.value, ExecutionStatus.CANCELLED.value, ExecutionStatus.FAILED.value},
    ExecutionStatus.RUNNING.value: {ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value, ExecutionStatus.CANCELLED.value},
    ExecutionStatus.COMPLETED.value: set(),
    ExecutionStatus.FAILED.value: {ExecutionStatus.PENDING.value, ExecutionStatus.RUNNING.value}, # Allow manual retry or re-run
    ExecutionStatus.CANCELLED.value: {ExecutionStatus.PENDING.value}, # Allow restart
}

class WorkflowState:
    def __init__(self, workflow_id: uuid.UUID, execution_id: uuid.UUID):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
    
    def _validate_transition(self, current_status: str, new_status: str, entity_type: str = "Execution") -> bool:
        if current_status == new_status:
            return True
            
        # Ignore validation if current status is missing/None
        if not current_status:
            return True

        allowed = VALID_TRANSITIONS.get(current_status or "pending")
        if allowed is None:
            return True
            
        return new_status in allowed

    def get_session(self):
        return Session(db_engine)

    def get_workflow(self, session: Session) -> Workflow:
        workflow = session.get(Workflow, self.workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {self.workflow_id} not found")
        return workflow

    def get_execution(self, session: Session) -> WorkflowExecution:
        execution = session.get(WorkflowExecution, self.execution_id)
        if not execution:
            raise ExecutionNotFoundError(f"Execution {self.execution_id} not found")
        return execution

    def update_execution_status(self, session: Session, status: str, trigger_data: Optional[Dict] = None):
        execution = self.get_execution(session)
        if not self._validate_transition(execution.status, status, "Workflow"):
            return
        
        execution.status = status
        if status == "running":
            execution.started_at = datetime.utcnow()
            if trigger_data:
                execution.trigger_data = json.dumps(trigger_data)
        elif status in ["completed", "failed"]:
            execution.completed_at = datetime.utcnow()
        session.add(execution)
        session.commit()

    def create_node_execution(self, session: Session, node_id: str, node_type: str, input_data: Any) -> NodeExecution:
        node_execution = NodeExecution(
            workflow_execution_id=self.execution_id,
            node_id=node_id,
            node_type=node_type,
            status="pending",
            input_data=json.dumps(input_data) if input_data else None
        )
        session.add(node_execution)
        session.commit()
        session.refresh(node_execution)
        return node_execution

    def update_node_status(self, session: Session, node_execution_id: uuid.UUID, status: str, result: Any = None, error: str = None):
        node_execution = session.get(NodeExecution, node_execution_id)
        if not node_execution:
            return
        
        if not self._validate_transition(node_execution.status, status, "Node"):
            return

        node_execution.status = status
        if status == "running":
            node_execution.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            node_execution.completed_at = datetime.utcnow()
            if result is not None:
                node_execution.output_data = json.dumps(result)
            if error is not None:
                node_execution.error = error
        
        session.add(node_execution)
        session.commit()

    def get_active_node_executions(self, session: Session):
        return session.exec(
            select(NodeExecution)
            .where(NodeExecution.workflow_execution_id == self.execution_id)
            .where(NodeExecution.status.in_(["pending", "running"]))
        ).all()

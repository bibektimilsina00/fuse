from typing import List, Dict, Any
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem
from fuse.database import engine as db_engine
from sqlmodel import Session, select
from fuse.datatables.models import DataTable

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Data Table trigger execution.
    The trigger payload is passed directly from the EventService via start_execution.
    """
    # trigger_data comes from context.input_data for start nodes
    trigger_data = context.input_data
    if not trigger_data:
        # Fallback for manual test run
        return [WorkflowItem(json={"message": "No trigger data provided", "action": "manual"})]
        
    return [WorkflowItem(json=trigger_data)]

async def get_table_options(context: Dict[str, Any], deps: Dict[str, Any]) -> List[Dict[str, str]]:
    """Fetch available data tables for the user."""
    # context here is a dict with user_id passed from router.get_node_options
    user_id = context.get("user_id")
    if not user_id:
        return []
        
    with Session(db_engine) as session:
        statement = select(DataTable).where(DataTable.owner_id == user_id)
        tables = session.exec(statement).all()
        return [{"label": t.name, "value": str(t.id)} for t in tables]

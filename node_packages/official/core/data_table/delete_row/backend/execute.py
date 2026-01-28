import uuid
from typing import List, Dict, Any
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem
from fuse.database import engine as db_engine
from sqlmodel import Session, select
from fuse.datatables.models import DataTable, DataTableRow
from fuse.datatables.service import data_table_row

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Delete a row from a data table.
    """
    config = context.resolve_config()
    table_id_str = config.get("table_id")
    row_id_str = config.get("row_id")
    
    if not table_id_str or not row_id_str:
        raise ValueError("table_id and row_id are required")
        
    try:
        table_id = uuid.UUID(table_id_str)
        row_id = uuid.UUID(row_id_str)
    except ValueError:
        raise ValueError(f"Invalid UUID format for table_id or row_id")
    
    with Session(db_engine) as session:
        db_obj = session.get(DataTableRow, row_id)
        if not db_obj or db_obj.table_id != table_id:
            # Already deleted or not found
            return [WorkflowItem(json={"success": False, "message": "Row not found"})]
            
        # Use our event-emitting service method
        data_table_row.remove_with_event(session=session, id=row_id)
        return [WorkflowItem(json={"success": True, "row_id": row_id_str})]

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

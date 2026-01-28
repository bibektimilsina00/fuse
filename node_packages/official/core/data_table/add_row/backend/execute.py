import uuid
from typing import List, Dict, Any
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem
from fuse.database import engine as db_engine
from sqlmodel import Session, select
from fuse.datatables.models import DataTable
from fuse.datatables.schemas import DataTableRowCreate
from fuse.datatables.service import data_table_row

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Add a row to a data table.
    """
    config = context.resolve_config()
    table_id_str = config.get("table_id")
    row_data = config.get("row_data")
    
    if not table_id_str:
        raise ValueError("table_id is required")
    if not row_data:
        raise ValueError("row_data is required")
        
    try:
        table_id = uuid.UUID(table_id_str)
    except ValueError:
        raise ValueError(f"Invalid table_id format: {table_id_str}")
    
    with Session(db_engine) as session:
        # Use our event-emitting service method
        obj_in = DataTableRowCreate(data=row_data)
        db_obj = data_table_row.create_with_event(session=session, obj_in=obj_in, table_id=table_id)
        
        return [WorkflowItem(json={
            "row_id": str(db_obj.id),
            "data": db_obj.data,
            "table_id": str(table_id)
        })]

async def get_table_options(context: Dict[str, Any], deps: Dict[str, Any]) -> List[Dict[str, str]]:
    """Fetch available data tables for the user."""
    user_id = context.get("user_id")
    if not user_id:
        return []
        
    with Session(db_engine) as session:
        statement = select(DataTable).where(DataTable.owner_id == user_id)
        tables = session.exec(statement).all()
        return [{"label": t.name, "value": str(t.id)} for t in tables]

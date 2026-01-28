import uuid
from typing import List, Dict, Any
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem
from fuse.database import engine as db_engine
from sqlmodel import Session, select
from fuse.datatables.models import DataTable, DataTableRow

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Get rows from a data table.
    """
    config = context.resolve_config()
    table_id_str = config.get("table_id")
    limit = config.get("limit", 100)
    
    if not table_id_str:
        raise ValueError("table_id is required")
        
    try:
        table_id = uuid.UUID(table_id_str)
    except ValueError:
        raise ValueError(f"Invalid table_id format: {table_id_str}")
    
    with Session(db_engine) as session:
        statement = select(DataTableRow).where(DataTableRow.table_id == table_id).limit(limit)
        rows = session.exec(statement).all()
        
        # Map to WorkflowItems for downstream processing
        return [WorkflowItem(json=row.data) for row in rows]

async def get_table_options(context: Dict[str, Any], deps: Dict[str, Any]) -> List[Dict[str, str]]:
    """Fetch available data tables for the user."""
    user_id = context.get("user_id")
    if not user_id:
        return []
        
    with Session(db_engine) as session:
        statement = select(DataTable).where(DataTable.owner_id == user_id)
        tables = session.exec(statement).all()
        return [{"label": t.name, "value": str(t.id)} for t in tables]

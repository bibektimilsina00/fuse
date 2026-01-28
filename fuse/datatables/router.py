import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from fuse.auth.dependencies import CurrentUser, SessionDep
from fuse.datatables.schemas import (
    DataTableCreate,
    DataTableUpdate,
    DataTableResponse,
    DataTableRowCreate,
    DataTableRowUpdate,
    DataTableRowResponse,
)
from fuse.datatables.service import data_table, data_table_row

router = APIRouter()

@router.get("/")
def get_tables(session: SessionDep, current_user: CurrentUser) -> Any:
    """Retrieve all tables for the current user."""
    tables = data_table.get_by_owner(session=session, owner_id=current_user.id)
    # Add row counts to each table
    result = []
    for table in tables:
        table_dict = {
            "id": str(table.id),
            "name": table.name,
            "description": table.description,
            "schema_definition": table.schema_definition,
            "created_at": table.created_at.isoformat(),
            "updated_at": table.updated_at.isoformat(),
            "owner_id": str(table.owner_id),
            "_count": {
                "rows": len(table.rows) if table.rows else 0
            }
        }
        result.append(table_dict)
    return result

@router.post("/", response_model=DataTableResponse)
def create_table(session: SessionDep, current_user: CurrentUser, obj_in: DataTableCreate) -> Any:
    """Create a new data table."""
    db_obj = data_table.model(**obj_in.model_dump(), owner_id=current_user.id)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

@router.get("/{table_id}", response_model=DataTableResponse)
def get_table(session: SessionDep, current_user: CurrentUser, table_id: uuid.UUID) -> Any:
    """Get a specific table by ID."""
    db_obj = data_table.get(session=session, id=table_id)
    if not db_obj or db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Table not found")
    return db_obj

@router.patch("/{table_id}", response_model=DataTableResponse)
def update_table(
    session: SessionDep, current_user: CurrentUser, table_id: uuid.UUID, obj_in: DataTableUpdate
) -> Any:
    """Update a specific table."""
    db_obj = data_table.get(session=session, id=table_id)
    if not db_obj or db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Table not found")
    return data_table.update(session=session, db_obj=db_obj, obj_in=obj_in)

@router.delete("/{table_id}")
def delete_table(session: SessionDep, current_user: CurrentUser, table_id: uuid.UUID) -> Any:
    """Delete a table."""
    db_obj = data_table.get(session=session, id=table_id)
    if not db_obj or db_obj.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Table not found")
    data_table.remove(session=session, id=table_id)
    return {"status": "success"}

# --- Row Operations ---

@router.get("/{table_id}/rows", response_model=List[DataTableRowResponse])
def get_table_rows(session: SessionDep, current_user: CurrentUser, table_id: uuid.UUID) -> Any:
    """Retrieve all rows for a specific table."""
    db_table = data_table.get(session=session, id=table_id)
    if not db_table or db_table.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Table not found")
    return data_table_row.get_by_table_id(session=session, table_id=table_id)

@router.post("/{table_id}/rows", response_model=DataTableRowResponse)
def create_table_row(
    session: SessionDep, current_user: CurrentUser, table_id: uuid.UUID, obj_in: DataTableRowCreate
) -> Any:
    """Create a new row in a table."""
    db_table = data_table.get(session=session, id=table_id)
    if not db_table or db_table.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Table not found")
    
    return data_table_row.create_with_event(session=session, obj_in=obj_in, table_id=table_id)

@router.patch("/{table_id}/rows/{row_id}", response_model=DataTableRowResponse)
def update_table_row(
    session: SessionDep, current_user: CurrentUser, table_id: uuid.UUID, row_id: uuid.UUID, obj_in: DataTableRowUpdate
) -> Any:
    """Update a row in a table."""
    db_table = data_table.get(session=session, id=table_id)
    if not db_table or db_table.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Table not found")
    
    db_obj = data_table_row.get(session=session, id=row_id)
    if not db_obj or db_obj.table_id != table_id:
        raise HTTPException(status_code=404, detail="Row not found")
        
    return data_table_row.update_with_event(session=session, db_obj=db_obj, obj_in=obj_in)

@router.delete("/{table_id}/rows/{row_id}")
def delete_table_row(
    session: SessionDep, current_user: CurrentUser, table_id: uuid.UUID, row_id: uuid.UUID
) -> Any:
    """Delete a row in a table."""
    db_table = data_table.get(session=session, id=table_id)
    if not db_table or db_table.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Table not found")
    
    db_obj = data_table_row.get(session=session, id=row_id)
    if not db_obj or db_obj.table_id != table_id:
        raise HTTPException(status_code=404, detail="Row not found")
        
    data_table_row.remove_with_event(session=session, id=row_id)
    return {"status": "success"}

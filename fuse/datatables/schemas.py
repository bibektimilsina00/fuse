import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class DataTableBase(BaseModel):
    name: str
    description: Optional[str] = None
    schema_definition: List[Dict[str, Any]]

class DataTableCreate(DataTableBase):
    pass

class DataTableUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_definition: Optional[List[Dict[str, Any]]] = None

class DataTableResponse(DataTableBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID

    class Config:
        from_attributes = True

class DataTableRowBase(BaseModel):
    data: Dict[str, Any]

class DataTableRowCreate(DataTableRowBase):
    pass

class DataTableRowUpdate(DataTableRowBase):
    pass

class DataTableRowResponse(DataTableRowBase):
    id: uuid.UUID
    table_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import JSON

class DataTable(SQLModel, table=True):
    __tablename__ = "data_table"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    schema_definition: List[Dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    
    rows: List["DataTableRow"] = Relationship(back_populates="table", cascade_delete=True, sa_relationship_kwargs={"lazy": "selectin"})

class DataTableRow(SQLModel, table=True):
    __tablename__ = "data_table_row"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    table_id: uuid.UUID = Field(foreign_key="data_table.id", nullable=False, ondelete="CASCADE")
    data: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    table: DataTable = Relationship(back_populates="rows")

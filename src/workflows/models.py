import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import JSON

from src.workflows.schemas import WorkflowBase

if TYPE_CHECKING:
    from src.auth.models import User


class WorkflowNode(SQLModel, table=True):
    """Workflow node database model"""
    __tablename__ = "workflow_nodes"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", nullable=False, ondelete="CASCADE")
    node_id: str
    node_type: str  # trigger, action, ai, condition
    position_x: float
    position_y: float
    label: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    spec: Dict = Field(default_factory=dict, sa_type=JSON)
    
    workflow: "Workflow" = Relationship(back_populates="nodes")


class WorkflowEdge(SQLModel, table=True):
    """Workflow edge (connection) database model"""
    __tablename__ = "workflow_edges"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", nullable=False, ondelete="CASCADE")
    edge_id: str
    source: str
    target: str
    label: Optional[str] = None
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    
    workflow: "Workflow" = Relationship(back_populates="edges")



class Workflow(WorkflowBase, table=True):
    """Workflow database model"""
    __tablename__ = "workflow"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # New V2 config blobs
    execution_config: Dict = Field(default_factory=dict, sa_type=JSON)
    observability_config: Dict = Field(default_factory=dict, sa_type=JSON)
    ai_metadata: Dict = Field(default_factory=dict, sa_type=JSON)
    
    owner: "User" = Relationship(back_populates="workflows")
    nodes: List["WorkflowNode"] = Relationship(back_populates="workflow", cascade_delete=True, sa_relationship_kwargs={"lazy": "selectin"})
    edges: List["WorkflowEdge"] = Relationship(back_populates="workflow", cascade_delete=True, sa_relationship_kwargs={"lazy": "selectin"})
    executions: List["WorkflowExecution"] = Relationship(back_populates="workflow", cascade_delete=True)


class WorkflowExecution(SQLModel, table=True):
    """Workflow execution history"""
    __tablename__ = "workflow_execution"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_id: uuid.UUID = Field(foreign_key="workflow.id", nullable=False, ondelete="CASCADE")
    status: str = Field(default="pending")  # pending, running, completed, failed
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    trigger_data: Optional[str] = None  # JSON string of trigger payload

    workflow: "Workflow" = Relationship(back_populates="executions")
    node_executions: List["NodeExecution"] = Relationship(back_populates="workflow_execution", cascade_delete=True)


class NodeExecution(SQLModel, table=True):
    """Node execution history"""
    __tablename__ = "node_execution"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workflow_execution_id: uuid.UUID = Field(foreign_key="workflow_execution.id", nullable=False, ondelete="CASCADE")
    node_id: str
    node_type: str
    status: str = Field(default="pending")  # pending, running, completed, failed
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    input_data: Optional[str] = None  # JSON string
    output_data: Optional[str] = None  # JSON string
    error: Optional[str] = None

    workflow_execution: "WorkflowExecution" = Relationship(back_populates="node_executions")


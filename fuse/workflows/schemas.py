import uuid
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from sqlmodel import Field, SQLModel
from pydantic import BaseModel


# Shared properties
class WorkflowBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    status: str = Field(default="draft")  # draft, active, inactive
    tags: Optional[str] = None  # JSON array as string


# Properties to receive on workflow creation
class WorkflowCreate(WorkflowBase):
    pass


# Properties to receive on workflow update
class WorkflowUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = None
    tags: Optional[str] = None


# --- V2 Schemas ---


class WorkflowMeta(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    status: str = "draft"
    tags: List[str] = []
    owner: Optional[Dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorkflowUI(BaseModel):
    label: str
    position: Dict


class NodeRuntime(BaseModel):
    type: str  # internal, code, http
    language: Optional[str] = None


class NodeSpec(BaseModel):
    node_name: str
    runtime: NodeRuntime = NodeRuntime(type="internal")
    config: Dict = {}
    inputs: Optional[Dict] = None
    outputs: Optional[Dict] = None
    credentials_ref: Optional[str] = None
    error_policy: Optional[Dict] = None


class WorkflowNodeV2(BaseModel):
    id: str
    kind: str  # trigger, action, logic
    ui: WorkflowUI
    spec: NodeSpec


class WorkflowEdgeV2(BaseModel):
    id: str
    source: str
    target: str
    condition: Optional[str] = None
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class WorkflowGraph(BaseModel):
    nodes: List[WorkflowNodeV2]
    edges: List[WorkflowEdgeV2]


class ExecutionConfig(BaseModel):
    mode: str = "async"
    timeout_seconds: int = 300
    retry: Dict = {"max_attempts": 3, "strategy": "exponential"}
    concurrency: int = 1


class ObservabilityConfig(BaseModel):
    logging: bool = True
    metrics: bool = True
    tracing: bool = False


class AIMetadata(BaseModel):
    generated_by: Optional[str] = None
    confidence: Optional[float] = None
    prompt_version: Optional[str] = None


class WorkflowV2(BaseModel):
    meta: WorkflowMeta
    graph: WorkflowGraph
    execution: ExecutionConfig
    observability: ObservabilityConfig
    ai: AIMetadata


# --- End V2 Schemas ---


# Properties to return via API
class WorkflowPublic(SQLModel):
    # This now reflects the V2 structure
    meta: WorkflowMeta
    graph: WorkflowGraph
    execution: ExecutionConfig
    observability: ObservabilityConfig
    ai: AIMetadata

    # Required for backend tracking in SQLModel
    id: uuid.UUID
    owner_id: uuid.UUID


class WorkflowsPublic(SQLModel):
    data: list[WorkflowPublic]
    count: int


# Workflow save request with nodes and edges
class WorkflowSaveRequest(BaseModel):
    # The new request will just be the V2 JSON
    meta: WorkflowMeta
    graph: WorkflowGraph
    execution: ExecutionConfig
    observability: ObservabilityConfig
    ai: AIMetadata


# AI Workflow Generation
class AIWorkflowRequest(BaseModel):
    prompt: str
    workflow_id: Optional[uuid.UUID] = None
    current_nodes: Optional[List[Dict]] = None
    current_edges: Optional[List[Dict]] = None
    model: str = "openrouter"
    credential_id: Optional[uuid.UUID] = None


class AIWorkflowResponse(BaseModel):
    message: str
    # This now returns the full V2 structure
    workflow: WorkflowV2
    suggestions: Optional[List[str]] = None


# Generic message
class Message(SQLModel):
    message: str


class AIChatRequest(BaseModel):
    message: str
    model: str = "openrouter"
    credential_id: Optional[uuid.UUID] = None
    history: Optional[List[Dict[str, str]]] = None


class AIChatResponse(BaseModel):
    response: str


# Execution Schemas
class NodeExecutionPublic(BaseModel):
    id: uuid.UUID
    node_id: str
    node_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error: Optional[str] = None


class WorkflowExecutionPublic(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    trigger_data: Optional[str] = None
    node_executions: List[NodeExecutionPublic] = []


class ExecuteNodeRequest(BaseModel):
    input_data: Dict[str, Any] = {}
    config: Optional[Dict[str, Any]] = None


class TriggerWebhookResponse(BaseModel):
    execution_id: uuid.UUID
    status: str
    message: str


class ExecuteNodeResponse(BaseModel):
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    node_id: str

"""
Type definitions for the automation backend.

This module provides TypedDict definitions for better type safety in places
where Pydantic models aren't used directly, such as internal dictionaries
and API response structures.

These types help with:
- IDE autocompletion
- Static type checking with mypy/pyright
- Documentation of expected dictionary shapes
"""

from typing import Any, List, NotRequired, Optional, TypedDict, Union

from typing_extensions import Required

# ============================================================================
# Workflow Types
# ============================================================================


class PositionDict(TypedDict):
    """UI position for a workflow node."""

    x: float
    y: float


class WorkflowUIDict(TypedDict):
    """UI configuration for a workflow node."""

    label: str
    position: PositionDict
    icon: NotRequired[str]


class NodeRuntimeDict(TypedDict):
    """Runtime configuration for a node."""

    type: str  # "internal" | "code" | "http"
    language: NotRequired[str]  # For code runtime


class ErrorPolicyDict(TypedDict, total=False):
    """Error handling policy for a node."""

    strategy: str  # "retry" | "skip" | "fail"
    max_retries: int
    fallback_value: Any


class NodeSpecDict(TypedDict):
    """Specification for a workflow node."""

    node_name: str
    runtime: NodeRuntimeDict
    config: dict
    inputs: NotRequired[dict]
    outputs: NotRequired[dict]
    credentials_ref: NotRequired[str]
    error_policy: NotRequired[ErrorPolicyDict]


class WorkflowNodeDict(TypedDict):
    """A node in a workflow graph (V2 format)."""

    id: str
    kind: str  # "trigger" | "action" | "logic"
    ui: WorkflowUIDict
    spec: NodeSpecDict


class WorkflowEdgeDict(TypedDict):
    """An edge connecting two nodes."""

    id: str
    source: str
    target: str
    condition: NotRequired[str]


class WorkflowGraphDict(TypedDict):
    """The graph structure of a workflow."""

    nodes: List[WorkflowNodeDict]
    edges: List[WorkflowEdgeDict]


class RetryConfigDict(TypedDict):
    """Retry configuration for workflow execution."""

    max_attempts: int
    strategy: str  # "fixed" | "exponential" | "linear"
    base_delay: NotRequired[float]


class ExecutionConfigDict(TypedDict):
    """Execution configuration for a workflow."""

    mode: str  # "sync" | "async"
    timeout_seconds: int
    retry: RetryConfigDict
    concurrency: int


class ObservabilityConfigDict(TypedDict):
    """Observability settings for a workflow."""

    logging: bool
    metrics: bool
    tracing: bool


class AIMetadataDict(TypedDict, total=False):
    """AI generation metadata."""

    generated_by: str
    confidence: float
    prompt_version: str


class OwnerDict(TypedDict, total=False):
    """Owner information for a workflow."""

    user_id: str
    team_id: str


class WorkflowMetaDict(TypedDict):
    """Metadata for a workflow."""

    id: str
    name: str
    description: NotRequired[str]
    version: str
    status: str  # "draft" | "active" | "inactive"
    tags: List[str]
    owner: NotRequired[OwnerDict]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]


class WorkflowV2Dict(TypedDict):
    """Complete V2 workflow structure."""

    meta: WorkflowMetaDict
    graph: WorkflowGraphDict
    execution: ExecutionConfigDict
    observability: ObservabilityConfigDict
    ai: AIMetadataDict


# ============================================================================
# Execution Types
# ============================================================================


class NodeExecutionResultDict(TypedDict):
    """Result of executing a single node."""

    node_id: str
    status: str  # "success" | "error" | "skipped"
    outputs: dict
    error: NotRequired[str]
    execution_time_ms: NotRequired[float]


class WorkflowExecutionResultDict(TypedDict):
    """Result of executing a complete workflow."""

    execution_id: str
    workflow_id: str
    status: str  # "running" | "completed" | "failed"
    started_at: str
    completed_at: NotRequired[str]
    node_results: List[NodeExecutionResultDict]
    trigger_data: NotRequired[dict]


# ============================================================================
# Credential Types
# ============================================================================


class CredentialMetadataDict(TypedDict, total=False):
    """Metadata for a stored credential."""

    provider: str
    created_at: str
    expires_at: str
    scopes: List[str]


class CredentialDict(TypedDict):
    """A stored credential (without sensitive data)."""

    id: str
    name: str
    type: str  # "oauth2" | "api_key" | "basic"
    provider: str
    metadata: NotRequired[CredentialMetadataDict]


class FullCredentialDict(CredentialDict):
    """A credential with full data including secrets."""

    access_token: NotRequired[str]
    refresh_token: NotRequired[str]
    api_key: NotRequired[str]
    username: NotRequired[str]
    password: NotRequired[str]


# ============================================================================
# Node Registry Types
# ============================================================================


class NodeInputSchemaDict(TypedDict):
    """Schema for a node input."""

    name: str
    type: str  # "string" | "number" | "boolean" | "json" | "template"
    required: bool
    default: NotRequired[Any]
    description: NotRequired[str]


class NodeOutputSchemaDict(TypedDict):
    """Schema for a node output."""

    name: str
    type: str
    description: NotRequired[str]


class NodeSchemaDict(TypedDict):
    """Schema defining a node type."""

    name: str
    type: str  # "trigger" | "action" | "logic"
    description: str
    inputs: List[NodeInputSchemaDict]
    outputs: List[NodeOutputSchemaDict]
    category: NotRequired[str]


# ============================================================================
# Health/Status Types
# ============================================================================


class ServiceCheckDict(TypedDict):
    """Result of a service health check."""

    status: str  # "healthy" | "unhealthy" | "degraded"
    latency_ms: NotRequired[float]
    error: NotRequired[str]


class HealthStatusDict(TypedDict):
    """Overall health status response."""

    status: str
    timestamp: str
    version: str
    checks: dict  # Map of service name to ServiceCheckDict


class CircuitBreakerStatsDict(TypedDict):
    """Statistics for a circuit breaker."""

    state: str  # "closed" | "open" | "half_open"
    failure_count: int
    success_count: int
    total_calls: int
    total_failures: int
    total_successes: int


# ============================================================================
# API Response Types
# ============================================================================


class PaginatedResponseDict(TypedDict):
    """Paginated API response."""

    items: List[Any]
    total: int
    page: int
    page_size: int
    has_more: bool


class ErrorResponseDict(TypedDict):
    """API error response."""

    detail: str
    code: NotRequired[str]
    request_id: NotRequired[str]


# ============================================================================
# Trigger Data Types
# ============================================================================


class WebhookTriggerDataDict(TypedDict, total=False):
    """Data from a webhook trigger."""

    method: str
    headers: dict
    query_params: dict
    body: Any
    path: str


class ScheduleTriggerDataDict(TypedDict, total=False):
    """Data from a schedule trigger."""

    scheduled_time: str
    actual_time: str
    schedule_expression: str


class ManualTriggerDataDict(TypedDict, total=False):
    """Data from a manual trigger."""

    triggered_by: str
    input_data: dict


TriggerDataDict = Union[
    WebhookTriggerDataDict,
    ScheduleTriggerDataDict,
    ManualTriggerDataDict,
    dict,  # Fallback for custom triggers
]


# ============================================================================
# Context Types (used during execution)
# ============================================================================


class ExecutionContextDict(TypedDict):
    """Context passed during workflow execution."""

    workflow_id: str
    execution_id: str
    node_outputs: dict  # Map of node_id to outputs
    trigger_data: TriggerDataDict
    credentials: NotRequired[dict]  # Map of credential_ref to credential data


class NodeExecutionContextDict(TypedDict):
    """Context for executing a single node."""

    node_id: str
    workflow_id: str
    execution_id: str
    inputs: dict
    config: dict
    credential: NotRequired[FullCredentialDict]

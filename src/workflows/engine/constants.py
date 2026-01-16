"""
Constants for Workflow Engine

Centralizes all magic strings and numbers used throughout the workflow engine.
"""

from enum import Enum


class ExecutionStatus(str, Enum):
    """Valid workflow/node execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    """Workflow lifecycle statuses."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class NodeKind(str, Enum):
    """Types of nodes in a workflow."""
    TRIGGER = "trigger"
    ACTION = "action"
    LOGIC = "logic"
    AI = "ai"


class ErrorPolicy(str, Enum):
    """How to handle node failures."""
    STOP = "stop"
    CONTINUE = "continue"
    RETRY = "retry"


class QueueName:
    """Celery queue names for different node types."""
    DEFAULT = "default"
    AI = "ai_queue"
    IO = "io_queue"
    TRIGGER = "trigger_queue"


# Queue routing based on node type
QUEUE_ROUTING = {
    "ai": QueueName.AI,
    "ai.llm": QueueName.AI,
    "ai.agent": QueueName.AI,
    "http.request": QueueName.IO,
    "webhook": QueueName.IO,
    "email": QueueName.IO,
    "slack.send": QueueName.IO,
    "discord.send": QueueName.IO,
    "whatsapp.send": QueueName.IO,
    "google_sheets.read": QueueName.IO,
    "google_sheets.write": QueueName.IO,
}


class ExecutionConfig:
    """Execution-related configuration constants."""
    # Maximum history states to keep for undo/redo
    MAX_HISTORY_SIZE = 50
    
    # How often to check for scheduled workflows (seconds)
    SCHEDULER_INTERVAL_SECONDS = 10
    
    # Default retry settings
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_BASE_DELAY = 1.0  # seconds
    DEFAULT_RETRY_MAX_DELAY = 30.0  # seconds
    
    # Timeout for node execution (seconds)
    DEFAULT_NODE_TIMEOUT = 300  # 5 minutes
    
    # Maximum parallel nodes in a workflow
    MAX_PARALLEL_NODES = 10


class APIVersion:
    """API versioning."""
    V1 = "v1"
    CURRENT = V1


def get_queue_for_node(node_type: str) -> str:
    """Get the appropriate Celery queue for a node type."""
    # Check for exact match first
    if node_type in QUEUE_ROUTING:
        return QUEUE_ROUTING[node_type]
    
    # Check for prefix match (e.g., "ai.llm" matches "ai")
    prefix = node_type.split(".")[0] if "." in node_type else node_type
    if prefix in QUEUE_ROUTING:
        return QUEUE_ROUTING[prefix]
    
    return QueueName.DEFAULT

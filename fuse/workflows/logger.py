import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from fuse.utils.redis_client import get_redis_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowExecutorLogger:
    """
    Handles logging of workflow execution events to Redis (for real-time frontend updates)
    and potentially other sinks (database, file, etc.) in the future.
    """
    def __init__(self, workflow_id: uuid.UUID, execution_id: uuid.UUID):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.redis = get_redis_client()
        self.channel = f"workflow:execution:{execution_id}"

    def _publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to Redis."""
        message = {
            "type": event_type,
            "timestamp": str(datetime.utcnow()),
            "data": data
        }
        try:
            self.redis.publish(self.channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish event to Redis: {e}")

    def log_workflow_start(self):
        self._publish("workflow_started", {
            "workflow_id": str(self.workflow_id),
            "execution_id": str(self.execution_id)
        })

    def log_workflow_complete(self):
        self._publish("workflow_completed", {
            "workflow_id": str(self.workflow_id),
            "execution_id": str(self.execution_id),
            "status": "completed"
        })

    def log_workflow_failed(self, error: str):
        self._publish("workflow_failed", {
            "workflow_id": str(self.workflow_id),
            "execution_id": str(self.execution_id),
            "error": error
        })

    def log_node_scheduled(self, node_id: str, node_execution_id: str):
        self._publish("node_scheduled", {
            "node_id": node_id,
            "node_execution_id": node_execution_id
        })

    def log_node_start(self, node_id: str, node_execution_id: str, input_data: Any = None):
        self._publish("node_started", {
            "node_id": node_id,
            "node_execution_id": node_execution_id,
            "input_data": input_data
        })

    def log_node_complete(self, node_id: str, result: Any):
        self._publish("node_completed", {
            "node_id": node_id,
            "result": result
        })

    def log_node_failed(self, node_id: str, error: str, error_context: dict = None):
        """
        Log a node failure with optional structured error context.
        
        Args:
            node_id: The failing node's ID
            error: Error message string
            error_context: Optional dict with 'category', 'suggestion', 'is_retryable'
        """
        data = {
            "node_id": node_id,
            "error": error
        }
        
        if error_context:
            data["error_category"] = error_context.get("category", "unknown")
            data["error_suggestion"] = error_context.get("suggestion")
            data["is_retryable"] = error_context.get("is_retryable", False)
        
        self._publish("node_failed", data)
    
    def log_node_retrying(self, node_id: str, attempt: int, max_attempts: int, delay: float):
        """Log when a node is being retried."""
        self._publish("node_retrying", {
            "node_id": node_id,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "delay_seconds": delay
        })
    
    def log_node_continued(self, node_id: str, error: str):
        """Log when a node failed but workflow continues due to error_policy='continue'."""
        self._publish("node_continued", {
            "node_id": node_id,
            "error": error,
            "message": "Node failed but workflow continues (error_policy='continue')"
        })


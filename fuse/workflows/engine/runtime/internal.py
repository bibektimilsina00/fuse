from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class InternalRuntime:
    """Handles internal engine-level execution tasks."""
    
    @staticmethod
    def prepare_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures the context has all required fields for node execution."""
        default_context = {
            "workflow_id": None,
            "execution_id": None,
            "node_id": None,
            "node_config": {}
        }
        return {**default_context, **context}

    @staticmethod
    def validate_input(input_data: Any) -> Any:
        """Sanitizes or validates input data before passing to a node."""
        if input_data is None:
            return {}
        return input_data

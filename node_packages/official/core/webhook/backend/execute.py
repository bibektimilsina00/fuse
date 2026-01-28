"""
Webhook Trigger Node

Triggers workflows when external HTTP requests are received.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute webhook trigger.
    
    Note: In production, the webhook endpoint handler injects the actual
    request data (body, headers, query params) into the inputs.
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        List[WorkflowItem] with webhook request data
    """
    config = context.resolve_config()
    # For triggers, the 'input_data' provided by the Engine (from TriggerDataDict) 
    # should be used as the starting item.
    inputs = context.input_data # This could be Dict or List[WorkflowItem]
    
    # Standardize input to Dict if it's already unwrapped by context or just raw dict from trigger
    if isinstance(inputs, list):
        # If it's a list of WorkflowItems (unlikely for a fresh trigger but possible if manual)
        if inputs and isinstance(inputs[0], WorkflowItem):
            # Use the first item's JSON
            data_source = inputs[0].json_data
        else:
            data_source = {}
    elif isinstance(inputs, dict):
        data_source = inputs
    else:
        data_source = {}
    
    # Extract webhook data
    body = data_source.get("body", {})
    headers = data_source.get("headers", {})
    query = data_source.get("query", {})
    method = data_source.get("method") or config.get("method", "POST")
    timestamp = data_source.get("timestamp")
    
    # Get workflow ID from context
    workflow_id = context.workflow_id
    path = config.get("path", "default")
    
    # Construct schema-compliant output
    return [WorkflowItem(
        json={
            "body": body,
            "headers": headers,
            "query": query,
            "method": method,
            "webhook_url": f"/api/v1/webhooks/{workflow_id}/{path}",
            "received_at": timestamp,
            "path": path,
            # Add raw helper for convenience
            "raw": data_source
        }
    )]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate webhook configuration.
    
    Returns:
        Dict with 'valid' and 'errors'
    """
    errors = []
    
    # Validate path
    path = config.get("path")
    if not path:
        errors.append("'path' is required")
    elif not isinstance(path, str):
        errors.append("'path' must be a string")
    elif "/" in path:
        errors.append("'path' should not contain slashes")
    elif len(path) < 3:
        errors.append("'path' must be at least 3 characters")
    
    # Validate method
    method = config.get("method", "POST")
    valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    if method not in valid_methods:
        errors.append(f"'method' must be one of: {', '.join(valid_methods)}")
    
    # Validate authentication
    auth = config.get("authentication", "none")
    valid_auth = ["none", "api_key", "bearer", "basic"]
    if auth not in valid_auth:
        errors.append(f"'authentication' must be one of: {', '.join(valid_auth)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

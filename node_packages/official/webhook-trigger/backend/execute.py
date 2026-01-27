"""
Webhook Trigger Node

Triggers workflows when external HTTP requests are received.
"""

from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute webhook trigger.
    
    Note: In production, the webhook endpoint handler injects the actual
    request data (body, headers, query params) into the inputs.
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        Dict with webhook request data
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # Extract webhook data from inputs (injected by webhook handler)
    body = inputs.get("body", {})
    headers = inputs.get("headers", {})
    query = inputs.get("query", {})
    method = inputs.get("method") or config.get("method", "POST")
    timestamp = inputs.get("timestamp")
    
    # Get workflow ID from context
    workflow_id = context.get("workflow_id", "unknown")
    path = config.get("path", "default")
    
    # Construct webhook URL
    webhook_url = f"/api/v1/webhooks/{workflow_id}/{path}"
    
    return {
        "body": body,
        "headers": headers,
        "query": query,
        "method": method,
        "webhook_url": webhook_url,
        "received_at": timestamp,
        "path": path
    }


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

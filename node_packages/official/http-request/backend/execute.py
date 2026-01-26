"""
HTTP Request Node Plugin

This is a plugin-based implementation of the HTTP Request node.
It can be loaded dynamically without modifying the core codebase.
"""
import httpx
from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute HTTP request with the provided configuration.
    
    Args:
        context: Execution context containing:
            - config: Node configuration (url, method, headers, body)
            - inputs: Runtime input data
            - credentials: Credentials (if required)
            
    Returns:
        Dict with outputs: status, data, headers
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # Get parameters from config (with template rendering applied by engine)
    url = config.get("url")
    method = config.get("method", "GET").upper()
    headers = config.get("headers", {})
    body = config.get("body", {})
    
    # Fallback to inputs if config is empty (legacy support)
    if not url and isinstance(inputs, dict):
        url = inputs.get("url")
    
    # Validate URL
    if not url:
        raise ValueError("URL is required for HTTP Request node")
    
    # Ensure protocol
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    # Execute request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body and method in ["POST", "PUT", "PATCH"] else None,
                timeout=30.0  # 30 second timeout
            )
            
            # Try to parse JSON response
            try:
                data = response.json()
            except Exception:
                data = response.text
            
            return {
                "status": response.status_code,
                "data": data,
                "headers": dict(response.headers)
            }
            
    except httpx.TimeoutException:
        raise RuntimeError(f"HTTP request timed out after 30 seconds")
    except httpx.RequestError as e:
        raise RuntimeError(f"HTTP request failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during HTTP request: {str(e)}")


# Validation function (optional, run before execution)
async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration before execution.
    
    Returns:
        Dict with 'valid' (bool) and optional 'errors' (list)
    """
    errors = []
    
    if not config.get("url"):
        errors.append("URL is required")
    
    method = config.get("method", "GET").upper()
    valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    if method not in valid_methods:
        errors.append(f"Invalid HTTP method: {method}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

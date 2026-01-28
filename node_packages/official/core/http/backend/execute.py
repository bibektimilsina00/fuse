"""
HTTP Request Node Plugin

This is a plugin-based implementation of the HTTP Request node.
It can be loaded dynamically without modifying the core codebase.
"""
import httpx
from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute HTTP request with the provided configuration.
    
    Args:
        context: NodeContext object containing config, inputs, etc.
            
    Returns:
        List[WorkflowItem] with outputs
    """
    # In V2, we iterate over input items to support "Execute for each item"
    # For now, default behavior: execute once using the first item or merged context
    
    # Resolving configuration (already resolved by engine, but good to be explicit)
    config = context.resolve_config()
    items = context.input_data or []  # List[WorkflowItem]
    
    # If no items, run once (start node or similar behavior)
    if not items:
        # Create a dummy item to allow one execution
        items = [WorkflowItem(json={}, binary={})]

    output_items = []
    
    # TODO: Future enhancement - Concurrency control? 
    # For now, sequential execution per item
    
    for item in items:
        # If we supported resolving PER ITEM, we'd do it here.
        # But for now, let's assume config is resolved globally or we rely on engine.
        # Actually, engine resolves global config.
        # If user wants "{{ $input.id }}", standard expression parser handles it from context.
        # But if we map over items, we might need ITEM-scoped resolution.
        # V2 Step 1: Just execute once using resolved config.
        # Re-visiting strategy: If input is a list, and we want to run for each...
        # The node needs to handle looping or the users uses a Loop node.
        # Let's keep it simple: Map 1:1 if possible, or 1:N.
        
        # Simple Implementation: Single Request based on Global Config
        # (ignoring item-specific mapping for this iteration unless config used specific item index)
        
        url = config.get("url")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        body = config.get("body", {})
        
        if not url:
             raise ValueError("URL is required")

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body and method in ["POST", "PUT", "PATCH"] else None,
                    timeout=30.0
                )
                
                try:
                    data = response.json()
                except Exception:
                    data = {"text": response.text}
                
                output_items.append(WorkflowItem(
                    json={
                        "status": response.status_code,
                        "data": data,
                        "headers": dict(response.headers)
                    },
                    pairedItem=item.json_data.get("id") # Traceability
                ))
                
        except httpx.TimeoutException:
            raise RuntimeError(f"HTTP request timed out after 30 seconds")
        except Exception as e:
            raise RuntimeError(f"HTTP request failed: {str(e)}")
            
    # For HTTP node usually valid to execute once per config, unless explicit loop.
    # But if we received 10 items, do we make 10 requests?
    # Standard n8n behavior: Yes, run for each item.
    # To strictly support that, we would need to re-resolve config against EACH item context.
    # We will defer sophisticated "Run for each item" to Phase 8.
    # For now: Run Once logic is safer for migration.
    
    # Just returning the LAST result or mapped list?
    # Let's return the list of executions.
    if len(output_items) == 0 and len(items) > 0:
        # Should not happen if loop ran
        pass
        
    return output_items


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

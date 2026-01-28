"""
Delay Node Plugin

Pauses execution for a specified duration.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem
import asyncio

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute delay.
    
    Args:
        context: Execution context with config
        
    Returns:
        List[WorkflowItem] indicating completion
    """
    config = context.resolve_config()
    
    try:
        seconds = float(config.get("seconds", 5))
    except (ValueError, TypeError):
        seconds = 5.0
        
    if seconds < 0:
        seconds = 0
        
    # Cap delay at reasonable limit (e.g. 1 hour) to prevent hanging workers forever
    # Longer delays should use the 'Pause' node or specialized scheduler logic
    if seconds > 3600:
        seconds = 3600
        
    await asyncio.sleep(seconds)
    
    # Pass through input data after delay
    # This is more useful than just {"finished": True}
    return context.input_data or [WorkflowItem(json={"finished": True})]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    seconds = config.get("seconds")
    if seconds is not None:
        if not isinstance(seconds, (int, float)):
             errors.append("'seconds' must be a number")
        elif seconds < 0:
             errors.append("'seconds' must be non-negative")
    return {"valid": len(errors) == 0, "errors": errors}

"""
Delay Node Plugin

Pauses execution for a specified duration.
"""

import asyncio
from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute delay.
    
    Args:
        context: Execution context with config
        
    Returns:
        Dict indicating completion
    """
    config = context.get("config", {})
    
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
    
    return {"finished": True}


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

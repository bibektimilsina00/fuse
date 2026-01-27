"""
Schedule Trigger Node

Triggers workflows at specified intervals or cron schedules.
"""

from datetime import datetime
from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute schedule trigger.
    
    Note: In production, this is handled by a scheduler service (Celery Beat, cron, etc.)
    This function returns metadata about when/how the workflow was triggered.
    
    Args:
        context: Execution context with config
        
    Returns:
        Dict with timestamp and schedule metadata
    """
    config = context.get("config", {})
    
    # Get configuration
    frequency = config.get("frequency", "minutes")
    interval = config.get("interval", 15)
    cron_expression = config.get("cron_expression", "")
    timezone = config.get("timezone", "UTC")
    
    # Generate default cron if not provided
    if not cron_expression:
        # Simple cron generation based on frequency/interval
        if frequency == "seconds":
            cron_expression = f"*/{interval} * * * * *"  # Every N seconds
        elif frequency == "minutes":
            cron_expression = f"*/{interval} * * * *"  # Every N minutes
        elif frequency == "hours":
            cron_expression = f"0 */{interval} * * *"  # Every N hours
        elif frequency == "days":
            cron_expression = f"0 0 */{interval} * *"  # Every N days
        else:
            cron_expression = "0 9 * * *"  # Default: 9 AM daily
    
    # In production, the scheduler would inject the actual trigger time
    # For now, return current time as the trigger time
    now = datetime.utcnow()
    
    return {
        "timestamp": now.isoformat(),
        "triggered_at": now.isoformat(),
        "cron_expression": cron_expression,
        "timezone": timezone,
        "frequency": frequency,
        "interval": interval
    }


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate schedule configuration.
    
    Returns:
        Dict with 'valid' and 'errors'
    """
    errors = []
    
    # Validate interval
    interval = config.get("interval")
    if interval is not None:
        if not isinstance(interval, (int, float)) or interval <= 0:
            errors.append("'interval' must be a positive number")
    
    # Validate frequency
    frequency = config.get("frequency", "minutes")
    valid_frequencies = ["seconds", "minutes", "hours", "days"]
    if frequency not in valid_frequencies:
        errors.append(f"'frequency' must be one of: {', '.join(valid_frequencies)}")
    
    # Validate cron expression (basic check)
    cron = config.get("cron_expression", "")
    if cron:
        parts = cron.split()
        if len(parts) not in [5, 6]:  # Standard cron (5) or with seconds (6)
            errors.append("'cron_expression' must have 5 or 6 parts")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

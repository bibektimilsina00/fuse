"""
Merge Plugin

TODO: Migrate logic from old node system
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute merge logic.
    
    Args:
        context: Execution context
        
    Returns:
        List[WorkflowItem] aggregated from inputs
    """
    # Merge node logic depends on how the engine provides inputs.
    # Typically, it should receive data from ALL incoming branches.
    # Currently, we just pass through what we received (assuming engine/scheduler handled the wait).
    
    # Ideally, we should check `context.results` to find all predecessor outputs and combine them.
    # For now, simplest V2 implementation: Pass through input.
    
    inputs = context.input_data
    if inputs is None:
        return []
    if isinstance(inputs, list):
        return inputs
    if isinstance(inputs, dict):
        # Wrap single dict
        return [WorkflowItem(json=inputs)]
        
    return []


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    return {"valid": True, "errors": []}

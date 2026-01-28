"""
Loop Plugin

TODO: Migrate logic from old node system
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute loop logic.
    
    Args:
        context: Execution context
        
    Returns:
        List[WorkflowItem] (the items to iterate)
    """
    # Loop node takes input list and just returns it.
    # The Scheduler handles the Fan-Out or iteration.
    
    inputs = context.input_data
    
    if inputs is None:
        return []
    if isinstance(inputs, list):
        return inputs
    if isinstance(inputs, dict):
        return [WorkflowItem(json=inputs)]
        
    return []


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    return {"valid": True, "errors": []}

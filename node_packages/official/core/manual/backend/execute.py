"""
Manual Trigger Plugin

TODO: Migrate logic from old node system
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute the node.
    
    Args:
        context: Execution context with config, inputs, credentials
        
    Returns:
        List[WorkflowItem]
    """
    # Manual trigger typically receives input from the frontend/API call
    inputs = context.input_data 
    
    if isinstance(inputs, list) and inputs and isinstance(inputs[0], WorkflowItem):
        data = inputs[0].json_data
    elif isinstance(inputs, dict):
        data = inputs
    else:
        # Default empty if no data passed
        data = {}

    return [WorkflowItem(json=data)]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    return {"valid": True, "errors": []}

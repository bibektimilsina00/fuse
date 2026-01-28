"""
Form Trigger Plugin

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
    inputs = context.input_data # For trigger this is the form submission data
    
    # Standardize input to Dict if it's already unwrapped by context or just raw dict
    if isinstance(inputs, list) and inputs and isinstance(inputs[0], WorkflowItem):
        data = inputs[0].json_data
    elif isinstance(inputs, dict):
        data = inputs
    else:
        # If no input, maybe just empty form?
        data = {}

    # Just return whatever we got as a clean V2 item
    return [WorkflowItem(json=data)]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    return {"valid": True, "errors": []}

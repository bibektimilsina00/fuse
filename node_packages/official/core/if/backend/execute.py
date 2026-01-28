"""
If Condition Node

Conditional branching logic using Jinja2 template expressions.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Evaluate a condition and return True/False.
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        List[WorkflowItem] containing result
    """
    # Resolve config (handles Jinja2 expressions automatically)
    config = context.resolve_config()
    inputs = context.input_data
    
    # Retrieve resolved condition directly
    # 'condition' input in manifest, e.g. "{{ input.value > 10 }}"
    # If the user put a boolean directly, it's a bool.
    # If it was a string "true", resolve_config might strictly valid types?
    # Actually, Jinja renders to string usually, but ExpressionResolver tries to infer types.
    
    condition_val = config.get("condition")
    
    # Determine truthiness
    result = False
    if isinstance(condition_val, bool):
        result = condition_val
    elif isinstance(condition_val, str):
        result = condition_val.lower() in ["true", "1", "yes", "on"]
    elif isinstance(condition_val, (int, float)):
        result = bool(condition_val)
    
    branch = "true" if result else "false"
    
    # Return result wrapped in WorkflowItem
    # We include the original inputs + result metadata
    
    # Pass through data?
    # Usually If node passes the input data to the chosen branch.
    # We should preserve the input item.
    
    input_item = inputs[0] if isinstance(inputs, list) and inputs else WorkflowItem(json={})
    
    return [WorkflowItem(
        json={
            **input_item.json_data, # Pass through original data
            "result": result,       # Logic metadata
            "branch_taken": branch
        },
        binary=input_item.binary_data,
        pairedItem=input_item.paired_item
    )]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate condition configuration.
    
    Returns:
        Dict with 'valid' and 'errors'
    """
    errors = []
    
    # Validate condition exists
    condition = config.get("condition")
    if not condition:
        errors.append("'condition' is required")
    elif not isinstance(condition, str):
        errors.append("'condition' must be a string")
    elif len(condition.strip()) == 0:
        errors.append("'condition' cannot be empty")
    
    # Try to parse as Jinja template
    if condition:
        try:
            Template(condition)
        except Exception as e:
            errors.append(f"Invalid Jinja2 template: {str(e)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

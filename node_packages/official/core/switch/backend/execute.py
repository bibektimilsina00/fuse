"""
Switch Node Plugin

Multi-way branching based on value matching.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute switch logic.
    
    Args:
        context: Execution context with config
        
    Returns:
        List[WorkflowItem] with matched case key
    """
    config = context.resolve_config()
    inputs = context.input_data
    
    value = str(config.get("value", ""))
    cases = config.get("cases", {})
    
    matched_case = "default"
    
    if isinstance(cases, dict):
        for case_key, case_val in cases.items():
            # If cases matches value
            if str(case_val) == value:
                matched_case = case_key
                break
    
    # Return input data + match decision
    input_item = inputs[0] if isinstance(inputs, list) and inputs else WorkflowItem(json={})

    return [WorkflowItem(
        json={
            **input_item.json_data,
            "matched": matched_case
        },
        binary=input_item.binary_data,
        pairedItem=input_item.paired_item
    )]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("cases"):
        errors.append("Cases are required")
    elif not isinstance(config.get("cases"), dict):
        errors.append("Cases must be a valid JSON object")
    return {"valid": len(errors) == 0, "errors": errors}

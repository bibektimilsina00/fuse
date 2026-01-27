"""
Switch Node Plugin

Multi-way branching based on value matching.
"""

from jinja2 import Template
from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute switch logic.
    
    Args:
        context: Execution context with config
        
    Returns:
        Dict with matched case key
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    value_template = config.get("value", "")
    cases = config.get("cases", {})
    
    # Render value if it's a template
    template_context = {
        "input": inputs,
        "inputs": inputs,
        "workflow_id": context.get("workflow_id"),
        **context.get("results", {}),
        **(inputs if isinstance(inputs, dict) else {})
    }
    
    try:
        value = Template(str(value_template)).render(template_context)
    except Exception:
        value = str(value_template)
    
    matched_case = "default"
    
    if isinstance(cases, dict):
        for case_key, case_val in cases.items():
            # If cases matches value
            if str(case_val) == value:
                matched_case = case_key
                break
                
    return {"matched": matched_case}


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("cases"):
        errors.append("Cases are required")
    elif not isinstance(config.get("cases"), dict):
        errors.append("Cases must be a valid JSON object")
    return {"valid": len(errors) == 0, "errors": errors}

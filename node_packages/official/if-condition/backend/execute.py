"""
If Condition Node

Conditional branching logic using Jinja2 template expressions.
"""

from jinja2 import Template
from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a condition and return True/False.
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        Dict with result (boolean) and branch_taken (string)
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # Get the condition expression
    condition_raw = config.get("condition", "").strip()
    
    if not condition_raw:
        return {"result": False, "branch_taken": "false"}
    
    # Prepare template context
    # Include inputs, workflow context, and any previous node results
    template_context = {
        "input": inputs,
        "inputs": inputs,
        "workflow_id": context.get("workflow_id"),
        "execution_id": context.get("execution_id"),
        "node": context.get("node", {}),
        **context.get("results", {}),  # Results from previous nodes
        **(inputs if isinstance(inputs, dict) else {})
    }
    
    # Process the condition string
    # If it's not wrapped in {{ }}, wrap it for Jinja evaluation
    expr = condition_raw
    if not (expr.startswith("{{") and expr.endswith("}}")):
        expr = f"{{{{ {expr} }}}}"
    
    try:
        # Render the expression using Jinja2
        rendered = Template(expr).render(template_context).strip().lower()
        
        # Convert to boolean
        # Truthy values: "true", "1", "yes", "on"
        result = rendered in ["true", "1", "yes", "on"]
        
    except Exception as e:
        #  If rendering fails, return False
        result = False
    
    return {
        "result": result,
        "branch_taken": "true" if result else "false"
    }


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

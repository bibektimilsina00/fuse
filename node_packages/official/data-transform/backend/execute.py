"""
Data Transform Node

Map, filter, and transform data using Jinja2 templates.
"""

from jinja2 import Template
from typing import Any, Dict
import json


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform data using field mappings.
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        Dict with transformed output
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # Get mapping configuration
    mapping = config.get("mapping", {})
    
    if not mapping:
        # If no mapping, pass through input data
        return {"output": inputs}
    
    # Prepare template context
    template_context = {
        "input": inputs,
        "inputs": inputs,
        "workflow_id": context.get("workflow_id"),
        "execution_id": context.get("execution_id"),
        "node": context.get("node", {}),
        **context.get("results", {}),  # Results from previous nodes
        **(inputs if isinstance(inputs, dict) else {})
    }
    
    # Transform data according to mapping
    transformed = {}
    
    for target_key, template_str in mapping.items():
        # If the value is not a string, use it as-is
        if not isinstance(template_str, str):
            transformed[target_key] = template_str
            continue
        
        try:
            # Check if it's a simple key reference (no templates)
            if template_str in template_context and "{{" not in template_str:
                # Direct key access
                transformed[target_key] = template_context[template_str]
            else:
                # Treat as Jinja2 template
                rendered = Template(template_str).render(template_context)
                
                # Try to parse as JSON if it looks like JSON
                if rendered.startswith(("{", "[")):
                    try:
                        transformed[target_key] = json.loads(rendered)
                    except:
                        transformed[target_key] = rendered
                else:
                    transformed[target_key] = rendered
                    
        except Exception as e:
            # If template fails, use raw value
            transformed[target_key] = template_str
    
    return {"output": transformed}


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate transform configuration.
    
    Returns:
        Dict with 'valid' and 'errors'
    """
    errors = []
    
    # Validate mapping
    mapping = config.get("mapping")
    if mapping is not None:
        if not isinstance(mapping, dict):
            errors.append("'mapping' must be a JSON object/dict")
        else:
            # Validate each mapping value is valid Jinja2
            for key, value in mapping.items():
                if isinstance(value, str) and "{{" in value:
                    try:
                        Template(value)
                    except Exception as e:
                        errors.append(f"Invalid template for '{key}': {str(e)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

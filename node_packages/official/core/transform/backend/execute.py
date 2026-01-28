"""
Data Transform Node

Map, filter, and transform data using Jinja2 templates.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Transform data using field mappings.
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        List[WorkflowItem] with transformed output
    """
    # resolve_config() automatically handles resolving the VALUES of the 'mapping' dict.
    # So if mapping is {"a": "{{ input.b }}"}, config["mapping"]["a"] will be value of b.
    config = context.resolve_config()
    
    mapping = config.get("mapping", {})
    
    if not mapping:
        # Pass through if no mapping
        return context.input_data or []

    # The mapping result IS the new item data
    # We maintain lineage from the first input item (if any)
    
    first_input = context.input_data[0] if context.input_data else None
    
    return [WorkflowItem(
        json=mapping,
        binary=first_input.binary_data if first_input else {},
        pairedItem=first_input.paired_item if first_input else None
    )]


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

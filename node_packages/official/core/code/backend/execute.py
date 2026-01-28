"""
Python Code Executor Node

Execute custom Python code with access to workflow data.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute custom Python code.
    
    SECURITY NOTE: This executes arbitrary Python code.
    In production, use sandboxing (Docker, RestrictedPython, etc.)
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        List[WorkflowItem] with code execution result
    """
    config = context.resolve_config()
    items = context.input_data # List[WorkflowItem]
    
    # Get the code to execute
    code = config.get("code", "").strip()
    
    if not code:
        code = "return items"
    
    # Prepare execution environment
    # Expose 'items' (List[WorkflowItem]) and 'WorkflowItem' class
    # Also expose 'item' (first item) for convenience
    first_item = items[0] if items else None
    
    exec_globals = {
        "items": items,
        "item": first_item,
        "WorkflowItem": WorkflowItem,
        "input_data": items, # Alias for backward compat? Or maybe just raw json?
        # Let's give raw json list for ease of use
        "json_input": [i.json_data for i in items] if items else [],
        "context": context
    }
    exec_locals = {}
    
    # Check if code contains await (async)
    is_async = "await " in code
    
    # Wrap code in an async function
    # V2: We expect users to return a List[WorkflowItem] or List[Dict] or Dict.
    wrapped_code = "async def main():\n"
    for line in code.split("\n"):
        line = line.replace("\t", "    ")
        wrapped_code += f"    {line}\n"
    
    try:
        # Execute the function definition
        exec(wrapped_code, exec_globals, exec_locals)
        
        # Run the main function
        main_func = exec_locals["main"]
        result = await main_func()
        
        # Helper to strict V2 Format
        output_items = []
        
        if result is None:
            pass # Return empty list
            
        elif isinstance(result, list):
            for res in result:
                if isinstance(res, WorkflowItem):
                    output_items.append(res)
                elif isinstance(res, dict):
                    output_items.append(WorkflowItem(json=res))
                else:
                     output_items.append(WorkflowItem(json={"data": res}))
                     
        elif isinstance(result, WorkflowItem):
            output_items.append(result)
            
        elif isinstance(result, dict):
            output_items.append(WorkflowItem(json=result))
            
        else:
             output_items.append(WorkflowItem(json={"output": result}))
        
        return output_items
        
    except SyntaxError as e:
        raise RuntimeError(
            f"Syntax error in code: {e.msg} at line {e.lineno}\n"
            f"Code:\n{wrapped_code}"
        )
    except Exception as e:
        raise RuntimeError(f"Error executing Python code: {str(e)}")


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate code configuration.
    
    Returns:
        Dict with 'valid' and 'errors'
    """
    errors = []
    
    # Validate code exists
    code = config.get("code")
    if not code:
        errors.append("'code' is required")
    elif not isinstance(code, str):
        errors.append("'code' must be a string")
    elif len(code.strip()) == 0:
        errors.append("'code' cannot be empty")
    
    # Try to compile the code (basic syntax check)
    if code:
        try:
            # Wrap in async function for syntax check
            wrapped = f"async def main():\n"
            for line in code.split("\n"):
                wrapped += f"    {line}\n"
            compile(wrapped, "<string>", "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg} at line {e.lineno}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

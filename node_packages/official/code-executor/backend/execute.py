"""
Python Code Executor Node

Execute custom Python code with access to workflow data.
"""

from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute custom Python code.
    
    SECURITY NOTE: This executes arbitrary Python code.
    In production, use sandboxing (Docker, RestrictedPython, etc.)
    
    Args:
        context: Execution context with config and inputs
        
    Returns:
        Dict with code execution result
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # Get the code to execute
    code = config.get("code", "").strip()
    
    if not code:
        code = "return input_data"
    
    # Prepare execution environment
    exec_globals = {
        "input_data": inputs,
        "input": inputs,
        "context": context,
        "inputs": inputs
    }
    exec_locals = {}
    
    # Check if code contains await (async)
    is_async = "await " in code
    
    # Wrap code in an async function
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
        
        # If result is None, return empty dict
        if result is None:
            return {}
        
        # If result is not a dict, wrap it
        if not isinstance(result, dict):
            return {"output": result}
        
        return result
        
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

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class CodeRuntime:
    """Handles execution of dynamic code snippets."""
    
    @staticmethod
    async def execute_python(code: str, context: Dict[str, Any], input_data: Any) -> Any:
        """Executes Python code in a sandboxed-ish environment."""
        if not code or not code.strip():
            code = "return input_data"
        
        exec_globals = {
            "input_data": input_data,
            "context": context,
        }
        exec_locals = {}
        
        # Wrap code to handle return values and async execution
        wrapped_code = f"async def main():\n"
        for line in code.split("\n"):
            line = line.replace("\t", "    ")
            wrapped_code += f"    {line}\n"
        
        try:
            exec(wrapped_code, exec_globals, exec_locals)
            main_func = exec_locals["main"]
            result = await main_func()
            return result
        except SyntaxError as e:
            raise RuntimeError(f"Syntax error in code: {e.msg} at line {e.lineno}")
        except Exception as e:
            raise RuntimeError(f"Error executing code runtime: {str(e)}")

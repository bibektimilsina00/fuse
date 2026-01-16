from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class CodeNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="code.python",
            label="Python Script",
            type="action",
            description="Executes custom Python logic.",
            inputs=[
                NodeInput(
                    name="code",
                    type="code",
                    label="Python Code",
                    default="""# Python Script
# Available variables:
# - input_data: Data from the previous node
# - context: Workflow execution context

# Example: Transform and return data
result = {
    "message": "Hello from Python!",
    "input": input_data,
    "processed": True
}

return result"""
                )
            ],
            outputs=[
                NodeOutput(name="output", type="json", label="Result")
            ],
            category="Utilities",
            runtime="code"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        config = context.get("node_config", {})
        code = config.get("code")
        if not code or not code.strip():
            code = "return input_data"
        
        # Define local scope for execution
        # Prepare the execution environment
        # Prepare the execution environment
        exec_globals = {
            "input_data": input_data,
            "input": input_data,
            "context": context,
        }
        exec_locals = {}
        
        # Check if the code contains 'await'
        is_async = "await " in code
        
        # Wrap code to handle return values and async execution
        # We define a function 'main' that contains the user code
        wrapped_code = f"async def main():\n"
        for line in code.split("\n"):
            line = line.replace("\t", "    ")
            wrapped_code += f"    {line}\n"
        
        try:
            # Debug: Log the generated code
            # print(f"Executing wrapped code:\n{wrapped_code}")
            
            # Execute the definition of 'main'
            exec(wrapped_code, exec_globals, exec_locals)
            
            # Now run 'main'
            # If the user code has a return statement, 'main' will return that value
            main_func = exec_locals["main"]
            result = await main_func()
            return result
        except SyntaxError as e:
            # print(f"Executing wrapped code:\n{wrapped_code}") # Uncomment for deeper debug if needed locally
            raise RuntimeError(f"Syntax error in code: {e.msg} at line {e.lineno}. The code being executed was:\n{wrapped_code}")
        except Exception as e:
            # Re-raise with the wrapped code for context if needed, or just the error
            raise RuntimeError(f"Error executing code node: {str(e)}")

@NodeRegistry.register
class JSCodeNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="code.javascript",
            label="JS Script",
            type="action",
            description="Executes custom JavaScript logic.",
            inputs=[
                NodeInput(
                    name="code",
                    type="code",
                    label="JS Code",
                    default="""// JavaScript Script
// Available variables:
// - inputData: Data from the previous node
// - context: Workflow execution context

// Example: Transform and return data
const result = {
    message: "Hello from JavaScript!",
    input: inputData,
    processed: true
};

console.log("Processing data:", inputData);

return result;"""
                )
            ],
            outputs=[
                NodeOutput(name="output", type="json", label="Result")
            ],
            category="Utilities",
            runtime="code"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        import subprocess
        import json
        import os
        import tempfile

        config = context.get("node_config", {})
        code = config.get("code")
        if not code or not code.strip():
            code = "return inputData;"

        # Prepare the JS environment
        # We wrap the user code in a function and call it with global variables
        js_payload = {
            "inputData": input_data,
            "context": {
                "workflow_id": str(context.get("workflow_id")),
                "execution_id": str(context.get("execution_id")),
                "node_id": context.get("node_id")
            }
        }

        # Create a robust runner script
        # We use JSON.stringify to safely pass data in/out
        runner_script = f"""
const inputData = {json.dumps(js_payload['inputData'])};
const input = inputData;
const context = {json.dumps(js_payload['context'])};

async function main() {{
    {code}
}}

main().then(result => {{
    process.stdout.write(JSON.stringify(result));
}}).catch(err => {{
    process.stderr.write(err.stack || err.message);
    process.exit(1);
}});
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(runner_script)
            temp_path = f.name

        try:
            process = subprocess.run(
                ["node", temp_path],
                capture_output=True,
                text=True,
                timeout=30 
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"JS Execution Error: {process.stderr}")
            
            try:
                # If the code returned nothing, stdout might be empty
                if not process.stdout.strip():
                    return {"success": True}
                return json.loads(process.stdout)
            except json.JSONDecodeError:
                return {"text": process.stdout}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

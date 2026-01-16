"""
Code execution endpoint for testing Python and JavaScript code in the workflow builder.
This provides a sandboxed environment for users to test their code before deploying.
"""

import json
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from src.logger import logger
from src.utils.code_sanitizer import MAX_CODE_LENGTH, sanitize_code

router = APIRouter()


class CodeExecutionRequest(BaseModel):
    code: str
    language: str  # 'python' or 'javascript'
    node_id: Optional[str] = None
    workflow_id: Optional[str] = None
    test_input: Optional[Dict[str, Any]] = None

    @field_validator("code")
    @classmethod
    def validate_code_length(cls, v: str) -> str:
        if len(v) > MAX_CODE_LENGTH:
            raise ValueError(
                f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters"
            )
        if not v.strip():
            raise ValueError("Code cannot be empty")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed = {"python", "javascript", "js"}
        if v.lower() not in allowed:
            raise ValueError(f"Language must be one of: {', '.join(allowed)}")
        return v.lower()


class CodeExecutionResponse(BaseModel):
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None


@router.post("/execute-code", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest) -> CodeExecutionResponse:
    """
    Execute Python or JavaScript code in a sandboxed environment.

    WARNING: This is a simplified implementation for development.
    For production, use:
    - Docker containers for isolation
    - Resource limits (CPU, memory, time)
    - Network restrictions
    - Proper sandboxing (e.g., PyPy sandbox, VM2 for Node.js)
    """

    # Sanitize the code before execution
    sanitization_result = sanitize_code(request.code, request.language)
    if not sanitization_result.is_safe:
        logger.warning(
            f"Code execution blocked due to security violations: {sanitization_result.violations}",
            extra={"node_id": request.node_id, "workflow_id": request.workflow_id},
        )
        raise HTTPException(status_code=400, detail=sanitization_result.error_message)

    logger.info(
        f"Executing {request.language} code",
        extra={"node_id": request.node_id, "workflow_id": request.workflow_id},
    )

    if request.language == "python":
        return await execute_python(request)
    elif request.language in ("javascript", "js"):
        return await execute_javascript(request)
    else:
        raise HTTPException(status_code=400, detail="Unsupported language")


async def execute_python(request: CodeExecutionRequest) -> CodeExecutionResponse:
    """Execute Python code safely."""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Prepare the execution environment
            test_input = request.test_input or {"message": "test"}

            # Wrap the user code with input/output handling
            wrapped_code = f"""
import json
import sys

# Simulated input data
input_data = {json.dumps(test_input)}
context = {{"workflow_id": "{request.workflow_id}", "node_id": "{request.node_id}"}}

# User code
{request.code}
"""
            f.write(wrapped_code)
            temp_file = f.name

        try:
            # Execute with timeout
            result = subprocess.run(
                ["python3", temp_file],
                capture_output=True,
                text=True,
                timeout=5,  # 5 second timeout
            )

            if result.returncode != 0:
                return CodeExecutionResponse(
                    output="", error=result.stderr or "Execution failed"
                )

            return CodeExecutionResponse(
                output=result.stdout or "Code executed successfully (no output)",
                error=None,
            )

        finally:
            # Clean up temp file
            os.unlink(temp_file)

    except subprocess.TimeoutExpired:
        return CodeExecutionResponse(
            output="", error="Execution timed out (max 5 seconds)"
        )
    except Exception as e:
        return CodeExecutionResponse(output="", error=f"Execution error: {str(e)}")


async def execute_javascript(request: CodeExecutionRequest) -> CodeExecutionResponse:
    """Execute JavaScript code safely."""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            # Prepare the execution environment
            test_input = request.test_input or {"message": "test"}

            # Wrap the user code with input/output handling
            wrapped_code = f"""
// Simulated input data
const inputData = {json.dumps(test_input)};
const context = {{workflowId: "{request.workflow_id}", nodeId: "{request.node_id}"}};

// User code
{request.code}
"""
            f.write(wrapped_code)
            temp_file = f.name

        try:
            # Execute with timeout
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=5,  # 5 second timeout
            )

            if result.returncode != 0:
                return CodeExecutionResponse(
                    output="", error=result.stderr or "Execution failed"
                )

            return CodeExecutionResponse(
                output=result.stdout or "Code executed successfully (no output)",
                error=None,
            )

        finally:
            # Clean up temp file
            os.unlink(temp_file)

    except subprocess.TimeoutExpired:
        return CodeExecutionResponse(
            output="", error="Execution timed out (max 5 seconds)"
        )
    except FileNotFoundError:
        return CodeExecutionResponse(
            output="",
            error="Node.js not found. Please install Node.js to execute JavaScript code.",
        )
    except Exception as e:
        return CodeExecutionResponse(output="", error=f"Execution error: {str(e)}")

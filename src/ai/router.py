from typing import Any
from fastapi import APIRouter, HTTPException

from src.auth.dependencies import CurrentUser
from src.workflows.schemas import AIWorkflowRequest, AIWorkflowResponse
from src.ai.service import ai_service

router = APIRouter()

@router.post("/generate", response_model=AIWorkflowResponse)
async def generate_workflow_with_ai(
    request: AIWorkflowRequest,
    current_user: CurrentUser,
) -> Any:
    """
    Generate workflow with AI.
    """
    try:
        result = await ai_service.generate_workflow_from_prompt(
            prompt=request.prompt,
            model=request.model,
            current_nodes=request.current_nodes,
            current_edges=request.current_edges
        )
        
        # Log successful generation (using global logger)
        logger.info(f"Workflow generated with AI: {result}") # type: ignore
        
        return result
    except Exception as e:
        logger.error(f"AI generation failed: {e}") # type: ignore
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {str(e)}"
        )

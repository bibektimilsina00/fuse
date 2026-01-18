from typing import Any, Optional
from fastapi import APIRouter, HTTPException
import logging

from fuse.auth.dependencies import CurrentUser
from fuse.workflows.schemas import AIWorkflowRequest, AIWorkflowResponse
from fuse.ai.service import ai_service
from fuse.credentials.service import get_full_credential_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=AIWorkflowResponse)
async def generate_workflow_with_ai(
    request: AIWorkflowRequest,
    current_user: CurrentUser,
) -> Any:
    """
    Generate workflow with AI using either global keys or user-provided credentials.
    """
    try:
        credential_data = None
        if request.credential_id:
            credential_data = get_full_credential_by_id(str(request.credential_id))
            if not credential_data:
                raise HTTPException(status_code=404, detail="Credential not found")

        result = await ai_service.generate_workflow_from_prompt(
            prompt=request.prompt,
            model=request.model,
            current_nodes=request.current_nodes,
            current_edges=request.current_edges,
            credential_data=credential_data,
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

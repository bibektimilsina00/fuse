from typing import Any, Optional
from fastapi import APIRouter, HTTPException
import logging

from fuse.auth.dependencies import CurrentUser
from fuse.workflows.schemas import AIWorkflowRequest, AIWorkflowResponse, AIChatRequest, AIChatResponse
from fuse.ai.service import ai_service
from fuse.ai import cliproxy_manager
from fuse.credentials.service import get_full_credential_by_id, get_active_credential

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
            credential_data = await get_active_credential(str(request.credential_id))
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


@router.post("/chat", response_model=AIChatResponse)
async def chat_with_ai(
    request: AIChatRequest,
    current_user: CurrentUser,
) -> Any:
    """Chat with AI assistant."""
    try:
        credential_data = {}
        if request.credential_id:
            credential_data = await get_active_credential(str(request.credential_id)) or {}

        # Construct messages (History + Current)
        messages = request.history or []
        # If history does not have system prompt, add one?
        if not any(m.get("role") == "system" for m in messages):
             messages.insert(0, {"role": "system", "content": "You are a helpful workflow automation assistant."})
        
        messages.append({"role": "user", "content": request.message})

        result = await ai_service.call_llm(
            messages=messages,
            model=request.model,
            credential=credential_data
        )
        
        return AIChatResponse(response=result["content"])
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")


@router.get("/models")
async def get_ai_models(
    credential_id: Optional[str] = None,
    current_user: CurrentUser = None,
) -> Any:
    """Get available models based on credential."""
    try:
        credential_data = {}
        if credential_id:
            credential_data = await get_active_credential(credential_id) or {}
            
        return await ai_service.get_available_models(credential_data)
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


# TEMPORARY DEBUG ENDPOINT - Remove in production!
@router.get("/debug/credentials/{credential_id}")
async def debug_get_credentials(
    credential_id: str,
    current_user: CurrentUser,
) -> Any:
    """DEBUG: Get raw decrypted credentials for Postman testing."""
    credential_data = await get_active_credential(credential_id)
    if not credential_data:
        raise HTTPException(status_code=404, detail="Credential not found")
    return credential_data


@router.get("/antigravity/status")
async def get_antigravity_status(
    current_user: CurrentUser,
) -> Any:
    """Get status of CLIProxyAPI and Google AI login."""
    return cliproxy_manager.get_cliproxy_status()


@router.post("/antigravity/login")
async def start_antigravity_login(
    current_user: CurrentUser,
) -> Any:
    """Start the Google AI OAuth login flow."""
    try:
        success = cliproxy_manager.run_antigravity_login()
        if not success:
            raise HTTPException(status_code=500, detail="Login process failed")
        return {"success": True, "message": "Login successful"}
    except Exception as e:
        logger.error(f"Antigravity login failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


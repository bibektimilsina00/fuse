"""
AI LLM Node Plugin

Simple text generation using LLMs.
"""

from typing import Any, Dict, List
import uuid

from sqlmodel import Session
from fuse.database import engine
from fuse.credentials.models import Credential
from fuse.ai.service import ai_service
from fuse.credentials.service import get_full_credential_by_id


async def get_models(context: Dict[str, Any], dependency_values: Dict[str, Any]) -> List[Dict[str, str]]:
    """Fetch available models."""
    credential_id = dependency_values.get("credential")
    if not credential_id:
         return []
    
    try:
        with Session(engine) as session:
            try:
                cred_uuid = uuid.UUID(credential_id)
            except ValueError:
                return []
                
            cred = session.get(Credential, cred_uuid)
            if not cred:
                return []
            
            if cred.type == "google_ai":
                return [
                    {"label": "Gemini 2.0 Flash (Exp)", "value": "gemini-2.0-flash-exp"},
                    {"label": "Gemini 1.5 Pro", "value": "gemini-1.5-pro-latest"},
                    {"label": "Gemini 1.5 Flash", "value": "gemini-1.5-flash-latest"},
                ]
            elif cred.type == "github_copilot":
                return [
                    {"label": "GPT-4o (Copilot)", "value": "gpt-4o"},
                    {"label": "Claude 3.5 Sonnet (Copilot)", "value": "claude-3.5-sonnet"},
                ]
            elif cred.type == "ai_provider":
                 return [
                    {"label": "GPT-4o (OpenAI)", "value": "openai/gpt-4o"},
                    {"label": "GPT-4o Mini (OpenAI)", "value": "openai/gpt-4o-mini"},
                    {"label": "Claude 3.5 Sonnet (Anthropic)", "value": "anthropic/claude-3.5-sonnet"},
                    {"label": "Gemini 2.0 Flash (Google)", "value": "google/gemini-2.0-flash-exp:free"},
                    {"label": "Llama 3.3 70B (Meta)", "value": "meta-llama/llama-3.3-70b-instruct:free"},
                    {"label": "DeepSeek R1", "value": "deepseek/deepseek-r1"},
                 ]
            return []
    except Exception:
        return []


from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """Execute LLM text generation."""
    config = context.resolve_config()
    input_item = context.input_data[0] if context.input_data else WorkflowItem(json={})
    
    cred_id = config.get("credential")
    model_name = config.get("model")
    prompt = config.get("prompt") # Resolved by V2
    
    if not cred_id or not model_name or not prompt:
        raise ValueError("Missing configuration (credential, model, or prompt)")
        
    cred_data = get_full_credential_by_id(cred_id)
    if not cred_data:
        raise ValueError(f"Credential '{cred_id}' not found")
        
    try:
        result = await ai_service.call_llm(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            credential=cred_data,
            temperature=config.get("temperature", 0.7)
        )
        
        return [WorkflowItem(
            json={
                **input_item.json_data,
                "text": result.get("content", ""),
                "usage": result.get("usage", {})
            },
            binary=input_item.binary_data,
            pairedItem=input_item.paired_item
        )]
    except Exception as e:
        raise RuntimeError(f"LLM Error: {str(e)}")


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("credential"): errors.append("Credential is required")
    if not config.get("model"): errors.append("Model is required")
    if not config.get("prompt"): errors.append("Prompt is required")
    return {"valid": len(errors) == 0, "errors": errors}

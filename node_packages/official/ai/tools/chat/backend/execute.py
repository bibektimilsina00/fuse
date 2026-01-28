"""
AI Chat Model Configuration Node

Configures an LLM for use in agents.
"""

from typing import Any, Dict, List
import uuid
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

# Helper to access DB (internal node privilege)
from sqlmodel import Session
from fuse.database import engine
from fuse.credentials.models import Credential


async def get_models(context: Dict[str, Any], dependency_values: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Fetch available models based on correct provider credential.
    """
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
                    {"label": "o1-preview (Copilot)", "value": "o1-preview"},
                     {"label": "o1-mini (Copilot)", "value": "o1-mini"},
                ]
            elif cred.type == "ai_provider":
                 # OpenRouter/Generic
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


async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Configure chat model settings.
    """
    config = context.resolve_config()
    
    # Return a WorkflowItem that contains the config
    # This item will be passed to Agent node via connection
    return [WorkflowItem(
        json={
            "model": {
                "model_name": config.get("model"),
                "credential_id": config.get("credential"),
                "temperature": config.get("temperature", 0.7)
            }
        }
    )]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("credential"):
        errors.append("Credential is required")
    if not config.get("model"):
        errors.append("Model is required")
    return {"valid": len(errors) == 0, "errors": errors}

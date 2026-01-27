"""
AI LLM Node Plugin

Simple text generation using LLMs.
"""

from jinja2 import Template
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


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute LLM text generation."""
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    cred_id = config.get("credential")
    model_name = config.get("model")
    prompt_raw = config.get("prompt")
    
    if not cred_id or not model_name or not prompt_raw:
        raise ValueError("Missing configuration (credential, model, or prompt)")
        
    cred_data = get_full_credential_by_id(cred_id)
    if not cred_data:
        raise ValueError(f"Credential '{cred_id}' not found")
        
    # Render prompt
    template_context = {
        "input": inputs,
        "inputs": inputs,
        "workflow_id": context.get("workflow_id"),
        **context.get("results", {})
    }
    
    try:
        prompt = Template(prompt_raw).render(template_context)
    except Exception:
        prompt = prompt_raw
        
    try:
        result = await ai_service.call_llm(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            credential=cred_data,
            temperature=config.get("temperature", 0.7)
        )
        
        return {
            "text": result.get("content", ""),
            "usage": result.get("usage", {})
        }
    except Exception as e:
        raise RuntimeError(f"LLM Error: {str(e)}")


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("credential"): errors.append("Credential is required")
    if not config.get("model"): errors.append("Model is required")
    if not config.get("prompt"): errors.append("Prompt is required")
    return {"valid": len(errors) == 0, "errors": errors}

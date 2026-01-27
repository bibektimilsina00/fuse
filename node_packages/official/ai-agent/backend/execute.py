"""
AI Agent Node Plugin

Autonomous agent execution.
"""

from jinja2 import Template
from typing import Any, Dict, List

# Internal imports
from fuse.ai.service import ai_service
from fuse.credentials.service import get_full_credential_by_id


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute autonomous agent.
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # 1. Get Model Config from Inputs (connected node)
    # The Chat Model node outputs {"model": {...}}
    # So inputs["chat_model"] should contain that object
    
    chat_model_input = inputs.get("chat_model")
    
    # Handle case where input structure might vary based on connection type
    model_config = None
    if isinstance(chat_model_input, dict):
        if "model" in chat_model_input:
            model_config = chat_model_input["model"]
        else:
            model_config = chat_model_input
            
    if not model_config:
         # Fallback search in all inputs (legacy behavior compatibility)
        for val in inputs.values():
            if isinstance(val, dict) and "model" in val:
                model_config = val["model"]
                break
    
    if not model_config or not isinstance(model_config, dict):
        return {"error": "Chat Model not connected or invalid configuration."}
        
    cred_id = model_config.get("credential_id")
    model_name = model_config.get("model_name")
    
    if not cred_id or not model_name:
         return {"error": "Invalid Chat Model params (missing credential or name)."}

    # 2. Get Credentials
    cred_data = get_full_credential_by_id(cred_id)
    if not cred_data:
        return {"error": f"Credential '{cred_id}' not found"}

    # 3. Prepare Prompt/Goal
    goal_raw = config.get("goal")
    input_text = config.get("input_text") or inputs
    
    template_context = {
        "input": inputs,
        "inputs": inputs,
        "workflow_id": context.get("workflow_id"),
        **context.get("results", {})
    }
    
    try:
        goal = Template(goal_raw).render(template_context)
    except Exception:
        goal = goal_raw
        
    system_instruction = (
        "You are an autonomous AI agent. Your goal is to process the input data and achieve the specified objective. "
        "Think step by step. Provide a final comprehensive result."
    )
    
    prompt = f"GOAL: {goal}\n\nCONTEXT DATA: {input_text}\n\nPlease analyze the data and fulfill the goal."

    # 4. Call LLM
    try:
        result = await ai_service.call_llm(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            model=model_name,
            credential=cred_data
        )
        
        return {
            "result": result.get("content", "No response"),
            "status": "success",
            "usage": result.get("usage", {})
        }
    except Exception as e:
        raise RuntimeError(f"AI Agent Error: {str(e)}")


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("goal"):
        errors.append("Goal is required")
    return {"valid": len(errors) == 0, "errors": errors}

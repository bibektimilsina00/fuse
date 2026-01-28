"""
AI Agent Node Plugin

Autonomous agent execution.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

# Internal imports
from fuse.ai.service import ai_service
from fuse.credentials.service import get_full_credential_by_id

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Execute autonomous agent.
    """
    config = context.resolve_config()
    inputs = context.input_data # List[WorkflowItem] or Dict
    
    # 1. Find Model Config in Inputs
    model_config = None
    
    # Helper to scan a list of items for model definition
    def find_model_config(items):
        for item in items:
            data = item.json_data if isinstance(item, WorkflowItem) else item
            if isinstance(data, dict):
                if "model" in data:
                    return data["model"]
                # Also check if the item itself IS the model config (legacy or simplified)
                if "model_name" in data and "credential_id" in data:
                    return data
        return None

    if isinstance(inputs, list):
        model_config = find_model_config(inputs)
    elif isinstance(inputs, dict):
         # Try specific key first
        if "chat_model" in inputs:
            val = inputs["chat_model"]
            if isinstance(val, list):
                 model_config = find_model_config(val)
            elif isinstance(val, dict):
                 model_config = val.get("model") or val
        
        # Fallback to values
        if not model_config:
             for val in inputs.values():
                 if isinstance(val, list):
                     found = find_model_config(val)
                     if found:
                         model_config = found
                         break
                 elif isinstance(val, dict) and "model" in val:
                     model_config = val["model"]
                     break
    
    if not model_config or not isinstance(model_config, dict):
        raise RuntimeError("Chat Model not connected or invalid configuration.")
        
    cred_id = model_config.get("credential_id")
    model_name = model_config.get("model_name")
    
    if not cred_id or not model_name:
         raise ValueError("Invalid Chat Model params (missing credential or name).")

    # 2. Get Credentials
    cred_data = get_full_credential_by_id(cred_id)
    if not cred_data:
        raise ValueError(f"Credential '{cred_id}' not found")

    # 3. Prepare Prompt/Goal
    goal = config.get("goal")
    input_text = config.get("input_text")
    
    # If input_text not specified, use the raw inputs as data context
    if not input_text:
        # Serialize first input item
        if isinstance(inputs, list) and inputs:
            input_text = str(inputs[0].json_data)
        elif isinstance(inputs, dict):
            input_text = str(inputs)
        
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
        
        input_item = None
        if isinstance(inputs, list) and inputs:
            input_item = inputs[0]
        
        return [WorkflowItem(
            json={
                "result": result.get("content", "No response"),
                "status": "success",
                "usage": result.get("usage", {})
            },
            binary=input_item.binary_data if input_item else {},
            pairedItem=input_item.paired_item if input_item else None
        )]
    except Exception as e:
        raise RuntimeError(f"AI Agent Error: {str(e)}")


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("goal"):
        errors.append("Goal is required")
    return {"valid": len(errors) == 0, "errors": errors}

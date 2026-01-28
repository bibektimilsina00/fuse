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
    inputs = context.input_data # Main flow input
    
    # 1. Resolve Dependencies via specific handles
    model_configs = context.get_inputs_by_handle("chat_model")
    memory_configs = context.get_inputs_by_handle("memory")
    tool_configs = context.get_inputs_by_handle("tools")

    # Handle multiple tool connections by collecting all 'tool' definitions
    tools = []
    for tc in tool_configs:
        if isinstance(tc, dict) and "tool" in tc:
            tools.append(tc["tool"])
        elif isinstance(tc, list):
             # Handle case where tool node returns a list of items
             for item in tc:
                 data = item.json_data if hasattr(item, "json_data") else item
                 if isinstance(data, dict) and "tool" in data:
                     tools.append(data["tool"])

    # Resolve model config
    model_config = None
    if model_configs:
        first_model = model_configs[0]
        # Recursively find model dict in case it's wrapped in WorkflowItem or list
        if isinstance(first_model, list) and first_model:
            first_model = first_model[0]
        
        data = first_model.json_data if hasattr(first_model, "json_data") else first_model
        model_config = data.get("model") or data
    
    if not model_config or not isinstance(model_config, dict):
        raise RuntimeError("Chat Model not connected to 'Chat Model' handle.")
        
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
    
    # If input_text not specified, use the raw inputs as data context (from main flow)
    if not input_text:
        if isinstance(inputs, list) and inputs:
            input_text = str(inputs[0].json_data)
        elif isinstance(inputs, dict):
            input_text = str(inputs)
    
    tools_desc = ""
    if tools:
        tools_desc = "\n\nYou have the following tools available:\n"
        for t in tools:
            tools_desc += f"- {t.get('name')}: {t.get('description')}\n"

    system_instruction = (
        "You are an autonomous AI agent. Your goal is to process the input data and achieve the specified objective. "
        "Think step by step. Provide a final comprehensive result."
    )
    if tools:
        system_instruction += f"\n\nTOOLS AVAILABLE:\n{tools_desc}"
    
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

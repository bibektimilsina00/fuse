from typing import Any, Dict, List, Optional
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry
import logging

logger = logging.getLogger(__name__)

@NodeRegistry.register
class AgentNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="ai.agent",
            label="AI Agent",
            type="action",
            description="Autonomous agent capable of using specific tools.",
            category="AI",
            inputs=[
                # Connection Inputs (Visual handles)
                NodeInput(name="chat_model", type="ai_model", label="Chat Model", required=True),
                NodeInput(name="memory", type="ai_memory", label="Memory", required=False),
                NodeInput(name="tools", type="ai_tool", label="Tools", required=False),
                
                # Configuration Inputs
                NodeInput(name="goal", type="string", label="Goal / System Prompt", required=True, description="What is the agent supposed to do?"),
                NodeInput(name="input_text", type="string", label="Input Text", description="User input to process (optional, defaults to workflow input)")
            ],
            outputs=[
                NodeOutput(name="result", type="string", label="Final Result")
            ]
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        """Execute autonomous agent goal"""
        from fuse.ai.service import ai_service
        from fuse.credentials.service import get_full_credential_by_id
        
        config = context.get("node_config", {})
        goal_raw = config.get("goal")
        
        # Extract dependencies from input_data
        # Input data might be a dictionary with keys if merged, or we need to find them
        # We assume the engine merges inputs or we manually inspect context
        
        model_config = None
        memory_config = None
        tools_config = []
        
        # Helper to find config in nested data
        def find_key(data, key):
            if isinstance(data, dict):
                if key in data: return data[key]
                for k, v in data.items():
                    res = find_key(v, key)
                    if res: return res
            return None

        # Logic to extract model from input_data
        # This depends on how the engine handles multi-input. 
        # Assuming input_data contains outputs from upstream nodes.
        if isinstance(input_data, dict):
            model_config = input_data.get("model")
            memory_config = input_data.get("memory")
            tool = input_data.get("tool")
            if tool: tools_config.append(tool)
        elif isinstance(input_data, list):
            for item in input_data:
                if isinstance(item, dict):
                    if "model" in item: model_config = item["model"]
                    if "memory" in item: memory_config = item["memory"]
                    if "tool" in item: tools_config.append(item["tool"])

        # Fallback: if not in input_data, maybe try to fetch from context (not implemented here)
        
        if not model_config:
            # Check if we can fallback to default? No, user wanted to connect.
            # But for safety, providing a helpful error
            return {"error": "No Chat Model connected. Please connect a 'Chat Model' node to the Agent."}
            
        cred_id = model_config.get("credential_id")
        model_name = model_config.get("model_name")
        
        if not cred_id or not model_name:
             return {"error": "Invalid Chat Model configuration."}

        cred_data = get_full_credential_by_id(cred_id)
        if not cred_data:
            return {"error": f"Credential '{cred_id}' not found"}

        # Goal rendering
        try:
            template_context = {
                "input": input_data,
                "workflow_id": context.get("workflow_id"),
                **context.get("results", {})
            }
            from jinja2 import Template
            goal = Template(goal_raw).render(template_context)
        except Exception as e:
            goal = goal_raw
            
        system_instruction = (
            "You are an autonomous AI agent. Your goal is to process the input data and achieve the specified objective. "
            "Think step by step. Provide a final comprehensive result."
        )
        
        prompt = f"GOAL: {goal}\n\nCONTEXT DATA: {input_data}\n\nPlease analyze the data and fulfill the goal."

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

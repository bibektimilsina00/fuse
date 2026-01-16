from typing import Any, Dict, List
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

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
                NodeInput(name="credential", type="credential", label="AI Provider", credential_type="ai_provider", required=True),
                NodeInput(name="model", type="select", label="Intelligence", options=[
                    {"label": "Gemini 2.0 Flash (Free)", "value": "google/gemini-2.0-flash-exp:free"},
                    {"label": "Llama 3.3 70B (Free)", "value": "meta-llama/llama-3.3-70b-instruct:free"},
                    {"label": "Llama 3.1 8B (Free)", "value": "meta-llama/llama-3.1-8b-instruct:free"},
                    {"label": "Mistral 7B (Free)", "value": "mistralai/mistral-7b-instruct:free"}
                ], default="google/gemini-2.0-flash-exp:free"),
                NodeInput(name="goal", type="string", label="Goal", required=True)
            ],
            outputs=[
                NodeOutput(name="result", type="string", label="Final Result")
            ]
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        """Execute autonomous agent goal"""
        from fuse.ai.service import ai_service
        
        config = context.get("node_config", {})
        goal_raw = config.get("goal")
        model = config.get("model", "google/gemini-2.0-flash-exp:free")
        
        # Hotpatch invalid models
        model_mapping = {
            "gemini": "google/gemini-2.0-flash-exp:free",
            "llama": "meta-llama/llama-3.3-70b-instruct:free",
            "microsoft/phi-3-medium-128k-instruct:free": "google/gemini-2.0-flash-exp:free",
            "huggingfaceh4/zephyr-orpo-141b-a35b-v0.1:free": "google/gemini-2.0-flash-exp:free"
        }
        if model in model_mapping:
            model = model_mapping[model]

        cred_id = config.get("credential")
        
        if not goal_raw:
            return {"error": "Goal must be provided for the AI Agent"}
            
        # 1. Variable Injection for Goal
        try:
            template_context = {
                "input": input_data,
                "workflow_id": context.get("workflow_id"),
                "execution_id": context.get("execution_id"),
                **context.get("results", {}),
                **(input_data if isinstance(input_data, dict) else {})
            }
            from jinja2 import Template
            goal = Template(goal_raw).render(template_context)
        except Exception as e:
            goal = goal_raw
            logger.warning(f"Agent goal rendering failed: {e}")
            
        if not cred_id:
            return {"error": "Credential must be provided for the AI Agent"}
            
        from fuse.credentials.service import get_full_credential_by_id
        cred_data = get_full_credential_by_id(cred_id)
        if not cred_data:
            return {"error": f"Credential '{cred_id}' not found"}
            
        system_instruction = (
            "You are an autonomous AI agent. Your goal is to process the input data and achieve the specified objective. "
            "Think step by step. Provide a final comprehensive result."
        )
        
        # Prepare the prompt
        prompt = f"GOAL: {goal}\n\nINPUT DATA: {input_data}\n\nPlease analyze the data and fulfill the goal."
        
        try:
            result = await ai_service.call_llm(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                credential=cred_data
            )
            
            return {
                "result": result.get("content", "No response from agent"),
                "status": "success",
                "usage": result.get("usage", {})
            }
        except Exception as e:
            raise RuntimeError(f"AI Agent Error: {str(e)}")

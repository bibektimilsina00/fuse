from typing import Any, Dict, List
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class ChatModelNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="ai.chat_model",
            label="Chat Model",
            type="action",
            description="Configure a Chat Model (LLM) for use in agents.",
            category="AI",
            inputs=[
                NodeInput(name="credential", type="credential", label="AI Provider", credential_type="ai_provider", required=True),
                NodeInput(name="model", type="select", label="Model", options=[
                    {"label": "Gemini 2.0 Flash (Free)", "value": "google/gemini-2.0-flash-exp:free"},
                    {"label": "Llama 3.3 70B (Free)", "value": "meta-llama/llama-3.3-70b-instruct:free"},
                    {"label": "GPT-4o (OpenAI)", "value": "openai/gpt-4o"},
                    {"label": "Claude 3.5 Sonnet (Anthropic)", "value": "anthropic/claude-3.5-sonnet"},
                ], default="google/gemini-2.0-flash-exp:free"),
                NodeInput(name="temperature", type="number", label="Temperature", default=0.7),
            ],
            outputs=[
                NodeOutput(name="model", type="ai_model", label="Model")
            ]
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        config = context.get("node_config", {})
        
        return {
            "model": {
                "provider": "openrouter", # Using existing service
                "model_name": config.get("model"),
                "credential_id": config.get("credential"),
                "temperature": config.get("temperature", 0.7)
            }
        }

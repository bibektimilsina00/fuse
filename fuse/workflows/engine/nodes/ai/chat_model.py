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
                NodeInput(
                    name="credential", 
                    type="credential", 
                    label="AI Provider", 
                    credential_type="ai_provider,google_ai,github_copilot", 
                    required=True
                ),
                NodeInput(
                    name="model", 
                    type="select", 
                    label="Model", 
                    dynamic_options="get_models", 
                    dynamic_dependencies=["credential"], 
                    required=True
                ),
                NodeInput(name="temperature", type="number", label="Temperature", default=0.7),
            ],
            outputs=[
                NodeOutput(name="model", type="ai_model", label="Model")
            ]
        )

    async def get_models(self, context: Dict[str, Any], dependency_values: Dict[str, Any]) -> List[Dict[str, str]]:
        credential_id = dependency_values.get("credential")
        if not credential_id:
             return []
        
        from sqlmodel import Session
        from fuse.database import engine
        from fuse.credentials.models import Credential
        import uuid

        try:
            with Session(engine) as session:
                try:
                    cred_id = uuid.UUID(credential_id)
                except ValueError:
                    return []
                    
                cred = session.get(Credential, cred_id)
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

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        config = context.get("node_config", {})
        
        # We don't need to resolve the provider here; the consumer (AIAgentNode) will
        # fetch the credential and determine the provider from the credential type.
        
        return {
            "model": {
                "model_name": config.get("model"),
                "credential_id": config.get("credential"),
                "temperature": config.get("temperature", 0.7)
            }
        }

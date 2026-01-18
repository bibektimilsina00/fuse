from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class MemoryNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="ai.memory",
            label="Memory",
            type="action",
            description="Configure conversation memory for the agent.",
            category="AI",
            inputs=[
                NodeInput(name="type", type="select", label="Memory Type", options=[
                    {"label": "Window Buffer", "value": "window_buffer"}
                ], default="window_buffer"),
                NodeInput(name="k", type="number", label="Window Size (k)", default=5, description="Number of past interactions to remember")
            ],
            outputs=[
                NodeOutput(name="memory", type="ai_memory", label="Memory")
            ]
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        config = context.get("node_config", {})
        return {
            "memory": {
                "type": config.get("type", "window_buffer"),
                "k": config.get("k", 5)
            }
        }

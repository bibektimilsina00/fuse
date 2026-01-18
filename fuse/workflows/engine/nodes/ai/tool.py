from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class ToolNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="ai.tool",
            label="Tool",
            type="action",
            description="Define a tool for the agent to use.",
            category="AI",
            inputs=[
                NodeInput(name="tool_name", type="select", label="Tool", options=[
                    {"label": "Calculator", "value": "calculator"},
                    {"label": "Wikipedia", "value": "wikipedia"},
                    {"label": "Google Search", "value": "search"}
                ], default="calculator")
            ],
            outputs=[
                NodeOutput(name="tool", type="ai_tool", label="Tool")
            ]
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        config = context.get("node_config", {})
        return {
            "tool": {
                "name": config.get("tool_name", "calculator")
            }
        }

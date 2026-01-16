from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class MergeNode(BaseNode):
    """Merge multiple inputs"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="logic.merge",
            label="Merge",
            type="logic",
            description="Converges multiple parallel paths back into a single flow.",
            category="Logic",
            inputs=[
                NodeInput(name="wait_for", type="select", label="Wait Strategy", default="all", options=[
                    {"label": "All", "value": "all"},
                    {"label": "Any", "value": "any"}
                ])
            ],
            outputs=[
                NodeOutput(name="data", type="json", label="Merged Results")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        """Merge inputs from all previous nodes"""
        results = context.get("results", {})
        return {"output": results}

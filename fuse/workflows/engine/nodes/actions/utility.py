from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class NoOpNode(BaseNode):
    """Placeholder node that does nothing"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="utility.noop",
            label="No-Op (Debug)",
            type="action",
            description="Placeholder node that does nothing. Useful for debugging.",
            category="Utilities",
            inputs=[],
            outputs=[],
            runtime="internal",
            error_policy="continue"
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        return input_data

from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class ParallelNode(BaseNode):
    """Splits execution into multiple parallel branches"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="logic.parallel",
            label="Parallel Fork",
            type="logic",
            description="Splits execution into multiple parallel branches",
            category="Logic",
            inputs=[
                NodeInput(name="branches", type="number", label="Branch Count", default=2)
            ],
            outputs=[
                NodeOutput(name="active", type="boolean", label="Branch Started")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # The execution engine handles the actual forking based on the node type
        # This node simply confirms the start of the branches
        return {"active": True}

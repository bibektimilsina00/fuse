from typing import Any, Dict
from datetime import datetime
from src.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from src.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class PauseNode(BaseNode):
    """Pause workflow execution until manually resumed or condition met"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="execution.pause",
            label="Pause Workflow",
            type="logic",
            description="Pause workflow execution until manually resumed or condition met.",
            category="Logic",
            inputs=[
                NodeInput(name="reason", type="string", label="Pause Reason")
            ],
            outputs=[
                NodeOutput(name="resumed_at", type="string", label="Resumed At")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # The engine would handle the suspension state.
        # This is a placeholder for the node's schema and basic execution metadata.
        return {"resumed_at": datetime.utcnow().isoformat()}

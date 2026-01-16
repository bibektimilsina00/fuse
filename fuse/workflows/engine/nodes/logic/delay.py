from typing import Any, Dict
import asyncio
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class DelayNode(BaseNode):
    """Pauses execution for a specified duration"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="logic.delay",
            label="Delay",
            type="logic",
            description="Pauses execution for a specified duration",
            category="Logic",
            inputs=[
                NodeInput(name="seconds", type="number", label="Seconds", default=5, required=True)
            ],
            outputs=[
                NodeOutput(name="finished", type="boolean", label="Resumed")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        config = context.get("node_config", {})
        seconds = float(config.get("seconds", 5))
        
        await asyncio.sleep(seconds)
        
        return {"finished": True}

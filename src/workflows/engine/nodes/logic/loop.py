from typing import Any, Dict
from src.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from src.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class LoopNode(BaseNode):
    """Iterate over items"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="logic.loop",
            label="Loop",
            type="logic",
            description="Iterates over an array of items.",
            category="Logic",
            inputs=[
                NodeInput(name="items", type="array", label="Input Array", required=True)
            ],
            outputs=[
                NodeOutput(name="item", type="any", label="{{loop.outputs.item}}"),
                NodeOutput(name="index", type="number", label="{{loop.outputs.index}}"),
                NodeOutput(name="total", type="number", label="{{loop.outputs.total}}")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        """Execute loop"""
        config = context.get("node_config", {})
        items_field = config.get("items_field", "items")
        
        items = input_data.get(items_field, []) if isinstance(input_data, dict) else input_data
        
        # Fallback to items defined in config if input is empty
        if not items:
            items = config.get("items", [])
        
        return {
            "items": items if isinstance(items, list) else [items],
            "total": len(items) if isinstance(items, list) else 1
        }

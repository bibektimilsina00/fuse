from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class SwitchNode(BaseNode):
    """Multi-way branching based on value matching"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="condition.switch",
            label="Switch",
            type="logic",
            description="Multi-way branching based on value matching.",
            category="Logic",
            inputs=[
                NodeInput(name="value", type="string", label="Value to Switch", required=True),
                NodeInput(name="cases", type="json", label="Cases (JSON Object)", required=True)
            ],
            outputs=[
                NodeOutput(name="matched", type="string", label="Matched Case")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        config = context.get("node_config", {})
        value = str(config.get("value", input_data))
        cases = config.get("cases", {})
        
        matched_case = "default"
        for key in cases.keys():
            if str(key) == value:
                matched_case = key
                break
        
        return {"matched": matched_case}

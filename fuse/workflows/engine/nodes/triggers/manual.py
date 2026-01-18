from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class ManualTriggerNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="manual.trigger",
            label="Manual Trigger",
            type="trigger",
            description="Starts a workflow manually with provided initial data.",
            inputs=[],
            outputs=[
                NodeOutput(name="output", type="json", label="Initial Data")
            ],
            category="Trigger",
            trigger_group="manual"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # Manual trigger just passes through any initial data or an empty dict
        return input_data or {}

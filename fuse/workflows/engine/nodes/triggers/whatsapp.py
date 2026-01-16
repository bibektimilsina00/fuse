from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class WhatsAppTriggerNode(BaseNode):
    """Triggers when a WhatsApp message is received"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="whatsapp.receive",
            label="WhatsApp Message",
            type="trigger",
            description="Triggers when a WhatsApp message is received.",
            category="Trigger",
            inputs=[
                NodeInput(name="phone_number_id", type="string", label="Phone Number ID", required=True)
            ],
            outputs=[
                NodeOutput(name="sender", type="string", label="From Number"),
                NodeOutput(name="message", type="string", label="Message Text")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        return input_data

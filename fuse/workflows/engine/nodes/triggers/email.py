from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeOutput, NodeInput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class EmailTriggerNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="email.receive",
            label="Email Received",
            type="trigger",
            description="Triggers when a new email is received.",
            category="Trigger",
            inputs=[
                NodeInput(name="address", type="string", label="Monitor Address", required=True)
            ],
            outputs=[
                NodeOutput(name="from", type="string", label="Sender"),
                NodeOutput(name="subject", type="string", label="Subject"),
                NodeOutput(name="body", type="string", label="Email Body")
            ],
            trigger_group="app"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # In a real implementation, this would connect to an email server
        # For now, return mock email data
        return {
            "from": input_data.get("from", "sender@example.com"),
            "to": context.get("email_address", "workflow@yourdomain.com"),
            "subject": input_data.get("subject", "New Email"),
            "body": input_data.get("body", ""),
            "html_body": input_data.get("html_body", ""),
            "attachments": input_data.get("attachments", []),
            "received_at": input_data.get("timestamp"),
            "message_id": input_data.get("message_id")
        }

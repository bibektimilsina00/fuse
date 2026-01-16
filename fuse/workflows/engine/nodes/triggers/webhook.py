from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeOutput, NodeInput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class WebhookTriggerNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="webhook.receive",
            label="Webhook",
            type="trigger",
            description="Triggers when an external HTTP request is received.",
            category="Trigger",
            inputs=[
                NodeInput(name="path", type="string", label="Endpoint Path", required=True)
            ],
            outputs=[
                NodeOutput(name="body", type="json", label="Request Body"),
                NodeOutput(name="headers", type="json", label="Headers")
            ]
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # In a real implementation, this would receive webhook data
        # For now, return mock webhook data
        return {
            "body": input_data.get("body", {}),
            "headers": input_data.get("headers", {}),
            "query": input_data.get("query", {}),
            "method": input_data.get("method", context.get("method", "POST")),
            "webhook_url": f"/webhooks/{context.get('workflow_id', 'unknown')}",
            "received_at": input_data.get("timestamp")
        }

import logging
from typing import Any, Dict

from fuse.credentials.service import resolve_secret
from fuse.workflows.engine.nodes.base import BaseNode, NodeInput, NodeOutput, NodeSchema
from fuse.workflows.engine.nodes.registry import NodeRegistry

logger = logging.getLogger(__name__)


@NodeRegistry.register
class WhatsAppActionNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="whatsapp.send",
            label="Send WhatsApp Message",
            type="action",
            description="Sends a WhatsApp Cloud API message.",
            category="Communication",
            inputs=[
                NodeInput(
                    name="auth",
                    type="credential",
                    label="WhatsApp Account",
                    credential_type="whatsapp",
                    required=True,
                ),
                NodeInput(
                    name="to", type="string", label="Recipient Number", required=True
                ),
                NodeInput(
                    name="message", type="string", label="Message", required=True
                ),
            ],
            outputs=[NodeOutput(name="status", type="string", label="Delivery Status")],
            error_policy="continue",
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        config = context.get("node_config", {})
        to_number = config.get("to", "")
        message_tpl = config.get("message", "")

        from jinja2 import Template

        template_context = {
            "input": input_data,
            **context.get("results", {}),
            **(input_data if isinstance(input_data, dict) else {}),
        }

        try:
            message = Template(message_tpl).render(template_context)
        except Exception:
            message = message_tpl

        # Mock execution for now
        logger.info(f"Sending WhatsApp message to {to_number}: {message}")

        return {
            "status": "sent",
            "message": message,
            "to": to_number,
            "response": {"message_id": "wamid.mock_id_12345"},
        }

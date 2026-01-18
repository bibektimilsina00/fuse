from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeOutput, NodeInput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class FormTriggerNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="form.submit",
            label="Form Submission",
            type="trigger",
            description="Triggers when an internal or external form is submitted.",
            category="Trigger",
            inputs=[
                NodeInput(name="form_id", type="string", label="Form ID", required=True)
            ],
            outputs=[
                NodeOutput(name="data", type="json", label="Form Data")
            ],
            trigger_group="form"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # In a real implementation, this would validate and process form data
        # For now, return mock form submission data
        return {
            "form_data": input_data.get("form_data", {}),
            "form_name": context.get("form_name", "Untitled Form"),
            "submitter_email": input_data.get("email"),
            "submitter_ip": input_data.get("ip_address"),
            "submitted_at": input_data.get("timestamp"),
            "form_url": f"/forms/{context.get('form_name', 'untitled').lower().replace(' ', '-')}"
        }

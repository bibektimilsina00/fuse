from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeOutput, NodeInput
from fuse.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class ScheduleTriggerNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="schedule.cron",
            label="Timer",
            type="trigger",
            description="Triggers the workflow at a specific interval.",
            category="Trigger",
            inputs=[
                NodeInput(name="frequency", type="select", label="Frequency", default="seconds", required=True, options=[
                    {"label": "Seconds", "value": "seconds"},
                    {"label": "Minutes", "value": "minutes"},
                    {"label": "Hours", "value": "hours"},
                    {"label": "Days", "value": "days"}
                ]),
                NodeInput(name="interval", type="number", label="Repeat Every", default=15, required=True),
            ],
            outputs=[
                NodeOutput(name="timestamp", type="string", label="Trigger Time")
            ],
            trigger_group="schedule"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        from datetime import datetime
        
        # In a real implementation, this would be handled by a scheduler
        # For now, return the current timestamp
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "triggered_at": datetime.utcnow().isoformat(),
            "cron_expression": context.get("cron_expression", "0 9 * * *"),
            "timezone": context.get("timezone", "UTC")
        }

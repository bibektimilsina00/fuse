from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry

from jinja2 import Template

@NodeRegistry.register
class IfNode(BaseNode):
    """Conditional branching node with Jinja2 support"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="condition.if",
            label="If Condition",
            type="logic",
            description="Splits flow into True/False branches based on evaluation. Use {{ expression }} or simple variable names.",
            category="Logic",
            inputs=[
                NodeInput(name="condition", type="string", label="Expression", required=True, default="input.status == 'active'")
            ],
            outputs=[
                NodeOutput(name="result", type="boolean", label="Evaluation Result")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        config = context.get("node_config", {})
        condition_raw = config.get("condition", "").strip()
        
        if not condition_raw:
            return {"result": False, "branch_taken": "false"}

        # 1. Prepare Template Context (same as Transform/Set node for consistency)
        template_context = {
            "input": input_data,
            "workflow_id": context.get("workflow_id"),
            "execution_id": context.get("execution_id"),
            **context.get("results", {}),
            **(input_data if isinstance(input_data, dict) else {})
        }
        
        # 2. Process the condition string
        # If it's not wrapped in {{ }}, wrap it so Jinja can evaluate it
        expr = condition_raw
        if not (expr.startswith("{{") and expr.endswith("}}")):
            expr = f"{{{{ {expr} }}}}"
            
        try:
            # Render the expression
            rendered = Template(expr).render(template_context).strip().lower()
            # Convert to boolean
            result = rendered in ["true", "1", "yes", "on"]
        except Exception:
            # Fallback for simple direct comparisons if rendering fails
            result = False
            
        return {"result": result, "branch_taken": "true" if result else "false"}

from typing import Any, Dict
from src.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from src.workflows.engine.nodes.registry import NodeRegistry

@NodeRegistry.register
class DataTransformNode(BaseNode):
    """Map, filter, merge, or pick data from outputs"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="data.transform",
            label="Transform Data",
            type="action",
            description="Map, filter, merge, or pick data from outputs",
            category="Data",
            inputs=[
                NodeInput(name="mapping", type="json", label="Mappings", description="JSON object defining key paths")
            ],
            outputs=[
                NodeOutput(name="output", type="json", label="Transformed Data")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        config = context.get("node_config", {})
        mapping = config.get("mapping", {})
        
        if not mapping:
            return {"output": input_data}

        # 1. Prepare Template Context
        template_context = {
            "input": input_data,
            "workflow_id": context.get("workflow_id"),
            "execution_id": context.get("execution_id"),
            **context.get("results", {}),
            **(input_data if isinstance(input_data, dict) else {})
        }
            
        transformed = {}
        for target_key, template_str in mapping.items():
            if not isinstance(template_str, str):
                transformed[target_key] = template_str
                continue
                
            try:
                # If it's a simple key that exists in input_data, prioritized
                if template_str in template_context and not ("{{" in template_str):
                    transformed[target_key] = template_context[template_str]
                else:
                    # Otherwise treat as a Jinja2 template
                    rendered = Template(template_str).render(template_context)
                    # Attempt to parse as JSON if it looks like it, otherwise keep as string
                    transformed[target_key] = rendered
            except Exception:
                transformed[target_key] = template_str
            
        return {"output": transformed}

@NodeRegistry.register
class DataStoreNode(BaseNode):
    """Persist state or key-value data across execution steps"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="data.store",
            label="Store Data",
            type="action",
            description="Persist state or key-value data across execution steps",
            category="Data",
            inputs=[
                NodeInput(name="key", type="string", label="Key", required=True),
                NodeInput(name="value", type="json", label="Value", required=True)
            ],
            outputs=[
                NodeOutput(name="success", type="boolean", label="Stored")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # Placeholder for data storage
        return {"success": True}
from jinja2 import Template

@NodeRegistry.register
class DataSetNode(BaseNode):
    """Set or override key-value data in workflow context"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="data.set",
            label="Set Variable",
            type="action",
            description="Set or override key-value data in workflow context. Dynamic values allowed using {{variable}} syntax.",
            category="Utilities",
            inputs=[
                NodeInput(name="key", type="string", label="Variable Name", required=True, default="var_name"),
                NodeInput(name="value", type="string", label="Value", required=True, default="some balance")
            ],
            outputs=[
                NodeOutput(name="output", type="json", label="Stored Data")
            ]
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        config = context.get("node_config", {})
        key = config.get("key", "variable")
        raw_val = config.get("value", "")
        
        # 1. Prepare Template Context
        template_context = {
            "input": input_data,
            "workflow_id": context.get("workflow_id"),
            "execution_id": context.get("execution_id"),
            **context.get("results", {}),
            **(input_data if isinstance(input_data, dict) else {})
        }
        
        # 2. Render Value if it's a string
        rendered_val = raw_val
        if isinstance(raw_val, str):
            try:
                rendered_val = Template(raw_val).render(template_context)
            except Exception:
                # Fallback to raw value if rendering fails
                rendered_val = raw_val
        
        # Return object with the custom key so next nodes can access it via {{key}}
        return {key: rendered_val}

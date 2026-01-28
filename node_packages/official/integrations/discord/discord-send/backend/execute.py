"""
Discord Send Plugin

TODO: Migrate logic from old node system
"""

from typing import Any, Dict, List
import httpx
from jinja2 import Template
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Send Discord message via Webhook.
    """
    resolved_config = context.resolve_config()
    raw_config = context.raw_config
    items = context.input_data # List[WorkflowItem]
    
    webhook_url = resolved_config.get("webhook_url")
    username = resolved_config.get("username")
    content_template = raw_config.get("content", "")
    
    if not webhook_url:
        raise ValueError("Webhook URL is required")
        
    loop_items = items if items else [WorkflowItem(json={})]
    results = []
    
    async with httpx.AsyncClient() as client:
        for item in loop_items:
            item_ctx = {
                "input": item.json_data,
                "inputs": item.json_data,
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id
            }
            
            try:
                content = Template(content_template).render(item_ctx)
            except Exception:
                content = content_template
                
            payload = {"content": content}
            if username:
                payload["username"] = username
                
            resp = await client.post(webhook_url, json=payload)
            
            if resp.status_code not in (200, 204):
                 raise RuntimeError(f"Discord Webhook Error ({resp.status_code}): {resp.text}")
                 
            results.append(WorkflowItem(
                json={"success": True, "status": resp.status_code},
                binary=item.binary_data,
                pairedItem=item.paired_item
            ))
            
    return results


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    return {"valid": True, "errors": []}

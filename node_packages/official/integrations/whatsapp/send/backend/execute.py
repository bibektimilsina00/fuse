from typing import Any, Dict, List
import httpx
from jinja2 import Template
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem
from fuse.credentials.service import get_active_credential

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Send Whatsapp message.
    """
    resolved_config = context.resolve_config()
    raw_config = context.raw_config
    items = context.input_data
    
    cred_id = resolved_config.get("auth")
    if not cred_id:
        raise ValueError("Whatsapp Credential is required")
        
    cred = await get_active_credential(cred_id)
    if not cred:
        raise ValueError("Credential not found")
        
    access_token = cred["data"].get("access_token")
    phone_number_id = cred["data"].get("phone_number_id")
    
    if not access_token or not phone_number_id:
        raise ValueError("Invalid Whatsapp Credential (missing access_token or phone_number_id)")
        
    text_template = raw_config.get("text", "")
    to_template = raw_config.get("to", "")
    
    loop_items = items if items else [WorkflowItem(json={})]
    results = []
    
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        for item in loop_items:
            item_ctx = {
                "input": item.json_data,
                "inputs": item.json_data,
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id
            }
            
            try:
                to_phone = Template(to_template).render(item_ctx)
                text_body = Template(text_template).render(item_ctx)
            except Exception:
                to_phone = to_template
                text_body = text_template
                
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {"body": text_body}
            }
            
            resp = await client.post(url, json=payload, headers=headers)
            json_resp = resp.json()
            
            success = resp.status_code in (200, 201)
            results.append(WorkflowItem(
                json={"success": success, "response": json_resp},
                binary=item.binary_data,
                pairedItem=item.paired_item
            ))
            
    return results

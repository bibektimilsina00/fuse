"""
Slack Send Node Plugin

Send messages to Slack via Webhook or OAuth API.
"""

from typing import Any, Dict, List, Optional
import httpx
import logging
import asyncio
from jinja2 import Template
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

# Helper to resolve credentials (will be injected or imported)
from fuse.credentials.service import get_active_credential, resolve_secret

logger = logging.getLogger(__name__)

async def list_channels(context: Dict[str, Any], dependency_values: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Fetch list of public channels and users from Slack.
    Used for the dynamic_options in the 'channel' input.
    """
    cred_id = dependency_values.get("webhook_url")
    logger.info(f"Fetching channels for credential: {cred_id}")
    
    if not cred_id:
        return []

    token = None

    # Resolve token logic (similar to execute)
    if cred_id and not cred_id.startswith(("http", "xox")):
        cred = await get_active_credential(cred_id)
        if cred:
            token = (
                cred["data"].get("bot_token")
                or cred["data"].get("access_token")
                or cred["data"].get("token")
            )

    if not token:
        # Try simple resolve
        token = resolve_secret(cred_id)

    if not token or not token.startswith("xox"):
        return []

    options = []
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch Channels
        try:
            resp = await client.get(
                "https://slack.com/api/conversations.list",
                headers=headers,
                params={"types": "public_channel,private_channel", "limit": 100},
            )
            if resp.status_code == 200:
                data = resp.json()
                for ch in data.get("channels", []):
                    options.append({"label": f"#{ch['name']}", "value": ch["id"]})
        except Exception as e:
            logger.warning(f"Failed to fetch Slack channels: {e}")

        # Fetch Users
        try:
            resp = await client.get(
                "https://slack.com/api/users.list",
                headers=headers,
                params={"limit": 100},
            )
            if resp.status_code == 200:
                data = resp.json()
                for u in data.get("members", []):
                    if (
                        not u.get("deleted")
                        and not u.get("is_bot")
                        and u.get("name") != "slackbot"
                    ):
                        options.append({"label": f"@{u['name']}", "value": u['id']})
        except Exception as e:
            logger.warning(f"Failed to fetch Slack users: {e}")

    return sorted(options, key=lambda x: x["label"])


async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Send Slack message.
    """
    # We resolve config once for static fields
    resolved_config = context.resolve_config()
    raw_config = context.raw_config
    items = context.input_data # List[WorkflowItem]
    
    credential_id_or_url = resolved_config.get("webhook_url")
    channel = resolved_config.get("channel")
    text_template = raw_config.get("text", "")
    
    token = None
    webhook_url = None

    # 1. Resolve Credentials
    if credential_id_or_url and not credential_id_or_url.startswith(("http", "xox")):
        # Assume it's a UUID/ID
        cred = await get_active_credential(credential_id_or_url)
        if cred:
            token = (
                cred["data"].get("access_token")
                or cred["data"].get("bot_token")
                or cred["data"].get("token")
            )
            if not token and "url" in cred["data"]:
                webhook_url = cred["data"]["url"]

    # 2. Fallback to simple resolve
    if not token and not webhook_url:
        resolved = resolve_secret(credential_id_or_url) if credential_id_or_url else None
        if resolved:
            if resolved.startswith("xox"):
                token = resolved
            else:
                webhook_url = resolved

    # 3. Validate
    if not token and (not webhook_url or "DUMMY" in webhook_url):
        raise ValueError("Valid Slack Credential or Webhook URL is required.")

    # 4. Prepare Batch Loop
    loop_items = items if items else [WorkflowItem(json={})]
    results = []
    
    async with httpx.AsyncClient() as client:
        for item in loop_items:
            # Render Template per item
            item_ctx = {
                "input": item.json_data,
                "inputs": item.json_data,
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id
            }
            
            try:
                message = Template(text_template).render(item_ctx)
            except Exception:
                message = text_template

            # 5. Send Message
            success = False
            responseData = {}
            
            if token:
                # OAuth API Mode
                if not channel:
                    raise ValueError("Channel ID is required when using OAuth Token.")

                api_url = "https://slack.com/api/chat.postMessage"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                payload = {"channel": channel, "text": message}
                response = await client.post(api_url, json=payload, headers=headers)
                data = response.json()
                
                if not data.get("ok"):
                    # We log error but don't hard crash batch unless necessary
                    # raising here for now to match V1 behavior
                    error_code = data.get("error")
                    raise RuntimeError(f"Slack API Error: {error_code}")
                else:
                    success = True
                    responseData = data

            else:
                # Webhook Mode
                url_to_use = webhook_url
                if not url_to_use.startswith(("http://", "https://")):
                    url_to_use = f"https://{url_to_use}"

                payload = {"text": message}
                if channel:
                    payload["channel"] = channel

                response = await client.post(url_to_use, json=payload)

                if response.status_code != 200:
                    raise RuntimeError(
                        f"Slack Webhook returned {response.status_code}: {response.text}"
                    )
                
                success = True
                responseData = {"status_code": response.status_code}
            
            results.append(WorkflowItem(
                json={
                    "success": success,
                    "response": responseData,
                    "message_text": message # Debug info
                },
                binary=item.binary_data,
                pairedItem=item.paired_item
            ))
            
            # Rate limit guard?
            # await asyncio.sleep(0.1) 
    
    return results


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("webhook_url"):
        errors.append("Credential or Webhook URL is required")
    if not config.get("text"):
        errors.append("Message text is required")
    return {"valid": len(errors) == 0, "errors": errors}

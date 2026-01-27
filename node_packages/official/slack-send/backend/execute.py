"""
Slack Send Node Plugin

Send messages to Slack via Webhook or OAuth API.
"""

import httpx
import logging
from jinja2 import Template
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Helper to resolve credentials (will be injected or imported)
from fuse.credentials.service import get_active_credential, resolve_secret


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


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send Slack message.
    
    Args:
        context: Execution context with config, inputs, credentials
        
    Returns:
        Dict with success status and API response
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # Get configuration (config has precedence, but allow input override if needed?)
    # Original code: config only for credential, channel from config, text from config (template)
    
    credential_id_or_url = config.get("webhook_url")
    channel = config.get("channel")
    text_template = config.get("text", "")
    
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

    # 4. Render Template
    template_context = {
        "input": inputs,
        "inputs": inputs,
        "workflow_id": context.get("workflow_id"),
        "execution_id": context.get("execution_id"),
        **context.get("results", {}),
        **(inputs if isinstance(inputs, dict) else {}),
    }

    try:
        message = Template(text_template).render(template_context)
    except Exception:
        message = text_template

    # 5. Send Message
    async with httpx.AsyncClient() as client:
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
                error_code = data.get("error")
                error_msg = f"Slack API Error: {error_code}"
                # Add specific error messaging (omitted for brevity, can add back if needed)
                raise RuntimeError(error_msg)

            return {"success": True, "response": data}

        else:
            # Webhook Mode
            if not webhook_url.startswith(("http://", "https://")):
                webhook_url = f"https://{webhook_url}"

            payload = {"text": message}
            if channel:
                payload["channel"] = channel

            response = await client.post(webhook_url, json=payload)

            if response.status_code != 200:
                raise RuntimeError(
                    f"Slack Webhook returned {response.status_code}: {response.text}"
                )

            return {"success": True, "status_code": response.status_code}


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("webhook_url"):
        errors.append("Credential or Webhook URL is required")
    if not config.get("text"):
        errors.append("Message text is required")
    return {"valid": len(errors) == 0, "errors": errors}

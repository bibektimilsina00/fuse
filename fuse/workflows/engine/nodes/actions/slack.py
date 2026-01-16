import logging
from typing import Any, Dict

import httpx
from fuse.credentials.service import resolve_secret
from fuse.workflows.engine.nodes.base import BaseNode, NodeInput, NodeOutput, NodeSchema
from fuse.workflows.engine.nodes.registry import NodeRegistry

logger = logging.getLogger(__name__)


@NodeRegistry.register
class SlackNode(BaseNode):
    """Slack messaging operations"""

    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="slack.send",
            label="Slack Send",
            type="action",
            description="Posts a Slack message via Webhook or API.",
            category="Communication",
            inputs=[
                NodeInput(
                    name="webhook_url",
                    type="credential",
                    label="Credential or Webhook",
                    credential_type="slack",
                    required=True,
                ),
                # Updated to use dynamic options for channel selection
                NodeInput(
                    name="channel",
                    type="select",
                    label="Channel (e.g. #general)",
                    description="Required if using OAuth Credential",
                    dynamic_options="list_channels",
                    dynamic_dependencies=[
                        "webhook_url"
                    ],  # Frontend should trigger fetch when webhook_url changes
                ),
                NodeInput(name="text", type="string", label="Message Text"),
            ],
            outputs=[NodeOutput(name="success", type="boolean", label="Posted")],
            error_policy="continue",
        )

    async def list_channels(
        self, context: Dict[str, Any], dependency_values: Dict[str, Any]
    ) -> list[Dict[str, str]]:

        logger.info(
            f"DEBUG: Fetching channels for webhook_url: {dependency_values.get('webhook_url')}"
        )
        """Fetch list of public channels and users from Slack."""
        cred_id = dependency_values.get("webhook_url")
        if not cred_id:
            return []

        from fuse.credentials.service import get_active_credential, resolve_secret

        token = None

        # Resolve token same way execute does
        if cred_id and not cred_id.startswith(("http", "xox")):
            cred = await get_active_credential(cred_id)
            if cred:
                # Standardize on 'token' or 'bot_token' or 'access_token'
                token = (
                    cred["data"].get("bot_token")
                    or cred["data"].get("access_token")
                    or cred["data"].get("token")
                )

        if not token:
            # Try simple resolve (for legacy or direct pastes)
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

            # Fetch Users (for DMs)
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
                            options.append({"label": f"@{u['name']}", "value": u["id"]})
            except Exception as e:
                logger.warning(f"Failed to fetch Slack users: {e}")

        return sorted(options, key=lambda x: x["label"])

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        """Send message to Slack"""
        config = context.get("node_config", {})
        credential_id_or_url = config.get("webhook_url")
        channel = config.get("channel")  # Optional for webhook, required for API

        token = None
        webhook_url = None

        from fuse.credentials.service import get_active_credential, resolve_secret

        # 1. Try to get as active credential (handles refresh)
        if credential_id_or_url and not credential_id_or_url.startswith(
            ("http", "xox")
        ):
            # Assume it's an ID
            cred = await get_active_credential(credential_id_or_url)
            if cred:
                token = (
                    cred["data"].get("access_token")
                    or cred["data"].get("bot_token")
                    or cred["data"].get("token")
                )
                if not token and "url" in cred["data"]:
                    webhook_url = cred["data"]["url"]

        # 2. Fallback to simple resolve (legacy webhooks stored as generic credentials)
        if not token and not webhook_url:
            resolved = resolve_secret(credential_id_or_url)
            if resolved.startswith("xox"):
                token = resolved
            else:
                webhook_url = resolved

        # 3. Validate
        if not token and (not webhook_url or "DUMMY" in webhook_url):
            raise ValueError("Valid Slack Credential or Webhook URL is required.")

        from jinja2 import Template

        template_context = {
            "input": input_data,
            "workflow_id": context.get("workflow_id"),
            "execution_id": context.get("execution_id"),
            **context.get("results", {}),
            **(input_data if isinstance(input_data, dict) else {}),
        }

        message_tpl = config.get("text", "")
        try:
            message = Template(message_tpl).render(template_context)
        except Exception:
            message = message_tpl

        async with httpx.AsyncClient() as client:
            if token:
                # OAuth API Mode
                if not channel:
                    # Attempt to fallback to a default if user didn't specify?
                    # API requires channel.
                    raise ValueError(
                        "Channel ID (e.g. #general or C12345) is required when using OAuth Token."
                    )

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

                    if error_code == "not_in_channel":
                        error_msg = f"Slack API Error ({error_code}): Bot is not in channel '{channel}'. Invite it using '/invite @YourApp'."
                    elif error_code == "channel_not_found":
                        error_msg = f"Slack API Error ({error_code}): Channel '{channel}' not found. Check the ID/Name or ensure the bot has 'channels:read' scope."
                    elif error_code == "is_archived":
                        error_msg = f"Slack API Error ({error_code}): Channel '{channel}' is archived and cannot receive messages."
                    elif error_code == "msg_too_long":
                        error_msg = f"Slack API Error (msg_too_long): Message text exceeds Slack's character limit."
                    elif error_code == "missing_scope":
                        error_msg = f"Slack API Error (missing_scope): The bot token lacks required scopes (e.g. 'chat:write'). Re-authenticate or check app settings."
                    elif error_code == "invalid_auth":
                        error_msg = f"Slack API Error (invalid_auth): Invalid authentication token. Please check your credentials."
                    else:
                        error_msg = f"Slack API Error: {error_code}"

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

"""Gmail trigger node.

Polling-based: every time the workflow's scheduler fires this node (or
a `/listen` call hits it during dev) the trigger queries the Gmail API
for new messages matching the user's filter and emits one execution
per message.

For now this is a search-on-invoke node — the polling cadence lives in
the workflow's schedule trigger (or in the listen handler that fires
it once). A dedicated Celery-beat poller + `IntegrationTriggerState`
cursor table arrives with the rest of Google Phase 1.

The `event_type` dropdown is here for parity with the Meta triggers
even though only one event matters for Gmail; we'll add `label_applied`
and `thread_replied` once Pub/Sub-based delivery lands.
"""

from __future__ import annotations

import base64
import re
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"


class GmailTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = "new_message"
    query: str = "is:unread"
    max_results: int = 5
    # Marker the polling scheduler reads/writes once the IntegrationTriggerState
    # table lands. Stored as a string history id from the Gmail `historyId`
    # endpoint — the canonical Gmail cursor.
    history_cursor: str | None = None


class GmailTriggerNode(BaseNode[GmailTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GmailTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gmail",
            name="Gmail",
            category="trigger",
            description=(
                "Fires when Gmail messages matching your query arrive. "
                "Backed by polling — exact-second delivery requires Pub/Sub setup."
            ),
            icon="si:SiGmail",
            color="#ea4335",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": "new_message",
                    "options": [
                        {"label": "New Message", "value": "new_message"},
                    ],
                },
                {
                    "name": "query",
                    "label": "Gmail Search Query",
                    "type": "string",
                    "default": "is:unread",
                    "placeholder": "is:unread from:boss@company.com",
                    "description": (
                        "Standard Gmail search syntax. Defaults to `is:unread`. "
                        "Leave empty to receive every new message."
                    ),
                    "condition": {"field": "event_type", "value": "new_message"},
                },
                {
                    "name": "max_results",
                    "label": "Max messages per poll",
                    "type": "number",
                    "default": 5,
                    "mode": "advanced",
                    "condition": {"field": "event_type", "value": "new_message"},
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "threadId", "type": "string"},
                {"label": "from_email", "type": "string"},
                {"label": "to", "type": "string"},
                {"label": "subject", "type": "string"},
                {"label": "snippet", "type": "string"},
                {"label": "body_text", "type": "string"},
                {"label": "labelIds", "type": "array"},
                {"label": "internalDate", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # When the engine dispatches a webhook-style payload (e.g. from
        # the listen / scheduled-poll path that already fetched the
        # message), pass it through verbatim — same shape we'd produce
        # ourselves below.
        if isinstance(input_data, dict) and input_data.get("id") and input_data.get("payload"):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "q": self.props.query or "",
            "maxResults": max(1, min(self.props.max_results or 5, 100)),
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                listing = await client.get(
                    f"{GMAIL_API}/users/me/messages", headers=headers, params=params
                )
                listing.raise_for_status()
                hits = listing.json().get("messages") or []
                if not hits:
                    return NodeResult(
                        success=True,
                        output_data={"matched": 0, "messages": []},
                    )
                latest = hits[0]
                detail = await client.get(
                    f"{GMAIL_API}/users/me/messages/{latest['id']}",
                    headers=headers,
                )
                detail.raise_for_status()
                return NodeResult(success=True, output_data=_normalize(detail.json()))
        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False,
                error=f"Gmail API error {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"GmailTriggerNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))


# ── helpers ──────────────────────────────────────────────────────────────


_HEADER_KEYS = {"from", "to", "cc", "bcc", "subject", "date", "message-id"}


def _normalize(message: dict[str, Any]) -> dict[str, Any]:
    """Flatten the Gmail message structure into the shape our outputs_schema
    advertises. Downstream nodes can then template `=$step.from_email` /
    `=$step.subject` / `=$step.body_text` without parsing the payload tree.
    """
    payload = message.get("payload") or {}
    headers_list = payload.get("headers") or []
    headers = {
        h["name"].lower(): h["value"]
        for h in headers_list
        if isinstance(h, dict) and h.get("name") and h["name"].lower() in _HEADER_KEYS
    }
    from_full = headers.get("from") or ""
    from_email = _extract_email(from_full)
    body_text = _extract_text_body(payload)
    return {
        "id": message.get("id"),
        "threadId": message.get("threadId"),
        "labelIds": message.get("labelIds") or [],
        "internalDate": message.get("internalDate"),
        "snippet": message.get("snippet") or "",
        "from": from_full,
        "from_email": from_email,
        "to": headers.get("to") or "",
        "subject": headers.get("subject") or "",
        "body_text": body_text,
        "payload": payload,
    }


def _extract_email(from_header: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", from_header)
    return match.group(0) if match else ""


def _extract_text_body(payload: dict[str, Any]) -> str:
    """Walk the MIME tree and return the first text/plain part decoded
    from base64url, falling back to text/html (HTML tags stripped)."""
    plain: str | None = None
    html: str | None = None

    def walk(part: dict[str, Any]) -> None:
        nonlocal plain, html
        mime = part.get("mimeType") or ""
        data = ((part.get("body") or {}).get("data")) or ""
        if data:
            try:
                decoded = base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                decoded = ""
            if mime.startswith("text/plain") and plain is None:
                plain = decoded
            elif mime.startswith("text/html") and html is None:
                html = decoded
        for sub in part.get("parts") or []:
            if isinstance(sub, dict):
                walk(sub)

    walk(payload)
    if plain:
        return plain
    if html:
        return re.sub(r"<[^>]+>", "", html).strip()
    return ""

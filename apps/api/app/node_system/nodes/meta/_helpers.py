"""Shared lookup helpers for Meta action nodes.

Every action that hits the Graph API needs a *page* access token (the
non-expiring per-Page token derived from the user's long-lived OAuth
token, stored under `data.pages[].access_token`). This module centralizes
the lookup so each node body stays focused on its API call.
"""

from __future__ import annotations

from typing import Any


def find_credential(
    credentials: list[dict[str, Any]] | None,
    selected_id: str | None,
    type_name: str = "meta_oauth",
) -> dict[str, Any] | None:
    """Pick the user-selected credential by id, falling back to the first
    credential of the given type when no explicit selection is set."""
    creds = credentials or []
    if selected_id:
        match = next((c for c in creds if str(c.get("id")) == selected_id), None)
        if match is not None:
            return match
    return next((c for c in creds if c.get("type") == type_name), None)


def page_token_by_page_id(
    credential_data: dict[str, Any],
    page_id: str,
) -> str | None:
    """Return the non-expiring page access token for a given FB Page id, or
    None if the user no longer manages that Page through this credential."""
    pages = credential_data.get("pages")
    if not isinstance(pages, list):
        return None
    for page in pages:
        if not isinstance(page, dict):
            continue
        if str(page.get("id") or "") != page_id:
            continue
        token = page.get("access_token")
        if isinstance(token, str) and token:
            return token
    return None


def page_token_by_ig_account_id(
    credential_data: dict[str, Any],
    ig_account_id: str,
) -> str | None:
    """Return the page access token that owns the given IG business account.

    The OAuth callback enriches each page with
    `instagram_business_account.{id, username}` so this lookup avoids an
    extra Graph API hop on the hot path.
    """
    pages = credential_data.get("pages")
    if not isinstance(pages, list):
        return None
    for page in pages:
        if not isinstance(page, dict):
            continue
        ig = page.get("instagram_business_account") or {}
        if str(ig.get("id") or "") != ig_account_id:
            continue
        token = page.get("access_token")
        if isinstance(token, str) and token:
            return token
    return None

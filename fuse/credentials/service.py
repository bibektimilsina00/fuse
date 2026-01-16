import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fuse.utils.security import decrypt_string, encrypt_string

from .router import OAUTH_CONFIG, load_credentials_db, save_credentials_db

logger = logging.getLogger(__name__)


def get_credential_by_id(cred_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a credential by ID and return its data dictionary.
    DECRYPTS sensitive fields.
    """
    creds = load_credentials_db()
    for c in creds:
        if c.id == cred_id:
            data = c.data.copy()
            if "access_token" in data:
                data["access_token"] = decrypt_string(data["access_token"])
            if "bot_token" in data:
                data["bot_token"] = decrypt_string(data["bot_token"])
            if "refresh_token" in data:
                data["refresh_token"] = decrypt_string(data["refresh_token"])
            return data
    return None


def get_full_credential_by_id(cred_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a credential by ID and return its full dictionary including type and data.
    DECRYPTS sensitive fields.
    """
    creds = load_credentials_db()
    for c in creds:
        if c.id == cred_id:
            # Determine provider for ai_provider type
            if c.type == "ai_provider":
                provider = c.data.get("provider", "openrouter")
            else:
                provider = c.type

            data = c.data.copy()
            if "access_token" in data:
                data["access_token"] = decrypt_string(data["access_token"])
            if "bot_token" in data:
                data["bot_token"] = decrypt_string(data["bot_token"])
            if "refresh_token" in data:
                data["refresh_token"] = decrypt_string(data["refresh_token"])

            return {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "provider": provider,
                "data": data,
            }
    return None


async def get_active_credential(cred_id: str) -> Optional[Dict[str, Any]]:
    """
    Async wrapper that fetches a credential AND refreshes it if expired.
    Use this in Nodes.
    """
    cred = get_full_credential_by_id(cred_id)
    if not cred:
        return None

    data = cred["data"]

    # Check expiry
    expires_at = data.get("expires_at")
    refresh_token = data.get("refresh_token")

    # If expired and we have a refresh token, TRY to refresh
    if (
        expires_at
        and refresh_token
        and datetime.fromisoformat(expires_at) < datetime.now()
    ):
        logger.debug(f"Token for {cred['name']} expired at {expires_at}. Refreshing...")

        provider = cred["type"]  # e.g., google_sheets
        config = OAUTH_CONFIG.get(provider)

        if config:
            try:
                # 1. Determine which keys to use (User-provided VS Server-provided)
                # If the credential itself has client_id/secret (Manual Setup), use those.
                # Otherwise, fallback to the server config (.env).
                client_id = data.get("client_id") or config.get("client_id")
                client_secret = data.get("client_secret") or config.get("client_secret")

                if not client_id or not client_secret:
                    logger.error(
                        f"No Client ID/Secret found for refresh. (Provider: {provider})"
                    )
                    return cred

                # Refresh logic
                async with httpx.AsyncClient() as client:
                    payload = {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    }
                    resp = await client.post(config["token_url"], data=payload)

                    if resp.status_code == 200:
                        new_tokens = resp.json()

                        # Update DB
                        # We need to load fresh from DB to write safely
                        creds_db = load_credentials_db()
                        for c in creds_db:
                            if c.id == cred_id:
                                # Update fields
                                c.data["access_token"] = encrypt_string(
                                    new_tokens["access_token"]
                                )
                                # Some providers rotate refresh tokens
                                if "refresh_token" in new_tokens:
                                    c.data["refresh_token"] = encrypt_string(
                                        new_tokens["refresh_token"]
                                    )

                                if "expires_in" in new_tokens:
                                    from datetime import timedelta

                                    c.data["expires_at"] = (
                                        datetime.now()
                                        + timedelta(seconds=new_tokens["expires_in"])
                                    ).isoformat()

                                save_credentials_db(creds_db)

                                # Update our local return data (decrypted)
                                data["access_token"] = new_tokens["access_token"]
                                if "refresh_token" in new_tokens:
                                    data["refresh_token"] = new_tokens["refresh_token"]

                                logger.debug(
                                    f"Token refreshed successfully for {cred['name']}"
                                )
                                break
                    else:
                        logger.error(f"Failed to refresh token: {resp.text}")
            except Exception as e:
                logger.error(f"Refresh exception: {e}")

    return cred


def resolve_secret(value: str) -> str:
    """
    Helper to handle cases where value might be a simple string OR a credential ID.
    Now decrypts if it finds a credential.
    """
    if not value or not isinstance(value, str):
        return value

    data = get_credential_by_id(value)
    if data:
        if "value" in data:
            return data["value"]
        if "token" in data:
            return data["token"]
        if "bot_token" in data:
            return data["bot_token"]
        if "access_token" in data:
            return data["access_token"]
        if "url" in data:
            return data["url"]
        return str(data)

    return value

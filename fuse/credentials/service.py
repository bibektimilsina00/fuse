"""
Credential service functions for resolving and refreshing credentials.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import uuid

import httpx
from sqlmodel import Session, select

from fuse.database import engine
from fuse.utils.security import decrypt_string, encrypt_string
from fuse.credentials.models import Credential

logger = logging.getLogger(__name__)

# OAuth configuration - duplicated here to avoid circular imports
OAUTH_CONFIG = {
    "google_sheets": {
        "token_url": "https://oauth2.googleapis.com/token",
    },
    "google_ai": {
        "token_url": "https://oauth2.googleapis.com/token",
    },
    "slack": {
        "token_url": "https://slack.com/api/oauth.v2.access",
    },
    "discord": {
        "token_url": "https://discord.com/api/oauth2/token",
    }
}


def decrypt_credential_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive fields in credential data."""
    result = data.copy()
    sensitive_fields = ['access_token', 'refresh_token', 'api_key', 'token', 'secret', 'password', 'webhook_url', 'bot_token', 'copilot_token']
    
    for field in sensitive_fields:
        if field in result and result[field]:
            try:
                result[field] = decrypt_string(result[field])
            except Exception:
                pass  # If decryption fails, keep original value
    
    return result


def get_credential_by_id(cred_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a credential by ID and return its data dictionary.
    DECRYPTS sensitive fields.
    """
    try:
        cred_uuid = uuid.UUID(cred_id)
    except ValueError:
        return None
    
    with Session(engine) as session:
        credential = session.get(Credential, cred_uuid)
        if credential:
            return decrypt_credential_data(credential.data)
    
    return None


def get_full_credential_by_id(cred_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a credential by ID and return its full dictionary including type and data.
    DECRYPTS sensitive fields.
    """
    try:
        cred_uuid = uuid.UUID(cred_id)
    except ValueError:
        return None
    
    with Session(engine) as session:
        credential = session.get(Credential, cred_uuid)
        if credential:
            # Determine provider for ai_provider type
            if credential.type == "ai_provider":
                provider = credential.data.get("provider", "openrouter")
            else:
                provider = credential.type

            return {
                "id": str(credential.id),
                "name": credential.name,
                "type": credential.type,
                "provider": provider,
                "data": decrypt_credential_data(credential.data),
            }
    
    return None


def _parse_expiry(val: Any) -> Optional[datetime]:
    """Helper to parse expiry timestamps safely from int, float, or string."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val)
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            try:
                # Try parsing as timestamp string
                return datetime.fromtimestamp(float(val))
            except ValueError:
                pass
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
    provider = cred["type"]

    # Special handling for GitHub Copilot Refresh
    if provider == "github_copilot":
        copilot_expires = _parse_expiry(data.get("copilot_expires_at"))
        if copilot_expires and copilot_expires < datetime.now():
             logger.debug(f"Copilot token expired. Refreshing using device flow access token...")
             access_token = data.get("access_token")
             if not access_token:
                 return cred # Can't refresh
             
             try:
                 async with httpx.AsyncClient() as client:
                    copilot_resp = await client.get(
                        "https://api.github.com/copilot_internal/v2/token",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Editor-Version": "vscode/1.85.0",
                            "User-Agent": "GitHubCopilot/1.138.0"
                        }
                    )
                    
                    if copilot_resp.status_code == 200:
                        copilot_data = copilot_resp.json()
                        new_token = copilot_data.get("token")
                        new_expiry = copilot_data.get("expires_at")
                        
                        # Update DB
                        try:
                            cred_uuid = uuid.UUID(cred_id)
                            with Session(engine) as session:
                                credential = session.get(Credential, cred_uuid)
                                if credential:
                                    credential.data["copilot_token"] = encrypt_string(new_token)
                                    credential.data["copilot_expires_at"] = new_expiry
                                    credential.updated_at = datetime.utcnow()
                                    session.add(credential)
                                    session.commit()
                                    
                                    # Update local return
                                    data["copilot_token"] = new_token
                                    data["copilot_expires_at"] = new_expiry
                        except Exception as e:
                            logger.error(f"Failed to save refreshed Copilot token: {e}")
             except Exception as e:
                 logger.error(f"Failed to refresh Copilot token: {e}")
        
        return cred


    # Standard OAuth Refresh
    expires_at = data.get("expires_at")
    expiry_dt = _parse_expiry(expires_at)
    refresh_token = data.get("refresh_token")

    # If expired and we have a refresh token, TRY to refresh
    if (
        expiry_dt
        and refresh_token
        and expiry_dt < datetime.now()
    ):
        logger.debug(f"Token for {cred['name']} expired at {expiry_dt}. Refreshing...")

        config = OAUTH_CONFIG.get(provider)

        if config:
            try:
                # Get client credentials from settings
                from fuse.config import settings
                
                client_id = None
                client_secret = None
                
                if provider in ["google_sheets", "google_ai"]:
                    client_id = settings.GOOGLE_CLIENT_ID
                    client_secret = settings.GOOGLE_CLIENT_SECRET
                elif provider == "slack":
                    client_id = settings.SLACK_CLIENT_ID
                    client_secret = settings.SLACK_CLIENT_SECRET
                elif provider == "discord":
                    client_id = settings.DISCORD_CLIENT_ID
                    client_secret = settings.DISCORD_CLIENT_SECRET

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
                        try:
                            cred_uuid = uuid.UUID(cred_id)
                        except ValueError:
                            return cred
                            
                        with Session(engine) as session:
                            credential = session.get(Credential, cred_uuid)
                            if credential:
                                # Update fields
                                credential.data["access_token"] = encrypt_string(
                                    new_tokens["access_token"]
                                )
                                # Some providers rotate refresh tokens
                                if "refresh_token" in new_tokens:
                                    credential.data["refresh_token"] = encrypt_string(
                                        new_tokens["refresh_token"]
                                    )

                                if "expires_in" in new_tokens:
                                    credential.data["expires_at"] = (
                                        datetime.now()
                                        + timedelta(seconds=new_tokens["expires_in"])
                                    ).isoformat()

                                credential.updated_at = datetime.utcnow()
                                session.add(credential)
                                session.commit()

                                # Update our local return data (decrypted)
                                data["access_token"] = new_tokens["access_token"]
                                if "refresh_token" in new_tokens:
                                    data["refresh_token"] = new_tokens["refresh_token"]

                                logger.debug(
                                    f"Token refreshed successfully for {cred['name']}"
                                )
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

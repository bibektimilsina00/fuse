from typing import List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os
import uuid
from datetime import datetime, timedelta
from src.utils.security import encrypt_string

router = APIRouter()

CREDENTIALS_FILE = "credentials_storage.json"

class Credential(BaseModel):
    id: str
    name: str
    type: str  # e.g., 'google_sheets', 'slack', 'discord'
    data: dict # stores the actual secrets: { 'token': '...', 'webhook_url': '...' }
    created_at: str

class CredentialCreate(BaseModel):
    name: str
    type: str
    data: dict

def load_credentials_db() -> List[Credential]:
    if not os.path.exists(CREDENTIALS_FILE):
        return []
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            data = json.load(f)
            return [Credential(**d) for d in data]
    except:
        return []

def save_credentials_db(creds: List[Credential]):
    with open(CREDENTIALS_FILE, "w") as f:
        # Convert Pydantic models to dicts
        json.dump([c.dict() for c in creds], f, indent=2)

@router.get("/", response_model=List[Credential])
def get_credentials():
    """List all available credentials."""
    creds = load_credentials_db()
    # Mask sensitive data before returning list? 
    # For now, let's keep it simple. Usually we wouldn't return full secrets.
    # But for an internal automation tool, returning it (or just returning ID/Name) is ok.
    # Ideally, frontend only needs ID and Type/Name to display in dropdown.
    # Let's return everything but maybe we can be smarter later.
    return creds

@router.post("/", response_model=Credential)
def create_credential(cred_in: CredentialCreate):
    """Create a new credential."""
    creds = load_credentials_db()
    
    new_cred = Credential(
        id=str(uuid.uuid4()),
        name=cred_in.name,
        type=cred_in.type,
        data=cred_in.data,
        created_at=datetime.now().isoformat()
    )
    
    creds.append(new_cred)
    save_credentials_db(creds)
    return new_cred

@router.delete("/{cred_id}")
def delete_credential(cred_id: str):
    creds = load_credentials_db()
    creds = [c for c in creds if c.id != cred_id]
    save_credentials_db(creds)
    return {"success": True}

# --- OAuth Implementation ---

import httpx
from fastapi.responses import RedirectResponse
from src.config import settings

OAUTH_CONFIG = {
    "google_sheets": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.readonly",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
    },
    "slack": {
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "scopes": "chat:write,channels:read,commands,incoming-webhook",
        "client_id": settings.SLACK_CLIENT_ID,
        "client_secret": settings.SLACK_CLIENT_SECRET,
    },
    "discord": {
        "auth_url": "https://discord.com/api/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "scopes": "identify connections workflows.webhook.incoming",
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
    }
}

@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(provider: str):
    config = OAUTH_CONFIG.get(provider)
    if not config:
        raise HTTPException(status_code=400, detail=f"OAuth not supported for {provider}")
    
    if not config.get("client_id") or not config.get("client_secret"):
        # Map provider to actual env var names for helpful error message
        ENV_VARS = {
            "google_sheets": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
            "slack": ("SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"),
            "discord": ("DISCORD_CLIENT_ID", "DISCORD_CLIENT_SECRET"),
        }
        id_var, secret_var = ENV_VARS.get(provider, (f"{provider.upper()}_CLIENT_ID", f"{provider.upper()}_CLIENT_SECRET"))
        
        error_msg = (
            f"OAuth for {provider} is not configured on the server. "
            f"Please set {id_var} and {secret_var} in your backend .env file."
        )
        raise HTTPException(status_code=400, detail=error_msg)

    redirect_uri = f"{settings.server_host}/api/v1/credentials/oauth/{provider}/callback"
    
    params = {
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config["scopes"],
        "access_type": "offline",
        "prompt": "consent",
    }
    
    from urllib.parse import urlencode
    auth_url = config["auth_url"]
    query_string = urlencode(params)
    return RedirectResponse(url=f"{auth_url}?{query_string}")

@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str):
    config = OAUTH_CONFIG.get(provider)
    if not config:
        raise HTTPException(status_code=400, detail="Invalid provider")

    redirect_uri = f"{settings.server_host}/api/v1/credentials/oauth/{provider}/callback"
    
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        
        headers = {"Accept": "application/json"}
        
        response = await client.post(config["token_url"], data=data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to exchange code: {response.text}")
        
        token_data = response.json()
        
        # --- ENCRYPTION STEP ---
        # Encrypt sensitive fields before saving
        if "access_token" in token_data:
            token_data["access_token"] = encrypt_string(token_data["access_token"])
        if "refresh_token" in token_data:
            token_data["refresh_token"] = encrypt_string(token_data["refresh_token"])
        
        # Calculate expiry if present (Google gives expires_in)
        if "expires_in" in token_data:
             token_data["expires_at"] = (datetime.now() + timedelta(seconds=token_data["expires_in"])).isoformat()

        # Save as a credential
        creds = load_credentials_db()
        
        # Try to get a useful name
        name = f"{provider.replace('_', ' ').title()} OAuth"
        if provider == "slack":
            name = token_data.get("team", {}).get("name", name)
        
        new_cred = Credential(
            id=str(uuid.uuid4()),
            name=name,
            type=provider,
            data=token_data, # Encrypted data
            created_at=datetime.now().isoformat()
        )
        
        creds.append(new_cred)
        save_credentials_db(creds)
        
        # Redirect back to frontend
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback?status=success&id={new_cred.id}&name={name}")

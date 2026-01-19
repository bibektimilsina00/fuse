"""
Credentials API router with database storage.
"""
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select
import httpx
import logging

logger = logging.getLogger(__name__)

from fuse.auth.dependencies import get_db, get_current_user
from fuse.auth.models import User
from fuse.credentials.models import Credential
from fuse.utils.security import encrypt_string, decrypt_string
from fuse.config import settings

router = APIRouter()


# =============================================================================
# Pydantic Schemas
# =============================================================================

class CredentialResponse(BaseModel):
    """Public credential response (masks sensitive data)"""
    id: str
    name: str
    type: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    last_used_at: Optional[str] = None


class CredentialCreate(BaseModel):
    """Request body for creating a credential"""
    name: str
    type: str
    data: dict
    description: Optional[str] = None


class CredentialUpdate(BaseModel):
    """Request body for updating a credential"""
    name: Optional[str] = None
    data: Optional[dict] = None
    description: Optional[str] = None


class CredentialDetail(BaseModel):
    """Full credential response (includes data for internal use)"""
    id: str
    name: str
    type: str
    data: dict
    created_at: str
    updated_at: str
    description: Optional[str] = None
    last_used_at: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def credential_to_response(cred: Credential) -> CredentialResponse:
    """Convert database model to response schema (without sensitive data)"""
    return CredentialResponse(
        id=str(cred.id),
        name=cred.name,
        type=cred.type,
        created_at=cred.created_at.isoformat(),
        updated_at=cred.updated_at.isoformat(),
        description=cred.description,
        last_used_at=cred.last_used_at.isoformat() if cred.last_used_at else None
    )


def credential_to_detail(cred: Credential) -> CredentialDetail:
    """Convert database model to detail schema (with decrypted data)"""
    # Decrypt sensitive fields
    decrypted_data = {}
    for key, value in cred.data.items():
        if key in ['access_token', 'refresh_token', 'api_key', 'token', 'secret', 'password', 'webhook_url']:
            try:
                decrypted_data[key] = decrypt_string(value) if value else value
            except:
                decrypted_data[key] = value  # If decryption fails, use as-is
        else:
            decrypted_data[key] = value
    
    return CredentialDetail(
        id=str(cred.id),
        name=cred.name,
        type=cred.type,
        data=decrypted_data,
        created_at=cred.created_at.isoformat(),
        updated_at=cred.updated_at.isoformat(),
        description=cred.description,
        last_used_at=cred.last_used_at.isoformat() if cred.last_used_at else None
    )


def encrypt_credential_data(data: dict) -> dict:
    """Encrypt sensitive fields in credential data"""
    encrypted = {}
    sensitive_fields = ['access_token', 'refresh_token', 'api_key', 'token', 'secret', 'password', 'webhook_url']
    
    for key, value in data.items():
        if key in sensitive_fields and value:
            encrypted[key] = encrypt_string(str(value))
        else:
            encrypted[key] = value
    
    return encrypted


# =============================================================================
# CRUD Endpoints
# =============================================================================

@router.get("/", response_model=List[CredentialResponse])
def list_credentials(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all credentials for the current user."""
    statement = select(Credential).where(Credential.owner_id == current_user.id)
    credentials = session.exec(statement).all()
    return [credential_to_response(c) for c in credentials]


@router.get("/{cred_id}", response_model=CredentialDetail)
def get_credential(
    cred_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific credential with decrypted data."""
    try:
        cred_uuid = uuid.UUID(cred_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid credential ID")
    
    statement = select(Credential).where(
        Credential.id == cred_uuid,
        Credential.owner_id == current_user.id
    )
    credential = session.exec(statement).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    return credential_to_detail(credential)


@router.post("/", response_model=CredentialResponse)
def create_credential(
    cred_in: CredentialCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new credential."""
    encrypted_data = encrypt_credential_data(cred_in.data)
    
    credential = Credential(
        name=cred_in.name,
        type=cred_in.type,
        data=encrypted_data,
        owner_id=current_user.id,
        description=cred_in.description
    )
    
    session.add(credential)
    session.commit()
    session.refresh(credential)
    
    return credential_to_response(credential)


@router.patch("/{cred_id}", response_model=CredentialResponse)
def update_credential(
    cred_id: str,
    cred_in: CredentialUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing credential."""
    try:
        cred_uuid = uuid.UUID(cred_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid credential ID")
    
    statement = select(Credential).where(
        Credential.id == cred_uuid,
        Credential.owner_id == current_user.id
    )
    credential = session.exec(statement).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    if cred_in.name is not None:
        credential.name = cred_in.name
    
    if cred_in.data is not None:
        credential.data = encrypt_credential_data(cred_in.data)
    
    if cred_in.description is not None:
        credential.description = cred_in.description
    
    credential.updated_at = datetime.utcnow()
    
    session.add(credential)
    session.commit()
    session.refresh(credential)
    
    return credential_to_response(credential)


@router.delete("/{cred_id}")
def delete_credential(
    cred_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a credential."""
    try:
        cred_uuid = uuid.UUID(cred_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid credential ID")
    
    statement = select(Credential).where(
        Credential.id == cred_uuid,
        Credential.owner_id == current_user.id
    )
    credential = session.exec(statement).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    session.delete(credential)
    session.commit()
    
    return {"success": True, "message": "Credential deleted"}


# =============================================================================
# OAuth Implementation
# =============================================================================
import json
import base64
from urllib.parse import urlencode

OAUTH_CONFIG = {
    "google_sheets": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.readonly",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
    },
    "google_ai": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
        "client_id": "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com",
        "client_secret": "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",
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
        "scopes": "identify connections webhooks.incoming",
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
    }
}


@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Initiate OAuth flow for a provider."""
    config = OAUTH_CONFIG.get(provider)
    if not config:
        raise HTTPException(status_code=400, detail=f"OAuth not supported for {provider}")
    
    if not config.get("client_id") or not config.get("client_secret"):
        ENV_VARS = {
            "google_sheets": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
            "google_ai": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
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
    
    # Encode state with user_id
    state_data = {"user_id": str(current_user.id)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    params = {
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config["scopes"],
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    
    query_string = urlencode(params)
    # Return JSON with URL so frontend can redirect (preserving auth headers during the API call)
    return {"url": f"{config['auth_url']}?{query_string}"}


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: Optional[str] = None,
    session: Session = Depends(get_db)
):
    """Handle OAuth callback and save credential."""
    config = OAUTH_CONFIG.get(provider)
    if not config:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    # Retrieve user from state
    user_id = None
    if state:
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            user_id = state_data.get("user_id")
        except Exception:
            pass # Handle gracefully or error out
            
    if not user_id:
        # Fallback for legacy flows or direct visits?
        # In strictly secured app, we should fail.
        # But given we just removed superuser, we need a fallback if state is missing?
        # No, state is required now.
        raise HTTPException(status_code=400, detail="Invalid state parameter. Login flow interrupted.")

    # Verify user exists
    user = session.get(User, uuid.UUID(user_id))
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

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
        
        # Encrypt sensitive fields
        encrypted_data = encrypt_credential_data(token_data)
        
        # Calculate expiry if present
        if "expires_in" in token_data:
            encrypted_data["expires_at"] = (datetime.now() + timedelta(seconds=token_data["expires_in"])).isoformat()

        # Get name for the credential
        name = f"{provider.replace('_', ' ').title()} OAuth"
        if provider == "slack":
            name = token_data.get("team", {}).get("name", name)
        
        credential = Credential(
            name=name,
            type=provider,
            data=encrypted_data,
            owner_id=user.id
        )
        
        session.add(credential)
        session.commit()
        session.refresh(credential)
        
        # Redirect back to frontend
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/callback?status=success&id={credential.id}&name={name}"
        )


# =============================================================================
# GitHub Copilot (Device Flow)
# =============================================================================

GITHUB_COPILOT_CLIENT_ID = "01ab8ac9400c4e429b23" # VS Code Client ID

@router.post("/oauth/github-copilot/device/code")
async def github_copilot_device_code(current_user: User = Depends(get_current_user)):
    """Start GitHub Copilot Device Flow"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/device/code",
            json={"client_id": GITHUB_COPILOT_CLIENT_ID, "scope": "read:user"},
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to initiate device flow")
            
        return response.json()

@router.post("/oauth/github-copilot/device/poll")
async def github_copilot_poll(
    device_code: str, 
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Poll for GitHub Copilot Token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_COPILOT_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            },
            headers={"Accept": "application/json"}
        )
        
        data = response.json()
        logger.info(f"GitHub Device Poll Response: {data}")
        
        if "error" in data:
            error = data.get("error")
            if error == "authorization_pending":
                return {"status": "pending"}
            elif error == "slow_down":
                return {"status": "pending", "interval": data.get("interval", 5)}
            elif error == "expired_token":
                raise HTTPException(status_code=400, detail="Device code expired")
            else:
                 raise HTTPException(status_code=400, detail=f"GitHub Error: {error}")
                 
        # Success!
        # Now we need to get the "Copilot Token" using this OAuth token?
        # Actually, standard Copilot flow:
        # 1. OAuth Token (from device flow)
        # 2. Get Copilot Token (GET https://api.github.com/copilot_internal/v2/token) using OAuth token
        
        oauth_token = data.get("access_token")
        
        # Verify copilot access and get internal token
        copilot_resp = await client.get(
            "https://api.github.com/copilot_internal/v2/token",
            headers={
                "Authorization": f"token {oauth_token}",
                "Editor-Version": "vscode/1.85.0",
                "User-Agent": "GitHubCopilot/1.138.0"
            }
        )
        
        if copilot_resp.status_code != 200:
             raise HTTPException(status_code=403, detail="Failed to retrieve Copilot token. Access denied or no subscription.")

        copilot_data = copilot_resp.json()
        
        # Save Credential
        encrypted_data = encrypt_credential_data({
            "access_token": oauth_token, # The GitHub OAuth token
            "copilot_token": copilot_data.get("token"), # The actual model access token
            "copilot_expires_at": copilot_data.get("expires_at"),
            "token_type": "github_copilot"
        })
        
        credential = Credential(
            name="GitHub Copilot",
            type="github_copilot",
            data=encrypted_data,
            owner_id=current_user.id
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        
        return {"status": "success", "credential": credential_to_response(credential)}

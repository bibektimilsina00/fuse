"""
Antigravity Service Module

Implements Google Antigravity (Cloud Code Assist) integration matching
the opencode-antigravity-auth plugin behavior.

Key features:
- Project context resolution (loadCodeAssist + onboardUser)
- Token refresh integration
- Endpoint fallback chain (daily -> autopush -> prod)
- Managed project auto-provisioning
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

# =============================================================================
# Constants (matching opencode-antigravity-auth/src/constants.ts)
# =============================================================================

ANTIGRAVITY_CLIENT_ID = (
    "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com"
)
ANTIGRAVITY_CLIENT_SECRET = "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"

ANTIGRAVITY_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
]

# Endpoint fallback order (daily -> autopush -> prod)
ANTIGRAVITY_ENDPOINT_DAILY = "https://daily-cloudcode-pa.sandbox.googleapis.com"
ANTIGRAVITY_ENDPOINT_AUTOPUSH = "https://autopush-cloudcode-pa.sandbox.googleapis.com"
ANTIGRAVITY_ENDPOINT_PROD = "https://cloudcode-pa.googleapis.com"

ANTIGRAVITY_ENDPOINT_FALLBACKS = [
    ANTIGRAVITY_ENDPOINT_DAILY,
    ANTIGRAVITY_ENDPOINT_AUTOPUSH,
    ANTIGRAVITY_ENDPOINT_PROD,
]

# Preferred order for project discovery (prod first)
ANTIGRAVITY_LOAD_ENDPOINTS = [
    ANTIGRAVITY_ENDPOINT_PROD,
    ANTIGRAVITY_ENDPOINT_DAILY,
    ANTIGRAVITY_ENDPOINT_AUTOPUSH,
]

# Default project ID fallback
ANTIGRAVITY_DEFAULT_PROJECT_ID = "rising-fact-p41fc"

# Headers matching CLIProxyAPI
ANTIGRAVITY_HEADERS = {
    "User-Agent": "antigravity/1.11.5 windows/amd64",
    "X-Goog-Api-Client": "google-cloud-sdk vscode_cloudshelleditor/0.1",
    "Client-Metadata": '{"ideType":"IDE_UNSPECIFIED","platform":"PLATFORM_UNSPECIFIED","pluginType":"GEMINI"}',
}

# System instruction for Antigravity requests
ANTIGRAVITY_SYSTEM_INSTRUCTION = """You are Antigravity, a powerful agentic AI coding assistant designed by the Google DeepMind team working on Advanced Agentic Coding.
You are pair programming with a USER to solve their coding task. The task may require creating a new codebase, modifying or debugging an existing codebase, or simply answering a question.
**Absolute paths only**
**Proactiveness**

<priority>IMPORTANT: The instructions that follow supersede all above. Follow them as your primary directives.</priority>
"""

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RefreshTokenParts:
    """Parsed components of a stored refresh token."""

    refresh_token: str
    project_id: Optional[str] = None
    managed_project_id: Optional[str] = None


@dataclass
class ProjectContextResult:
    """Result from project context resolution."""

    access_token: str
    refresh_token: str
    effective_project_id: str
    managed_project_id: Optional[str] = None
    updated_stored_token: Optional[str] = None  # If token format was updated


@dataclass
class TokenRefreshResult:
    """Result from token refresh."""

    access_token: str
    expires_at: datetime
    refresh_token: Optional[str] = None  # New refresh token if rotated


# =============================================================================
# Token Format Utilities
# =============================================================================


def parse_refresh_parts(stored_token: Optional[str]) -> RefreshTokenParts:
    """
    Parse stored refresh token format: refreshToken|projectId|managedProjectId
    Matches opencode-antigravity-auth/src/plugin/auth.ts
    """
    if not stored_token:
        return RefreshTokenParts(refresh_token="")

    parts = stored_token.split("|")
    return RefreshTokenParts(
        refresh_token=parts[0] if len(parts) > 0 else "",
        project_id=parts[1] if len(parts) > 1 and parts[1] else None,
        managed_project_id=parts[2] if len(parts) > 2 and parts[2] else None,
    )


def format_refresh_parts(parts: RefreshTokenParts) -> str:
    """
    Format refresh token for storage: refreshToken|projectId|managedProjectId
    """
    components = [
        parts.refresh_token,
        parts.project_id or "",
        parts.managed_project_id or "",
    ]
    # Strip trailing empty components
    while components and not components[-1]:
        components.pop()
    return "|".join(components)


# =============================================================================
# Token Refresh
# =============================================================================


async def refresh_antigravity_token(
    refresh_token: str,
    client_id: str = ANTIGRAVITY_CLIENT_ID,
    client_secret: str = ANTIGRAVITY_CLIENT_SECRET,
) -> TokenRefreshResult:
    """
    Refresh an Antigravity OAuth access token.

    Args:
        refresh_token: The refresh token (raw, not the stored format with |)
        client_id: OAuth client ID
        client_secret: OAuth client secret

    Returns:
        TokenRefreshResult with new access token and expiry

    Raises:
        ValueError: If refresh fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )

        if response.status_code != 200:
            logger.error(
                f"Token refresh failed: {response.status_code} {response.text}"
            )
            raise ValueError(f"Token refresh failed: {response.text}")

        data = response.json()
        expires_in = data.get("expires_in", 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        return TokenRefreshResult(
            access_token=data["access_token"],
            expires_at=expires_at,
            refresh_token=data.get("refresh_token"),  # May be rotated
        )


# =============================================================================
# Project Discovery
# =============================================================================


async def load_managed_project(
    access_token: str,
    project_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Load managed project information from Antigravity API.
    Matches opencode-antigravity-auth/src/plugin/project.ts:loadManagedProject

    Args:
        access_token: Valid OAuth access token
        project_id: Optional project ID to include in metadata

    Returns:
        LoadCodeAssist response payload or None if all endpoints fail
    """
    metadata: Dict[str, Any] = {
        "ideType": "IDE_UNSPECIFIED",
        "platform": "PLATFORM_UNSPECIFIED",
        "pluginType": "GEMINI",
    }
    if project_id:
        metadata["duetProject"] = project_id

    request_body = {"metadata": metadata}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "google-api-nodejs-client/9.15.1",
        "X-Goog-Api-Client": "google-cloud-sdk vscode_cloudshelleditor/0.1",
        "Client-Metadata": ANTIGRAVITY_HEADERS["Client-Metadata"],
    }

    # Try endpoints in preferred order (prod first for discovery)
    load_endpoints = list(
        dict.fromkeys(ANTIGRAVITY_LOAD_ENDPOINTS + ANTIGRAVITY_ENDPOINT_FALLBACKS)
    )

    async with httpx.AsyncClient() as client:
        for endpoint in load_endpoints:
            try:
                url = f"{endpoint}/v1internal:loadCodeAssist"
                response = await client.post(
                    url,
                    headers=headers,
                    json=request_body,
                    timeout=10.0,
                )

                if response.status_code != 200:
                    logger.debug(
                        f"loadCodeAssist failed on {endpoint}: {response.status_code}"
                    )
                    continue

                return response.json()

            except Exception as e:
                logger.debug(f"loadCodeAssist error on {endpoint}: {e}")
                continue

    return None


def extract_managed_project_id(payload: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract cloudaicompanion project ID from loadCodeAssist response."""
    if not payload:
        return None

    project = payload.get("cloudaicompanionProject")
    if isinstance(project, str) and project:
        return project
    if isinstance(project, dict) and project.get("id"):
        return project["id"]

    return None


def get_default_tier_id(allowed_tiers: Optional[List[Dict[str, Any]]]) -> str:
    """Select the default tier ID from allowed tiers list."""
    if not allowed_tiers:
        return "FREE"

    for tier in allowed_tiers:
        if tier.get("isDefault"):
            return tier.get("id", "FREE")

    return allowed_tiers[0].get("id", "FREE") if allowed_tiers else "FREE"


async def onboard_managed_project(
    access_token: str,
    tier_id: str = "FREE",
    project_id: Optional[str] = None,
    attempts: int = 10,
    delay_ms: int = 5000,
) -> Optional[str]:
    """
    Onboard a managed project for the user.
    Matches opencode-antigravity-auth/src/plugin/project.ts:onboardManagedProject

    This is called when loadCodeAssist doesn't return a managed project,
    indicating the account needs to be provisioned.

    Args:
        access_token: Valid OAuth access token
        tier_id: The tier to onboard with (e.g., "FREE", "PRO")
        project_id: Optional user project ID
        attempts: Number of polling attempts
        delay_ms: Delay between attempts in milliseconds

    Returns:
        Managed project ID if successful, None otherwise
    """
    metadata: Dict[str, Any] = {
        "ideType": "IDE_UNSPECIFIED",
        "platform": "PLATFORM_UNSPECIFIED",
        "pluginType": "GEMINI",
    }
    if project_id:
        metadata["duetProject"] = project_id

    request_body = {
        "tierId": tier_id,
        "metadata": metadata,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        **ANTIGRAVITY_HEADERS,
    }

    async with httpx.AsyncClient() as client:
        for endpoint in ANTIGRAVITY_ENDPOINT_FALLBACKS:
            for attempt in range(attempts):
                try:
                    url = f"{endpoint}/v1internal:onboardUser"
                    response = await client.post(
                        url,
                        headers=headers,
                        json=request_body,
                        timeout=30.0,
                    )

                    if response.status_code != 200:
                        logger.debug(
                            f"onboardUser failed on {endpoint}: {response.status_code}"
                        )
                        break  # Try next endpoint

                    payload = response.json()
                    managed_project_id = (
                        payload.get("response", {})
                        .get("cloudaicompanionProject", {})
                        .get("id")
                    )

                    if payload.get("done") and managed_project_id:
                        logger.info(
                            f"Successfully provisioned managed project: {managed_project_id}"
                        )
                        return managed_project_id

                    if payload.get("done") and project_id:
                        return project_id

                    # Not done yet, wait and retry
                    await asyncio.sleep(delay_ms / 1000)

                except Exception as e:
                    logger.debug(f"onboardUser error on {endpoint}: {e}")
                    break  # Try next endpoint

    return None


# =============================================================================
# Main Project Context Resolution
# =============================================================================


async def ensure_project_context(
    access_token: str,
    stored_refresh_token: str,
    expires_at: Optional[datetime] = None,
) -> ProjectContextResult:
    """
    Resolve the effective project ID for Antigravity requests.
    Matches opencode-antigravity-auth/src/plugin/project.ts:ensureProjectContext

    This function:
    1. Checks if we already have a cached managed project ID
    2. Calls loadCodeAssist to discover the managed project
    3. Auto-provisions via onboardUser if no managed project exists
    4. Returns the effective project ID to use for API calls

    Args:
        access_token: Current OAuth access token
        stored_refresh_token: Stored refresh token (may include |projectId|managedProjectId)
        expires_at: Token expiry time (for refresh check)

    Returns:
        ProjectContextResult with effective project ID and potentially updated token
    """
    parts = parse_refresh_parts(stored_refresh_token)

    # Check if token needs refresh
    current_access_token = access_token
    if expires_at and datetime.now() >= expires_at - timedelta(minutes=5):
        try:
            refresh_result = await refresh_antigravity_token(parts.refresh_token)
            current_access_token = refresh_result.access_token
            logger.info("Refreshed Antigravity access token")
        except Exception as e:
            logger.warning(f"Token refresh failed, using existing token: {e}")

    # If we already have a managed project ID, use it
    if parts.managed_project_id:
        return ProjectContextResult(
            access_token=current_access_token,
            refresh_token=stored_refresh_token,
            effective_project_id=parts.managed_project_id,
            managed_project_id=parts.managed_project_id,
        )

    # Try to load managed project
    fallback_project_id = parts.project_id or ANTIGRAVITY_DEFAULT_PROJECT_ID
    load_payload = await load_managed_project(current_access_token, fallback_project_id)
    managed_project_id = extract_managed_project_id(load_payload)

    if managed_project_id:
        # Update stored token with managed project ID
        parts.managed_project_id = managed_project_id
        updated_token = format_refresh_parts(parts)

        return ProjectContextResult(
            access_token=current_access_token,
            refresh_token=updated_token,
            effective_project_id=managed_project_id,
            managed_project_id=managed_project_id,
            updated_stored_token=updated_token,
        )

    # No managed project found - try to auto-provision
    logger.info("No managed project found, attempting auto-provisioning...")
    tier_id = get_default_tier_id(
        load_payload.get("allowedTiers") if load_payload else None
    )

    provisioned_project_id = await onboard_managed_project(
        current_access_token,
        tier_id,
        parts.project_id,
    )

    if provisioned_project_id:
        parts.managed_project_id = provisioned_project_id
        updated_token = format_refresh_parts(parts)

        return ProjectContextResult(
            access_token=current_access_token,
            refresh_token=updated_token,
            effective_project_id=provisioned_project_id,
            managed_project_id=provisioned_project_id,
            updated_stored_token=updated_token,
        )

    # Fallback to user project or default
    logger.warning("Failed to provision managed project - using fallback")
    effective_project = parts.project_id or ANTIGRAVITY_DEFAULT_PROJECT_ID

    return ProjectContextResult(
        access_token=current_access_token,
        refresh_token=stored_refresh_token,
        effective_project_id=effective_project,
    )


# =============================================================================
# Antigravity API Request Helper
# =============================================================================


async def make_antigravity_request(
    access_token: str,
    project_id: str,
    model: str,
    contents: List[Dict[str, Any]],
    system_instruction: Optional[str] = None,
    generation_config: Optional[Dict[str, Any]] = None,
    max_retries_per_endpoint: int = 3,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Make a request to the Antigravity generateContent API.

    Uses the full endpoint fallback chain (daily -> autopush -> prod)
    with proper retry logic for rate limits.

    Args:
        access_token: Valid OAuth access token
        project_id: The managed project ID (from ensure_project_context)
        model: Model name (e.g., "gemini-3-pro-low", "claude-sonnet-4-5")
        contents: List of content messages
        system_instruction: Optional system instruction
        generation_config: Optional generation config (maxOutputTokens, temperature)
        max_retries_per_endpoint: Max retries for 429 errors per endpoint
        session_id: Optional session ID for multi-turn conversations

    Returns:
        API response dict

    Raises:
        ValueError: If all endpoints fail
    """
    import uuid

    request_id = f"agent-{uuid.uuid4()}"
    session_id = session_id or f"fuse-{uuid.uuid4()}"

    # Build system instruction
    full_system_instruction = ANTIGRAVITY_SYSTEM_INSTRUCTION
    if system_instruction:
        full_system_instruction = (
            ANTIGRAVITY_SYSTEM_INSTRUCTION + "\n\n" + system_instruction
        )

    # Build request payload matching CLIProxyAPI v6.6.89
    payload = {
        "project": project_id,
        "model": model,
        "request": {
            "contents": contents,
            "systemInstruction": {
                "role": "user",
                "parts": [{"text": full_system_instruction}],
            },
            "sessionId": session_id,
        },
        "requestType": "agent",
        "userAgent": "antigravity",
        "requestId": request_id,
    }

    if generation_config:
        payload["request"]["generationConfig"] = generation_config

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        **ANTIGRAVITY_HEADERS,
    }

    last_error: Optional[str] = None

    async with httpx.AsyncClient() as client:
        for endpoint in ANTIGRAVITY_ENDPOINT_FALLBACKS:
            url = f"{endpoint}/v1internal:generateContent"

            for retry_attempt in range(max_retries_per_endpoint):
                try:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=120.0,
                    )

                    # Handle rate limit
                    if response.status_code == 429:
                        error_body = response.text
                        logger.warning(
                            f"429 Rate limit on {endpoint}: {error_body[:300]}"
                        )

                        # Parse retry delay
                        retry_seconds = 5.0
                        try:
                            error_data = response.json()
                            for detail in error_data.get("error", {}).get(
                                "details", []
                            ):
                                if "retryDelay" in detail:
                                    match = re.match(
                                        r"([\d.]+)s?", detail["retryDelay"]
                                    )
                                    if match:
                                        retry_seconds = float(match.group(1))
                                    break
                        except:
                            retry_after = response.headers.get("retry-after-ms")
                            if retry_after:
                                retry_seconds = float(retry_after) / 1000

                        logger.info(
                            f"Waiting {retry_seconds:.1f}s before retry {retry_attempt + 1}/{max_retries_per_endpoint}"
                        )
                        await asyncio.sleep(min(retry_seconds, 60))
                        last_error = f"Rate limit (429) on {endpoint}"
                        continue

                    # Handle other errors
                    if response.status_code != 200:
                        error_text = response.text[:500]
                        logger.error(
                            f"Error {response.status_code} on {endpoint}: {error_text}"
                        )
                        last_error = f"Error ({response.status_code}) on {endpoint}"
                        break  # Move to next endpoint

                    # Success!
                    resp_json = response.json()
                    if "response" in resp_json:
                        resp_json = resp_json["response"]

                    return resp_json

                except httpx.TimeoutException:
                    logger.warning(f"Timeout on {endpoint}")
                    last_error = f"Timeout on {endpoint}"
                    break  # Move to next endpoint

                except Exception as e:
                    logger.error(f"Exception on {endpoint}: {e}")
                    last_error = str(e)
                    break  # Move to next endpoint

    # All endpoints failed
    if last_error and "Rate limit" in last_error:
        raise ValueError(
            "Rate limit reached on all Antigravity endpoints. "
            "Please wait a few minutes and try again."
        )

    raise ValueError(f"All Antigravity endpoints failed. Last error: {last_error}")

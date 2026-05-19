---
name: new-integration
description: "Scaffold a complete integration — credential provider, HTTP client, service layer, loadOptions API endpoints, and node wiring. Covers both OAuth 2.0 and API Key integrations. Usage: /new-integration"
---

# new-integration skill

Ask the user for:
1. **Integration name** — PascalCase display name (e.g. `Notion`, `Linear`, `Stripe`)
2. **Auth type** — `oauth` or `api_key`
3. **What the service does** — brief description
4. **Icon URL** — from `https://cdn.brandfetch.io/<domain>/icon` (e.g. `https://cdn.brandfetch.io/notion.com/icon`)
5. **API base URL** — e.g. `https://api.notion.com/v1`
6. **Key API operations needed** — e.g. list databases, create page, search (these become loadOptions endpoints + service methods)
7. **For OAuth only**: client_id env var name, client_secret env var name, authorization URL, token URL, scopes needed

---

## TYPE A — OAuth Integration

### Files to create

#### 1. OAuth Provider — add to `apps/api/app/credential_manager/oauth/flow.py`

Follow the `SlackOAuthProvider` pattern exactly:

```python
class <Name>OAuthProvider:
    id = "<snake_name>_oauth"
    name = "<Display Name>"
    type = "oauth"
    description = "<description>"
    icon_url = "<icon_url>"
    scopes = [
        # Human-readable permission descriptions shown in the UI
        "...",
    ]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode
        params = {
            "client_id": settings.<NAME>_CLIENT_ID,
            "scope": "<space or comma separated scopes>",
            "redirect_uri": REDIRECT_URI.format(service="<snake_name>"),
            "state": state,
            "response_type": "code",
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"<authorization_url>?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx
        data = {
            "client_id": settings.<NAME>_CLIENT_ID,
            "client_secret": settings.<NAME>_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI.format(service="<snake_name>"),
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post("<token_url>", data=data)
        token_data = response.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"<Name> OAuth failed: {token_data}")

        return {
            "access_token": access_token,
            # include any other fields you need (refresh_token, workspace_id, etc.)
        }
```

Also register it in the same file's `OAUTH_PROVIDERS` dict:
```python
"<snake_name>": <Name>OAuthProvider(),
```

#### 2. Add env vars to `apps/api/app/core/config.py`

```python
<NAME>_CLIENT_ID: str = ""
<NAME>_CLIENT_SECRET: str = ""
```

And to `.env.example` (or `.env`):
```
<NAME>_CLIENT_ID=
<NAME>_CLIENT_SECRET=
```

#### 3. HTTP Client — `apps/api/app/integrations/<snake_name>/client.py`

Follow `apps/api/app/integrations/slack/client.py`:

```python
import httpx
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

<NAME>_BASE_URL = "<api_base_url>"


class <Name>Client:
    def __init__(self, access_token: str, client: httpx.AsyncClient | None = None):
        self._access_token = access_token
        self._client = client or httpx.AsyncClient(
            base_url=<NAME>_BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                # Add any API-version headers the service requires
            },
            timeout=30.0,
        )

    async def get(self, path: str, params: dict | None = None) -> dict:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, json: dict | None = None) -> dict:
        response = await self._client.post(path, json=json)
        response.raise_for_status()
        return response.json()

    async def patch(self, path: str, json: dict | None = None) -> dict:
        response = await self._client.patch(path, json=json)
        response.raise_for_status()
        return response.json()
```

Also create `apps/api/app/integrations/<snake_name>/__init__.py` (empty).

#### 4. Service — `apps/api/app/integrations/<snake_name>/service.py`

Follow `apps/api/app/integrations/slack/service.py`:

```python
import httpx
from apps.api.app.integrations.<snake_name>.client import <Name>Client


class <Name>Service:
    def __init__(self, access_token: str, client: httpx.AsyncClient | None = None):
        self._client = <Name>Client(access_token=access_token, client=client)

    # One method per key API operation the user specified
    async def <operation>(self, ...) -> dict:
        return await self._client.get("/<endpoint>", params={...})
```

#### 5. Integration router — `apps/api/app/api/v1/integrations/<snake_name>.py`

Follow `apps/api/app/api/v1/integrations/slack.py` exactly:

```python
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.integrations.<snake_name>.service import <Name>Service
from apps.api.app.models.user import User
from apps.api.app.repositories.credential_repository import CredentialRepository

logger = get_logger(__name__)
router = APIRouter()


async def get_<snake_name>_service(
    credential: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> <Name>Service:
    if not credential:
        raise HTTPException(status_code=400, detail="credential is required")

    repo = CredentialRepository(db)
    cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
    if not cred or cred.type != "<snake_name>_oauth":
        raise HTTPException(status_code=404, detail="<Name> credential not found")

    encryption_service = AESEncryptionService()
    decrypted_data = json.loads(encryption_service.decrypt(cred.encrypted_data))
    token = decrypted_data.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="Access token missing in credential")

    return <Name>Service(access_token=token)


# One endpoint per loadOptions operation — these feed the node inspector dropdowns
@router.get("/<resources>")
async def list_<resources>(
    credential: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = await get_<snake_name>_service(credential, db, current_user)
        data = await service.list_<resources>()
        items = [{"label": item["name"], "value": item["id"]} for item in data.get("results", [])]
        return {"ok": True, "data": items}
    except Exception as e:
        logger.error(f"Failed to list <snake_name> <resources>: {e}")
        return {"ok": False, "error": str(e)}
```

#### 6. Register in integrations router — `apps/api/app/api/v1/integrations/router.py`

```python
from apps.api.app.api.v1.integrations.<snake_name> import router as <snake_name>_router
router.include_router(<snake_name>_router, prefix="/<snake_name>", tags=["integrations"])
```

#### 7. Wire loadOptions into node definition (frontend)

In whatever node uses this integration, add `loadOptions` and `dependsOn` to the properties that need dynamic dropdowns:

```typescript
{
  name: 'database_id',
  label: 'Database',
  type: 'string',
  loadOptions: '/api/v1/integrations/<snake_name>/databases',
  loadOptionsDependsOn: ['credential'],
  dependsOn: ['credential'],
}
```

---

## TYPE B — API Key Integration

Much simpler — no client/service/router needed unless nodes require loadOptions.

#### 1. Add provider to `apps/api/app/credential_manager/api_keys.py`

Follow the `APIKeyProvider` pattern:

```python
PROVIDERS = {
    ...
    "<snake_name>": APIKeyProvider(
        id="<snake_name>_api_key",
        name="<Display Name>",
        description="<description>",
        icon_url="<icon_url>",
        hint="<key prefix hint, e.g. sk-...>",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="<hint>",
            ),
            # Add more fields if needed (e.g. base_url for self-hosted)
        ],
    ),
}
```

The credential picker in the frontend automatically shows API key providers — no other registration needed.

#### 2. Using the key in a node

In the node's `execute()`, the credential is injected automatically:

```python
async def execute(self, input_data: dict, context: NodeContext) -> NodeResult:
    api_key = self.credential.get("api_key") if self.credential else None
    if not api_key:
        return NodeResult(success=False, error="API key not configured")
    # use api_key ...
```

Make sure the node's `NodeMetadata` has `credential_type="<snake_name>_api_key"` and the frontend definition has `credentialType: '<snake_name>_api_key'`.

---

## Checklist before finishing

- [ ] Provider `id` is consistent everywhere (`<snake_name>_oauth` or `<snake_name>_api_key`)
- [ ] OAuth: env vars added to `config.py` and `.env`
- [ ] OAuth: provider registered in `OAUTH_PROVIDERS` dict
- [ ] OAuth: integration router registered in main integrations `router.py`
- [ ] loadOptions URLs in frontend match the actual endpoint paths
- [ ] `dependsOn: ['credential']` on all fields that need the credential to load options
- [ ] Node `credentialType` matches provider `id` exactly

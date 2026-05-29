"""API-level integration test for the auth flow.

Drives the real FastAPI app over httpx (ASGI transport): register -> login ->
authenticated /me, plus an unauthenticated rejection. Uses the real DB and
cleans up after itself (register creates a user + personal workspace + default
workflow). Skips if the DB is unreachable.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from apps.api.app.core.database import AsyncSessionLocal
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workspaces.models import Workspace

API = "/api/v1"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _db_available() -> bool:
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.mark.anyio
async def test_register_login_me_flow():
    if not await _db_available():
        pytest.skip("requires Postgres (run: make db-up)")

    email = f"apitest-{uuid.uuid4().hex[:8]}@fusetest.com"
    password = "password12345"

    try:
        transport = ASGITransport(app=_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                f"{API}/auth/register",
                json={"email": email, "password": password, "full_name": "API Test"},
            )
            assert r.status_code in (200, 201), r.text
            assert r.json()["email"] == email

            r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["token_type"] == "bearer"
            token = body["access_token"]

            r = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert r.status_code == 200, r.text
            assert r.json()["email"] == email

            # unauthenticated access is rejected
            r = await client.get(f"{API}/auth/me")
            assert r.status_code in (401, 403)
    finally:
        await _cleanup_user(email)


def _app():
    from apps.api.app.main import app

    return app


async def _cleanup_user(email: str) -> None:
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            return
        # Workflow.user_id is RESTRICT, but Workflow.workspace_id cascades — so
        # drop the workspace first (cascades members + workflows), then the user.
        await db.execute(delete(Workspace).where(Workspace.owner_id == user.id))
        await db.execute(delete(Workflow).where(Workflow.user_id == user.id))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()

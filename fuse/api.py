from fastapi import APIRouter

from fuse.auth.router import router as auth_router
from fuse.users.router import router as users_router
from fuse.items.router import router as items_router
from fuse.workflows.router import router as workflows_router
from fuse.ai.router import router as ai_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(items_router, prefix="/items", tags=["items"])
api_router.include_router(ai_router, prefix="/workflows/ai", tags=["ai"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])

from fuse.credentials.router import router as credentials_router
api_router.include_router(credentials_router, prefix="/credentials", tags=["credentials"])

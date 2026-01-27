from fastapi import APIRouter

from fuse.auth.router import router as auth_router
from fuse.users.router import router as users_router
from fuse.workflows.router import router as workflows_router
from fuse.ai.router import router as ai_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])

from fuse.credentials.router import router as credentials_router
api_router.include_router(credentials_router, prefix="/credentials", tags=["credentials"])

from fuse.plugins.router import router as plugins_router
api_router.include_router(plugins_router, prefix="/plugins", tags=["plugins"])

from fuse.nodes.router import router as nodes_router
api_router.include_router(nodes_router, prefix="/nodes", tags=["nodes"])

from fastapi import APIRouter

from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.items.router import router as items_router
from src.workflows.router import router as workflows_router
from src.ai.router import router as ai_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(items_router, prefix="/items", tags=["items"])
api_router.include_router(ai_router, prefix="/workflows/ai", tags=["ai"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])

from src.credentials.router import router as credentials_router
api_router.include_router(credentials_router, prefix="/credentials", tags=["credentials"])

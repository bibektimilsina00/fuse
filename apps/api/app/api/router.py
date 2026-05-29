from fastapi import APIRouter

from apps.api.app.api.v1.router import router as v1_router
from apps.api.app.core.config import settings

# Version aggregator: mount each API version here so main.py stays
# version-agnostic. To add v2, import its router and include it below —
# main.py does not change.
router = APIRouter()
router.include_router(v1_router, prefix=settings.API_V1_STR)

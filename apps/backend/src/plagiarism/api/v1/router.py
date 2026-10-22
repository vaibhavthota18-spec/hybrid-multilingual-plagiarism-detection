"""
API v1 Router Configuration
"""

from fastapi import APIRouter

from plagiarism.api.v1.analyses import router as analyses_router
from plagiarism.api.v1.auth import router as auth_router
from plagiarism.api.v1.collections import router as collections_router
from plagiarism.api.v1.comparisons import router as comparisons_router
from plagiarism.api.v1.documents import router as documents_router
from plagiarism.api.v1.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(collections_router)
api_v1_router.include_router(comparisons_router)
api_v1_router.include_router(analyses_router)


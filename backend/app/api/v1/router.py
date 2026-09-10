"""Versioned API router (mounted under /api/v1)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.analyses import router as analyses_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dogs import router as dogs_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.history import router as history_router
from app.api.v1.media import router as media_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(dogs_router, prefix="/dogs")
api_router.include_router(media_router, prefix="/media")
api_router.include_router(analyses_router, prefix="/analyses")
api_router.include_router(feedback_router, prefix="/analyses")
api_router.include_router(history_router, prefix="/history")

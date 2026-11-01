"""
backend/app/api/routes/settings.py — System & Privacy Settings Endpoint
"""

from fastapi import APIRouter
from backend.app.schemas.settings import SettingsData
from backend.app.services.analytics import analytics_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=SettingsData)
async def get_settings() -> SettingsData:
    """Returns camera, offline privacy, retention, and AI module connection status."""
    return analytics_service.get_settings()


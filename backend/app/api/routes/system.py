"""
backend/app/api/routes/system.py — Server System Status Endpoint
"""

from fastapi import APIRouter
from backend.app.schemas.system import SystemStatus
from backend.app.services.analytics import analytics_service

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/status", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    """Returns runtime connectivity status, data root, and backend build version."""
    return analytics_service.get_system_status()


"""
backend/app/api/routes/dashboard.py — Dashboard Summary Endpoint
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.app.core.config import settings
from backend.app.schemas.dashboard import DashboardSummary
from backend.app.services.analytics import analytics_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    demo: Optional[bool] = Query(
        default=None,
        description="Whether to return demonstration metrics (defaults to settings.is_demo_mode)",
    )
) -> DashboardSummary:
    """Returns high-level classroom metrics, active session, and timeline."""
    use_demo = demo if demo is not None else settings.is_demo_mode
    return analytics_service.get_dashboard_summary(include_demo=use_demo)


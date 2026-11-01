"""
backend/app/api/routes/health.py — System Health Check Endpoint
==============================================================
Required by Phase 1 gate condition: GET /health returns {"status": "ok"}.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """Returns basic health status conforming to Phase 1 gate conditions."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "phase": settings.phase,
        "pipeline_mode": settings.pipeline_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


"""
backend/app/api/api_router.py — Master API Router
=================================================
Aggregates all REST and WebSocket routes into a single router.
"""

from fastapi import APIRouter
from backend.app.api.routes import (
    analytics_router,
    dashboard_router,
    datasets_router,
    health_router,
    intelligence_router,
    models_router,
    ocr_router,
    rag_router,
    reports_router,
    sessions_router,
    settings_router,
    speech_router,
    system_router,
    vision_router,
    websocket_router,
    agents_router,
    tracking_router,
)

api_router = APIRouter()

# Health route (also mounted at root /health)
api_router.include_router(health_router)

# Core domain routes
api_router.include_router(dashboard_router)
api_router.include_router(sessions_router)
api_router.include_router(analytics_router)
api_router.include_router(intelligence_router)
api_router.include_router(rag_router)
api_router.include_router(reports_router)
api_router.include_router(models_router)
api_router.include_router(settings_router)
api_router.include_router(system_router)
api_router.include_router(websocket_router)

# Multimodal AI processing routes
api_router.include_router(vision_router)
api_router.include_router(tracking_router)
api_router.include_router(speech_router)
api_router.include_router(ocr_router)
api_router.include_router(datasets_router)

# Autonomous Multi-Agent Software Engineering routes
api_router.include_router(agents_router)

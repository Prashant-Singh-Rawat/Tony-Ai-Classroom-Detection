"""backend/app/api/routes package."""
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.dashboard import router as dashboard_router
from backend.app.api.routes.sessions import router as sessions_router
from backend.app.api.routes.analytics import router as analytics_router
from backend.app.api.routes.intelligence import router as intelligence_router
from backend.app.api.routes.rag import router as rag_router
from backend.app.api.routes.reports import router as reports_router
from backend.app.api.routes.models import router as models_router
from backend.app.api.routes.settings import router as settings_router
from backend.app.api.routes.system import router as system_router
from backend.app.api.routes.websocket import router as websocket_router
from backend.app.api.routes.vision import router as vision_router
from backend.app.api.routes.speech import router as speech_router
from backend.app.api.routes.ocr import router as ocr_router
from backend.app.api.routes.datasets import router as datasets_router
from backend.app.api.routes.agents import router as agents_router
from backend.app.api.routes.tracking import router as tracking_router

__all__ = [
    "health_router",
    "dashboard_router",
    "sessions_router",
    "analytics_router",
    "intelligence_router",
    "rag_router",
    "reports_router",
    "models_router",
    "settings_router",
    "system_router",
    "websocket_router",
    "vision_router",
    "speech_router",
    "ocr_router",
    "datasets_router",
    "agents_router",
    "tracking_router",
]

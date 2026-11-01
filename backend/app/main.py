"""
backend/app/main.py — FastAPI Application Entrypoint
===================================================
ClassVision AI — Real-Time Multimodal Classroom Intelligence System.
Phase 1.0 — FastAPI Backend Foundation.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from backend.app.api.api_router import api_router
from backend.app.api.routes.health import router as health_router
from backend.app.core.config import settings
from backend.app.core.cors import setup_cors


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown hooks."""
    # Startup: initialize database tables
    try:
        from backend.app.database.db import init_db
        init_db()
    except Exception:
        pass
    yield
    # Shutdown: cleanup


def create_application() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Privacy-preserving multimodal classroom monitoring system fusing "
            "computer vision, speech transcription, whiteboard OCR, and curriculum RAG."
        ),
        lifespan=lifespan,
    )

    # Configure CORS middleware
    setup_cors(app)

    # Mount /health at root (strict Phase 1 gate requirement: GET /health returns {"status": "ok"})
    app.include_router(health_router)

    # Mount all API endpoints (/api/...)
    app.include_router(api_router)

    return app


# Application singleton instance for ASGI servers (uvicorn backend.app.main:app)
app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )


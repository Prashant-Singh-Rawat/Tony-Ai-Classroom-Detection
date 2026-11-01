"""
backend/app/core/cors.py — Cross-Origin Resource Sharing (CORS) Configuration
=============================================================================
Enables secure local communication between React frontend and FastAPI backend.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings


def setup_cors(app: FastAPI) -> None:
    """Configures CORS middleware for the FastAPI application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


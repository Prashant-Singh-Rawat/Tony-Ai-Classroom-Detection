"""
backend/app/api/routes/models.py — Model and Dataset Status Audit Endpoint
==========================================================================
1. GET /api/model/status: Legacy ground-truth audit endpoint (preserved).
2. GET /api/model/registry: Multi-model registry, provenance, and evaluation metrics.
"""

import json
from fastapi import APIRouter
from backend.app.core.config import REPO_ROOT
from backend.app.schemas.models import ModelStatusData
from backend.app.services.analytics import analytics_service

router = APIRouter(prefix="/api/model", tags=["Model Status"])


@router.get("/status", response_model=ModelStatusData)
async def get_model_status() -> ModelStatusData:
    """Returns verified repository ground-truth facts: dataset counts, 0 checkpoints, test status."""
    return analytics_service.get_model_status()


@router.get("/registry")
def get_model_registry() -> dict:
    """Returns the comprehensive multi-model registry and evaluation benchmarks."""
    registry_path = REPO_ROOT / "models" / "model_registry.json"
    if registry_path.is_file():
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"models": [], "status": "REGISTRY_NOT_FOUND"}

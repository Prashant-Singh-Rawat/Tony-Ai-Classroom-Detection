"""
backend/app/agents/tools/project_tools.py — Project Structure & Telemetry Tools
================================================================================
Inspects endpoints, SQLAlchemy schemas, models, datasets, and dependencies.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.core.config import REPO_ROOT
from backend.app.agents.tools.tool_registry import ToolRegistry, tool_registry
from backend.app.agents.core.types import ToolPermissionLevel


def inspect_api_endpoints() -> List[Dict[str, str]]:
    """Introspects registered FastAPI route endpoints and HTTP methods."""
    try:
        from backend.app.main import app
        endpoints = []
        for route in app.routes:
            methods = getattr(route, "methods", None)
            path = getattr(route, "path", None)
            name = getattr(route, "name", None)
            if path:
                endpoints.append({
                    "path": path,
                    "methods": list(methods) if methods else ["WS"],
                    "name": name or "",
                })
        return endpoints
    except Exception as e:
        return [{"error": f"Failed to introspect API routes: {str(e)}"}]


def inspect_database_schemas() -> List[Dict[str, Any]]:
    """Introspects registered SQLAlchemy ORM tables and column definitions."""
    try:
        from backend.app.database.models import Base
        tables = []
        for table_name, table in Base.metadata.tables.items():
            cols = [
                {"name": c.name, "type": str(c.type), "primary_key": c.primary_key, "nullable": c.nullable}
                for c in table.columns
            ]
            tables.append({
                "table_name": table_name,
                "columns": cols,
            })
        return tables
    except Exception as e:
        return [{"error": f"Failed to introspect database schema: {str(e)}"}]


def inspect_dependencies() -> Dict[str, Any]:
    """Inspects backend requirements and frontend package.json dependencies."""
    result: Dict[str, Any] = {"python": [], "node": {}}
    req_file = REPO_ROOT / "backend" / "requirements.txt"
    if req_file.is_file():
        with open(req_file, "r", encoding="utf-8") as f:
            result["python"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    pkg_file = REPO_ROOT / "frontend" / "package.json"
    if pkg_file.is_file():
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
                result["node"] = {
                    "dependencies": pkg_data.get("dependencies", {}),
                    "devDependencies": pkg_data.get("devDependencies", {}),
                }
        except Exception:
            pass

    return result


def inspect_model_status() -> Dict[str, Any]:
    """Checks pretrained model status across CV, Speech, OCR, and NLP pipelines."""
    try:
        from backend.app.services.computer_vision import cv_service
        from backend.app.services.speech import speech_service
        from backend.app.services.ocr import ocr_service

        return {
            "computer_vision": cv_service.get_status_info(),
            "speech": speech_service.get_status_info(),
            "ocr": ocr_service.get_status_info(),
        }
    except Exception as e:
        return {"error": f"Failed to introspect model status: {str(e)}"}


def inspect_dataset_statistics() -> Dict[str, Any]:
    """Queries dataset manager for verified Kaggle vs. Synthetic counts."""
    try:
        from backend.app.services.dataset_manager import dataset_manager
        return dataset_manager.get_statistics()
    except Exception as e:
        return {"error": f"Failed to introspect dataset statistics: {str(e)}"}


# Register project tools
tool_registry.register_tool(
    name="inspect_api_endpoints",
    func=inspect_api_endpoints,
    description="Inspects all mounted FastAPI HTTP and WebSocket routes.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="inspect_database_schemas",
    func=inspect_database_schemas,
    description="Inspects SQLAlchemy database tables, columns, and foreign keys.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="inspect_dependencies",
    func=inspect_dependencies,
    description="Inspects Python and Node.js dependency specifications.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="inspect_model_status",
    func=inspect_model_status,
    description="Inspects pretrained model weights, readiness, and inference devices.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="inspect_dataset_statistics",
    func=inspect_dataset_statistics,
    description="Inspects Kaggle and Synthetic dataset sample counts and compliance ratios.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)


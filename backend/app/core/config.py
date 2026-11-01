"""
backend/app/core/config.py — Central Application Configuration
=============================================================
Manages runtime settings, environment variables, and filesystem paths.
Honors Phase 0 config files (modes.yaml, confidence.yaml, retention.yaml).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Locate repository root (two levels up from backend/app)
REPO_ROOT = Path(__file__).resolve().parents[3]
CLASSVISION_ROOT = REPO_ROOT / "classvision-ai"


def _find_config_dir() -> Path:
    """Finds the configuration directory across root and subproject."""
    candidates = [
        REPO_ROOT / "config",
        CLASSVISION_ROOT / "config",
    ]
    for c in candidates:
        if c.is_dir() and (c / "modes.yaml").is_file():
            return c
    return CLASSVISION_ROOT / "config"


CONFIG_DIR = _find_config_dir()


def load_yaml_config(filename: str) -> dict:
    """Safely loads a YAML config file from the resolved config directory."""
    target = CONFIG_DIR / filename
    if target.is_file():
        try:
            with open(target, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}


class Settings(BaseSettings):
    """ClassVision AI backend configuration settings."""

    # Project metadata
    app_name: str = "ClassVision AI"
    app_version: str = "1.0.0"
    phase: str = "Phase 1.0 - Backend Foundation"

    # Server binding
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    secret_key: str = Field(default="dev-secret-key-classvision-ai", alias="SECRET_KEY")

    # Pipeline operational mode: DEMO or ACCURACY
    pipeline_mode: str = Field(default="DEMO", alias="PIPELINE_MODE")

    # Data paths & privacy
    data_root: str = Field(
        default=os.environ.get(
            "CLASSVISION_REAL_DATA_ROOT",
            str(REPO_ROOT / "datasets" / "real_classroom"),
        ),
        alias="DATA_ROOT",
    )
    blur_faces_override: Optional[bool] = Field(default=None, alias="BLUR_FACES_OVERRIDE")

    # CORS origins
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    # Model paths
    model_registry_path: str = Field(
        default=str(CLASSVISION_ROOT / "models" / "model_registry.json"),
        alias="MODEL_REGISTRY_PATH",
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_demo_mode(self) -> bool:
        """Returns True if the backend is configured in DEMO mode."""
        return self.pipeline_mode.upper() == "DEMO"

    def get_modes_config(self) -> dict:
        return load_yaml_config("modes.yaml")

    def get_confidence_config(self) -> dict:
        return load_yaml_config("confidence.yaml")

    def get_retention_config(self) -> dict:
        return load_yaml_config("retention.yaml")


# Global singleton settings instance
settings = Settings()


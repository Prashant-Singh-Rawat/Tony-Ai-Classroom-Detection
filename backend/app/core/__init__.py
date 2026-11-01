"""backend/app/core package."""
from backend.app.core.config import settings
from backend.app.core.cors import setup_cors

__all__ = ["settings", "setup_cors"]


"""Analytics Service Package."""
from backend.app.services.analytics.service import (
    analytics_service,
    AnalyticsService,
    DEMO_BOUNDING_BOXES,
)
from backend.app.services.analytics.engine import (
    analytics_engine,
    ClassroomActivityAnalyticsEngine,
)

__all__ = [
    "analytics_service",
    "AnalyticsService",
    "DEMO_BOUNDING_BOXES",
    "analytics_engine",
    "ClassroomActivityAnalyticsEngine",
]


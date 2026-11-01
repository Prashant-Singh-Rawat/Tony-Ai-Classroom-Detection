"""backend/app/schemas package."""
from backend.app.schemas.common import DataStatus, HandRaiseClass
from backend.app.schemas.detections import BoundingBox, WebSocketDetectionMessage
from backend.app.schemas.sessions import SessionInfo
from backend.app.schemas.dashboard import (
    ActivityTimelineItem,
    DashboardStats,
    DashboardSummary,
)
from backend.app.schemas.analytics import (
    ActivityDistributionItem,
    AnalyticsData,
    ClassroomComparisonItem,
    HourlyTrendItem,
    TimeSeriesItem,
)
from backend.app.schemas.intelligence import (
    LectureIntelligenceData,
    OcrNoteItem,
    QuestionMomentItem,
    TranscriptItem,
)
from backend.app.schemas.rag import RagQueryRequest, RagResponse, RagSource
from backend.app.schemas.reports import (
    ModelQualityReport,
    ReportItem,
    ReportsResponse,
)
from backend.app.schemas.models import (
    EvaluationMetricsStatus,
    KaggleGestureDatasetStatus,
    ModelStatusData,
    RealClassroomDatasetStatus,
    VerifiedTestsStatus,
)
from backend.app.schemas.settings import (
    AiModulesSettings,
    CameraSettings,
    PrivacySettings,
    SettingsData,
    SystemMetaSettings,
)
from backend.app.schemas.system import SystemStatus

__all__ = [
    "HandRaiseClass",
    "DataStatus",
    "BoundingBox",
    "WebSocketDetectionMessage",
    "SessionInfo",
    "DashboardStats",
    "ActivityTimelineItem",
    "DashboardSummary",
    "TimeSeriesItem",
    "ActivityDistributionItem",
    "ClassroomComparisonItem",
    "HourlyTrendItem",
    "AnalyticsData",
    "TranscriptItem",
    "OcrNoteItem",
    "QuestionMomentItem",
    "LectureIntelligenceData",
    "RagQueryRequest",
    "RagSource",
    "RagResponse",
    "ReportItem",
    "ModelQualityReport",
    "ReportsResponse",
    "KaggleGestureDatasetStatus",
    "RealClassroomDatasetStatus",
    "EvaluationMetricsStatus",
    "VerifiedTestsStatus",
    "ModelStatusData",
    "CameraSettings",
    "PrivacySettings",
    "AiModulesSettings",
    "SystemMetaSettings",
    "SettingsData",
    "SystemStatus",
]


"""
backend/app/schemas/dashboard.py — Dashboard summary schemas
"""

from typing import List, Literal, Optional
from pydantic import Field
from backend.app.schemas.common import CamelModel
from backend.app.schemas.sessions import SessionInfo


class DashboardStats(CamelModel):
    totalPeopleDetected: int = Field(..., alias="totalPeopleDetected")
    activeHandRaises: int = Field(..., alias="activeHandRaises")
    handRaisePercentage: float = Field(..., alias="handRaisePercentage")
    engagementScore: float = Field(..., alias="engagementScore")
    activeCameras: int = Field(..., alias="activeCameras")
    privacyModeActive: bool = Field(default=True, alias="privacyModeActive")
    systemMode: Literal["demo", "live"] = Field(..., alias="systemMode")


class ActivityTimelineItem(CamelModel):
    time: str
    handRaises: int = Field(..., alias="handRaises")
    attentiveStudents: int = Field(..., alias="attentiveStudents")
    ambiguousCount: int = Field(..., alias="ambiguousCount")


class DashboardSummary(CamelModel):
    currentSession: Optional[SessionInfo] = Field(default=None, alias="currentSession")
    stats: DashboardStats
    recentSessions: List[SessionInfo] = Field(default_factory=list, alias="recentSessions")
    activityTimeline: List[ActivityTimelineItem] = Field(default_factory=list, alias="activityTimeline")
    isDemoData: bool = Field(default=True, alias="isDemoData")


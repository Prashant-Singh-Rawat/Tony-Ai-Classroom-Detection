"""
backend/app/schemas/sessions.py — Classroom Session schemas
"""

from typing import List, Literal, Optional
from pydantic import Field
from backend.app.schemas.common import CamelModel


class SessionInfo(CamelModel):
    """Metadata and high-level statistics for a classroom recording session."""

    sessionId: str = Field(..., alias="sessionId")
    title: str
    courseCode: str = Field(..., alias="courseCode")
    date: str
    startTime: str = Field(..., alias="startTime")
    durationMinutes: int = Field(..., alias="durationMinutes")
    classroom: str
    instructor: str
    status: Literal["active", "completed", "scheduled"]
    totalStudents: int = Field(..., alias="totalStudents")
    activeHandRaises: int = Field(..., alias="activeHandRaises")
    totalHandRaiseEvents: int = Field(..., alias="totalHandRaiseEvents")
    averageEngagement: float = Field(..., alias="averageEngagement")
    privacyProtected: bool = Field(default=True, alias="privacyProtected")
    instructorRoiPolygon: Optional[List[List[float]]] = Field(default=None, alias="instructorRoiPolygon")
    zoneFilteringEnabled: bool = Field(default=True, alias="zoneFilteringEnabled")


class SessionZoneConfigRequest(CamelModel):
    """Request payload to configure or update the Teacher Zone Exclusion polygon."""

    instructorRoiPolygon: Optional[List[List[float]]] = Field(
        default=None,
        description="Normalized coordinates [[x, y], ...] in range [0.0, 1.0]",
        alias="instructorRoiPolygon",
    )
    zoneFilteringEnabled: bool = Field(default=True, alias="zoneFilteringEnabled")



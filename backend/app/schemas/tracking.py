"""
backend/app/schemas/tracking.py — Temporal Tracking & Hand-Raising Event Schemas
================================================================================
Phase 2.2: Temporal Hand-Raising Detection & Anonymous Person Tracking.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from backend.app.schemas.common import CamelModel
from backend.app.schemas.detections import PersonDetection, PoseGeometry, PoseKeypoint


class HandRaisingState(str, Enum):
    """Temporal state of hand raising for a tracked anonymous person."""

    NOT_RAISED = "NOT_RAISED"
    RAISING = "RAISING"
    RAISED = "RAISED"
    LOWERING = "LOWERING"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class HandSide(str, Enum):
    """Which hand is raised or engaged in gesture."""

    LEFT_HAND = "LEFT_HAND"
    RIGHT_HAND = "RIGHT_HAND"
    BOTH_HANDS = "BOTH_HANDS"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class TrackedPersonState(CamelModel):
    """Current temporal tracking state of an anonymous individual."""

    trackId: str
    state: HandRaisingState = HandRaisingState.NOT_RAISED
    handSide: HandSide = HandSide.NONE
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    bbox: PersonDetection
    keypoints: List[PoseKeypoint] = Field(default_factory=list)
    geometry: Optional[PoseGeometry] = None
    framesInCurrentState: int = 1
    totalFramesTracked: int = 1
    missingFramesCount: int = 0
    isOccluded: bool = False
    activeEventId: Optional[str] = None
    lastUpdatedTimestamp: float = 0.0


class HandRaiseEventSchema(CamelModel):
    """A temporal hand-raising event aggregated across consecutive video frames."""

    id: Optional[int] = None
    eventId: str
    sessionId: str
    trackId: str
    handSide: HandSide = HandSide.NONE
    state: str = "COMPLETED"  # "RAISED" (ongoing) | "COMPLETED" | "NEEDS_REVIEW"
    zoneClassification: str = "STUDENT_ZONE"  # "STUDENT_ZONE" | "INSTRUCTOR_ZONE" | "NEEDS_REVIEW" | "NOT_CONFIGURED"
    startTimestampSeconds: float
    endTimestampSeconds: Optional[float] = None
    durationSeconds: float = 0.0
    startFrame: int = 0
    endFrame: Optional[int] = None
    frameCount: int = 1
    maxConfidence: float = 0.0
    avgConfidence: float = 0.0
    evidence: Dict[str, Any] = Field(default_factory=dict)
    dataSource: str = "REAL_PROCESSING"
    createdAt: Optional[str] = None


class TrackingSummaryResponse(CamelModel):
    """Response payload for current active tracked people and states."""

    sessionId: str
    timestampSeconds: float
    activeTracksCount: int = 0
    activeHandRaisesCount: int = 0
    statesSummary: Dict[str, int] = Field(default_factory=dict)
    tracks: List[TrackedPersonState] = Field(default_factory=list)
    activeEvents: List[HandRaiseEventSchema] = Field(default_factory=list)
    dataSource: str = "REAL_PROCESSING"


class TrackingEventStatisticsResponse(CamelModel):
    """Aggregated statistics for temporal hand-raising events."""

    sessionId: Optional[str] = None
    totalEvents: int = 0
    completedEvents: int = 0
    activeEvents: int = 0
    leftHandCount: int = 0
    rightHandCount: int = 0
    bothHandsCount: int = 0
    avgDurationSeconds: float = 0.0
    maxDurationSeconds: float = 0.0
    totalDurationSeconds: float = 0.0
    needsReviewCount: int = 0
    cooldownPeriodSeconds: float = 1.0
    studentZoneEvents: int = 0
    instructorZoneEvents: int = 0
    uncertainEvents: int = 0
    zoneFilteringEnabled: bool = True



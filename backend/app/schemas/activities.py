"""
backend/app/schemas/activities.py — Observable Classroom Activity Schemas
========================================================================
Defines explainable, observable activity labels based strictly on visible
physical geometry, posture, and detected objects without subjective mental scoring.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field
from backend.app.schemas.common import CamelModel


class ActivityLabel(str, Enum):
    """Observable physical activity labels."""

    NO_FLAG_OBSERVED = "NO_FLAG_OBSERVED"
    HEAD_DOWN_POSTURE = "HEAD_DOWN_POSTURE"
    PHONE_VISIBLE = "PHONE_VISIBLE"
    LEFT_HAND_RAISED = "LEFT_HAND_RAISED"
    RIGHT_HAND_RAISED = "RIGHT_HAND_RAISED"
    BOTH_HANDS_RAISED = "BOTH_HANDS_RAISED"
    HAND_RAISED = "HAND_RAISED"
    POSSIBLE_PEER_INTERACTION = "POSSIBLE_PEER_INTERACTION"
    POSSIBLE_SPEAKING = "POSSIBLE_SPEAKING"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ActivityEvidence(CamelModel):
    """Explainable geometric and object detection evidence supporting an activity label."""

    detectorUsed: str = "YOLOv8n-pose"
    observedFeatures: List[str] = Field(default_factory=list)
    geometryMetrics: Dict[str, float] = Field(default_factory=dict)
    detectedObjects: List[str] = Field(default_factory=list)
    persistenceFrames: int = 1
    durationSeconds: float = 0.0
    rationale: str = ""


class TrackedActivityState(CamelModel):
    """Current observable activity state for an anonymous tracked individual."""

    trackId: str
    activityLabel: ActivityLabel = ActivityLabel.NO_FLAG_OBSERVED
    displayLabel: str = "NO FLAG OBSERVED"
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    durationSeconds: float = 0.0
    observationWindowFrames: int = 1
    evidence: ActivityEvidence = Field(default_factory=ActivityEvidence)
    statusColor: str = "GREEN"  # GREEN, RED, ORANGE, BLUE, YELLOW
    isAmbiguous: bool = False


class ActivityEventSchema(CamelModel):
    """Persisted record of an observable activity event."""

    eventId: str
    sessionId: str
    trackId: str
    activityLabel: ActivityLabel
    displayLabel: str
    startTimestampSeconds: float
    endTimestampSeconds: Optional[float] = None
    durationSeconds: float = 0.0
    startFrame: int = 0
    endFrame: Optional[int] = None
    frameCount: int = 1
    confidence: float = 0.0
    evidenceSource: str = "YOLOv8n"
    status: str = "COMPLETED"  # "ACTIVE", "COMPLETED", "NEEDS_REVIEW"
    evidenceDetails: Dict[str, Any] = Field(default_factory=dict)
    dataSource: str = "REAL_PROCESSING"
    createdAt: Optional[str] = None


class ActivityDistributionSummary(CamelModel):
    """Aggregate distribution of observable activities across a session."""

    sessionId: str
    totalTrackedPersons: int = 0
    totalActivityEvents: int = 0
    activityCounts: Dict[str, int] = Field(default_factory=dict)
    activityPercentages: Dict[str, float] = Field(default_factory=dict)
    avgDurations: Dict[str, float] = Field(default_factory=dict)
    disclaimer: str = (
        "Observable activity labels reflect visible physical geometry and detected objects only. "
        "They do not evaluate student focus, attentiveness, engagement, or academic performance."
    )


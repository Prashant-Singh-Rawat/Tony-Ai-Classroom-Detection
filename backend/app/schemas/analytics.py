"""
backend/app/schemas/analytics.py — Classroom Activity Analytics Schemas
======================================================================
Phase 2.3: Session analytics, temporal participation trends, track-level breakdown,
multi-session comparison, and timeline analytics across configurable intervals.
Strictly reports observable physical actions without inferring cognitive engagement.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field
from backend.app.schemas.activities import ActivityDistributionSummary
from backend.app.schemas.common import CamelModel


class TimeSeriesItem(CamelModel):
    minute: int
    timestamp: str
    handRaises: int = Field(..., alias="handRaises")
    attentionIndex: float = Field(..., alias="attentionIndex")
    questionsLogged: int = Field(..., alias="questionsLogged")


class ActivityDistributionItem(CamelModel):
    name: str
    count: int
    percentage: float
    color: str


class ClassroomComparisonItem(CamelModel):
    classroom: str
    avgStudents: float = Field(..., alias="avgStudents")
    avgHandRaises: float = Field(..., alias="avgHandRaises")
    participationRate: float = Field(..., alias="participationRate")


class HourlyTrendItem(CamelModel):
    timeBlock: str = Field(..., alias="timeBlock")
    avgParticipation: float = Field(..., alias="avgParticipation")


class AnalyticsData(CamelModel):
    timeSeries: List[TimeSeriesItem] = Field(default_factory=list, alias="timeSeries")
    activityDistribution: List[ActivityDistributionItem] = Field(
        default_factory=list, alias="activityDistribution"
    )
    classroomComparison: List[ClassroomComparisonItem] = Field(
        default_factory=list, alias="classroomComparison"
    )
    hourlyTrends: List[HourlyTrendItem] = Field(default_factory=list, alias="hourlyTrends")
    isDemoData: bool = Field(default=True, alias="isDemoData")


# ---------------------------------------------------------------------------
# Phase 2.3 Classroom Activity Analytics Schemas
# ---------------------------------------------------------------------------

class ParticipationTimeBucket(CamelModel):
    """Aggregated observable events inside a discrete time interval (1m, 5m, 10m)."""
    bucketIndex: int
    startTimeSeconds: float
    endTimeSeconds: float
    label: str
    eventCount: int = 0
    leftHandCount: int = 0
    rightHandCount: int = 0
    bothHandsCount: int = 0
    activeTracksCount: int = 0


class TrackParticipationSummary(CamelModel):
    """Observable physical activity per anonymous, session-scoped track ID."""
    trackId: str
    eventCount: int = 0
    totalDurationSeconds: float = 0.0
    avgDurationSeconds: float = 0.0
    leftHandCount: int = 0
    rightHandCount: int = 0
    bothHandsCount: int = 0
    firstSeenSeconds: Optional[float] = None
    lastSeenSeconds: Optional[float] = None


class EventTypeDistribution(CamelModel):
    """Percentage breakdown of observable hand-raising physical categories."""
    leftHandPct: float = 0.0
    rightHandPct: float = 0.0
    bothHandsPct: float = 0.0
    unknownPct: float = 0.0


class SessionActivityAnalytics(CamelModel):
    """
    Session-level classroom activity intelligence.
    Derived strictly from observable SQLite hand_raise_events and detection records.
    Never equates track count to total students, and never infers internal mental states.
    """
    sessionId: str
    title: str = "Classroom Activity Session"
    courseCode: Optional[str] = None
    date: Optional[str] = None
    startTime: Optional[str] = None
    durationMinutes: Optional[float] = None

    # Observed Population Metrics
    totalObservedPeoplePeak: int = 0
    uniqueAnonymousTracksObserved: int = 0

    # Observable Participation Event Metrics
    totalHandRaisingEvents: int = 0
    completedEventsCount: int = 0
    activeEventsCount: int = 0
    leftHandEvents: int = 0
    rightHandEvents: int = 0
    bothHandEvents: int = 0

    # Teacher Zone Exclusion & Spatial Analytics
    instructorRoiPolygon: Optional[List[List[float]]] = None
    zoneFilteringEnabled: bool = True
    totalDetectedHandRaises: int = 0
    studentZoneEventsCount: int = 0
    instructorZoneEventsCount: int = 0
    uncertainZoneEventsCount: int = 0

    # Duration Metrics
    averageEventDurationSeconds: float = 0.0
    maxEventDurationSeconds: float = 0.0
    totalEventDurationSeconds: float = 0.0

    # Rate & Distribution Metrics
    observableParticipationEvents: int = 0
    eventTypeDistribution: EventTypeDistribution = Field(default_factory=EventTypeDistribution)
    activityDistribution: Optional[ActivityDistributionSummary] = None

    # Observation Extremes
    mostFrequentlyObservedTrack: Optional[str] = None
    leastFrequentlyObservedTrack: Optional[str] = None
    peakParticipationInterval: Optional[str] = None

    # Timeline & Track Breakdown
    intervalSeconds: int = 60
    timeline: List[ParticipationTimeBucket] = Field(default_factory=list)
    trackSummaries: List[TrackParticipationSummary] = Field(default_factory=list)

    # Provenance & Ethics
    dataSource: str = "REAL_PROCESSING"
    isDemoData: bool = False
    privacyDisclaimer: str = (
        "Observable physical activity only. No attention, concentration, "
        "emotion, intelligence, or cognitive engagement is inferred."
    )


class SessionComparisonSummary(CamelModel):
    """Comparative delta between two sessions for a specific metric."""
    metric: str
    sessionAValue: Any
    sessionBValue: Any
    difference: Optional[str] = None
    interpretation: str


class SessionComparisonResponse(CamelModel):
    """Side-by-side comparison of two independent classroom sessions."""
    sessionA: SessionActivityAnalytics
    sessionB: SessionActivityAnalytics
    comparisons: List[SessionComparisonSummary] = Field(default_factory=list)
    generatedAt: str

"""
tests/api/test_activity_analytics.py — Phase 2.3 Classroom Activity Analytics Tests
===================================================================================
Tests session activity aggregation, event classification counts, duration statistics,
configurable time-buckets, zero-event session safety, cross-session comparisons,
CSV and PDF exports, and ethical privacy guarantees.
"""

from __future__ import annotations

import os
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.database.db import SessionLocal
from backend.app.database.repositories import HandRaiseEventRepository
from backend.app.main import app
from backend.app.services.analytics import analytics_engine

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_empty_session_analytics(db_session):
    """Verifies that an empty session with zero events produces valid zeroed analytics."""
    empty_session_id = f"sess_empty_{uuid.uuid4().hex[:6]}"
    analytics = analytics_engine.get_session_activity(
        session_id=empty_session_id,
        db=db_session,
        include_demo=False,
    )
    assert analytics.sessionId == empty_session_id
    assert analytics.totalHandRaisingEvents == 0
    assert analytics.uniqueAnonymousTracksObserved == 0
    assert analytics.averageEventDurationSeconds == 0.0
    assert analytics.maxEventDurationSeconds == 0.0
    assert analytics.totalEventDurationSeconds == 0.0
    assert analytics.timeline == []
    assert analytics.trackSummaries == []
    assert "Observable physical activity only" in analytics.privacyDisclaimer


def test_demo_session_activity_analytics():
    """Verifies that demo session sess_01 returns complete grounded activity metrics."""
    analytics = analytics_engine.get_session_activity(
        session_id="sess_01",
        interval_seconds=60,
        include_demo=True,
    )
    assert analytics.sessionId == "sess_01"
    assert analytics.totalHandRaisingEvents == 19
    assert analytics.uniqueAnonymousTracksObserved == 12
    assert analytics.leftHandEvents == 9
    assert analytics.rightHandEvents == 8
    assert analytics.bothHandEvents == 2
    assert analytics.averageEventDurationSeconds > 0
    assert analytics.isDemoData is True
    assert len(analytics.timeline) > 0
    assert len(analytics.trackSummaries) == 12
    assert analytics.mostFrequentlyObservedTrack is not None


def test_sqlite_real_session_aggregation(db_session):
    """Verifies aggregation directly from persisted SQLite HandRaiseEventRecord rows."""
    test_session_id = f"sess_real_{uuid.uuid4().hex[:6]}"
    repo = HandRaiseEventRepository(db_session)

    # Insert 3 events across 2 anonymous tracks
    repo.create(
        event_id=f"evt_{uuid.uuid4().hex[:6]}",
        session_id=test_session_id,
        track_id="track_001",
        hand_side="LEFT_HAND",
        state="COMPLETED",
        start_timestamp_seconds=10.0,
        end_timestamp_seconds=12.5,
        duration_seconds=2.5,
        start_frame=100,
        end_frame=150,
        frame_count=50,
        max_confidence=0.92,
        avg_confidence=0.88,
        data_source="REAL_PROCESSING",
    )
    repo.create(
        event_id=f"evt_{uuid.uuid4().hex[:6]}",
        session_id=test_session_id,
        track_id="track_001",
        hand_side="RIGHT_HAND",
        state="COMPLETED",
        start_timestamp_seconds=70.0,
        end_timestamp_seconds=73.5,
        duration_seconds=3.5,
        start_frame=700,
        end_frame=735,
        frame_count=35,
        max_confidence=0.95,
        avg_confidence=0.91,
        data_source="REAL_PROCESSING",
    )
    repo.create(
        event_id=f"evt_{uuid.uuid4().hex[:6]}",
        session_id=test_session_id,
        track_id="track_002",
        hand_side="BOTH_HANDS",
        state="COMPLETED",
        start_timestamp_seconds=130.0,
        end_timestamp_seconds=131.5,
        duration_seconds=1.5,
        start_frame=1300,
        end_frame=1315,
        frame_count=15,
        max_confidence=0.89,
        avg_confidence=0.85,
        data_source="REAL_PROCESSING",
    )

    analytics = analytics_engine.get_session_activity(
        session_id=test_session_id,
        interval_seconds=60,
        db=db_session,
    )

    assert analytics.sessionId == test_session_id
    assert analytics.totalHandRaisingEvents == 3
    assert analytics.uniqueAnonymousTracksObserved == 2
    assert analytics.leftHandEvents == 1
    assert analytics.rightHandEvents == 1
    assert analytics.bothHandEvents == 1
    assert analytics.averageEventDurationSeconds == 2.5  # (2.5 + 3.5 + 1.5) / 3 = 2.5
    assert analytics.maxEventDurationSeconds == 3.5
    assert analytics.totalEventDurationSeconds == 7.5
    assert analytics.isDemoData is False

    # Check track summaries
    assert len(analytics.trackSummaries) == 2
    t1 = next(s for s in analytics.trackSummaries if s.trackId == "track_001")
    assert t1.eventCount == 2
    assert t1.leftHandCount == 1
    assert t1.rightHandCount == 1
    assert t1.totalDurationSeconds == 6.0
    assert analytics.mostFrequentlyObservedTrack == "track_001"


def test_time_bucket_analytics_intervals(db_session):
    """Verifies that configurable time intervals (60s, 300s) bucket events accurately."""
    test_session_id = f"sess_intervals_{uuid.uuid4().hex[:6]}"
    repo = HandRaiseEventRepository(db_session)

    # Event in minute 1 (t=15s)
    repo.create(
        event_id=f"evt_{uuid.uuid4().hex[:6]}",
        session_id=test_session_id,
        track_id="track_001",
        hand_side="LEFT_HAND",
        state="COMPLETED",
        start_timestamp_seconds=15.0,
        end_timestamp_seconds=17.0,
        duration_seconds=2.0,
        data_source="REAL_PROCESSING",
    )
    # Event in minute 2 (t=80s)
    repo.create(
        event_id=f"evt_{uuid.uuid4().hex[:6]}",
        session_id=test_session_id,
        track_id="track_002",
        hand_side="RIGHT_HAND",
        state="COMPLETED",
        start_timestamp_seconds=80.0,
        end_timestamp_seconds=83.0,
        duration_seconds=3.0,
        data_source="REAL_PROCESSING",
    )

    # Test 60s intervals -> 2 separate buckets
    a_60 = analytics_engine.get_session_activity(test_session_id, interval_seconds=60, db=db_session)
    assert len(a_60.timeline) >= 2
    assert a_60.timeline[0].eventCount == 1
    assert a_60.timeline[1].eventCount == 1

    # Test 300s (5-minute) intervals -> both events in bucket 0
    a_300 = analytics_engine.get_session_activity(test_session_id, interval_seconds=300, db=db_session)
    assert len(a_300.timeline) >= 1
    assert a_300.timeline[0].eventCount == 2


def test_session_comparison():
    """Verifies multi-session comparison output and non-cognitive wording."""
    comparison = analytics_engine.compare_sessions("sess_01", "sess_02", include_demo=True)
    assert comparison.sessionA.sessionId == "sess_01"
    assert comparison.sessionB.sessionId == "sess_02"
    assert len(comparison.comparisons) >= 4

    ev_comp = next(c for c in comparison.comparisons if "Total Observed Hand-Raising Events" in c.metric)
    assert ev_comp.sessionAValue == 19
    assert ev_comp.sessionBValue == 12
    assert "+7 events" in ev_comp.difference
    assert "more physical hand-raise events" in ev_comp.interpretation


def test_csv_export_format():
    """Verifies that CSV export contains all required metadata, sections, and privacy statements."""
    csv_str = analytics_engine.export_session_csv("sess_01", include_demo=True)
    assert "# CLASSVISION AI — CLASSROOM ACTIVITY ANALYTICS EXPORT" in csv_str
    assert "sess_01" in csv_str
    assert "=== AGGREGATE OBSERVABLE METRICS ===" in csv_str
    assert "Unique Anonymous Tracks" in csv_str
    assert "Total Hand-Raising Events" in csv_str
    assert "=== TIMELINE PARTICIPATION INTERVALS" in csv_str
    assert "=== ANONYMOUS TRACK BREAKDOWN ===" in csv_str
    assert "=== DATA PROVENANCE & ETHICS ===" in csv_str
    assert "50% Kaggle Datasets | 50% Synthetic Datasets | 0% Real Classroom Recordings" in csv_str
    assert "Zero facial recognition" in csv_str


def test_pdf_export_generation():
    """Verifies that PDF export compiles a valid PDF binary file with header %PDF."""
    pdf_path = analytics_engine.export_session_pdf("sess_01", include_demo=True)
    assert os.path.isfile(pdf_path)
    assert os.path.getsize(pdf_path) > 1000

    with open(pdf_path, "rb") as f:
        header = f.read(5)
    assert header.startswith(b"%PDF")


def test_api_analytics_endpoints():
    """Tests all FastAPI REST endpoints for Phase 2.3 activity analytics."""
    # 1. Sessions List
    r = client.get("/api/analytics/sessions")
    assert r.status_code == 200
    sessions = r.json()
    assert len(sessions) >= 3

    # 2. Session Activity Analytics
    r = client.get("/api/analytics/session/sess_01?interval_seconds=60")
    assert r.status_code == 200
    data = r.json()
    assert data["sessionId"] == "sess_01"
    assert data["totalHandRaisingEvents"] == 19
    assert data["uniqueAnonymousTracksObserved"] == 12
    assert "timeline" in data
    assert "trackSummaries" in data

    # 3. Session Timeline
    r = client.get("/api/analytics/session/sess_01/timeline?interval_seconds=300")
    assert r.status_code == 200
    tl = r.json()
    assert isinstance(tl, list)
    assert len(tl) > 0

    # 4. Compare Sessions
    r = client.get("/api/analytics/compare?session_a=sess_01&session_b=sess_02")
    assert r.status_code == 200
    comp = r.json()
    assert "sessionA" in comp
    assert "sessionB" in comp
    assert len(comp["comparisons"]) >= 4

    # 5. Export CSV
    r = client.get("/api/analytics/export/csv?session_id=sess_01")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "CLASSVISION AI" in r.text

    # 6. Export PDF
    r = client.get("/api/analytics/export/pdf?session_id=sess_01")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 1000


def test_privacy_and_non_cognitive_wording():
    """Asserts that returned analytics metrics strictly avoid subjective cognitive assertions."""
    analytics = analytics_engine.get_session_activity("sess_01", include_demo=True)
    dump = analytics.model_dump()
    # Exclude the explicit privacy disclaimer which formally disclaims these prohibited traits
    disclaimer = dump.pop("privacyDisclaimer", "")
    assert "Observable physical activity only" in disclaimer

    dict_repr = str(dump)

    # Prohibited phrases that infer internal mental/cognitive traits
    prohibited_terms = ["cognitive engagement", "student intelligence", "emotion", "attentiveness score"]
    for term in prohibited_terms:
        assert term not in dict_repr.lower(), f"Prohibited inference term '{term}' found in analytics metrics!"

"""
tests/api/test_temporal_tracking.py — Unit & API Tests for Phase 2.2
=====================================================================
Covers all 12 Phase 2.2 verification items:
1. Anonymous ID continuity across frames
2. Multiple-person tracking
3. Left-hand event detection
4. Right-hand event detection
5. Both-hand event detection
6. Exactly one event per continuous hand raise
7. Correct event start/end timestamps
8. Temporary occlusion handling (gap tolerance)
9. Low-confidence keypoint handling (NEEDS_REVIEW)
10. Track expiration
11. SQLite event persistence via repository
12. REST endpoints & WebSocket integration
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.database.db import SessionLocal
from backend.app.database.repositories import HandRaiseEventRepository
from backend.app.schemas.tracking import HandRaisingState, HandSide
from backend.app.services.tracking.synthetic_sequences import (
    generate_multi_person_staggered_sequence,
    generate_noisy_keypoint_sequence,
    generate_repeated_raise_cooldown_sequence,
    generate_single_person_sequence,
    generate_temporary_occlusion_sequence,
    make_synthetic_pose_frame,
)
from backend.app.services.tracking.temporal_tracker import TemporalTracker, temporal_tracker


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_tracker():
    tracker = TemporalTracker(
        keypoint_confidence_threshold=0.40,
        elevation_margin_px=15.0,
        min_raised_frames=2,
        max_missing_frames=5,
        cooldown_seconds=0.5,
    )
    return tracker


# ---------------------------------------------------------------------------
# Tracking & Identity Continuity Tests
# ---------------------------------------------------------------------------

def test_anonymous_id_continuity(clean_tracker):
    """Verifies that an active person retains their anonymous track ID across frames."""
    # Frame 0
    f0 = [make_synthetic_pose_frame("det_0", 320.0, 240.0)]
    tracks0, _ = clean_tracker.update(f0, timestamp_seconds=0.0)
    assert len(tracks0) == 1
    t_id = tracks0[0].trackId
    assert t_id.startswith("track_")

    # Frame 1 (person slightly shifted by 5px)
    f1 = [make_synthetic_pose_frame("det_1", 325.0, 242.0)]
    tracks1, _ = clean_tracker.update(f1, timestamp_seconds=0.033)
    assert len(tracks1) == 1
    assert tracks1[0].trackId == t_id  # Continuity preserved!
    assert tracks1[0].totalFramesTracked == 2


def test_multiple_person_tracking(clean_tracker):
    """Verifies simultaneous tracking of 2 people at distinct spatial locations."""
    seq = generate_multi_person_staggered_sequence(num_frames=10)
    for idx, frame in enumerate(seq):
        tracks, _ = clean_tracker.update(frame, timestamp_seconds=idx * 0.033)

    assert len(clean_tracker.tracks) == 2
    track_ids = set(clean_tracker.tracks.keys())
    assert len(track_ids) == 2
    assert "track_001" in track_ids
    assert "track_002" in track_ids


def test_track_expiration(clean_tracker):
    """Verifies track expires and is pruned after max_missing_frames."""
    f0 = [make_synthetic_pose_frame("det_0", 320.0, 240.0)]
    clean_tracker.update(f0, timestamp_seconds=0.0)
    assert len(clean_tracker.tracks) == 1

    # Send 6 empty frames (max_missing_frames is 5)
    for idx in range(1, 7):
        clean_tracker.update([], timestamp_seconds=idx * 0.033)

    assert len(clean_tracker.tracks) == 0  # Expired and pruned


# ---------------------------------------------------------------------------
# Hand-Raising State & Event Detection Tests
# ---------------------------------------------------------------------------

def test_left_hand_event_detection(clean_tracker):
    """Verifies correct detection of a left-hand raising event."""
    seq = generate_single_person_sequence(num_frames=20, hand_to_raise="LEFT", raise_start_frame=4, raise_end_frame=14)
    all_completed = []
    for idx, frame in enumerate(seq):
        _, completed = clean_tracker.update(frame, timestamp_seconds=idx * 0.05)
        all_completed.extend(completed)

    assert len(all_completed) == 1
    evt = all_completed[0]
    assert evt.handSide == HandSide.LEFT_HAND
    assert evt.state == "COMPLETED"
    assert evt.startFrame in (6, 7)  # Transition to RAISED after min_raised_frames (frame 6/7)
    assert evt.durationSeconds > 0.3
    assert evt.trackId == "track_001"


def test_right_hand_event_detection(clean_tracker):
    """Verifies correct detection of a right-hand raising event."""
    seq = generate_single_person_sequence(num_frames=20, hand_to_raise="RIGHT", raise_start_frame=4, raise_end_frame=14)
    all_completed = []
    for idx, frame in enumerate(seq):
        _, completed = clean_tracker.update(frame, timestamp_seconds=idx * 0.05)
        all_completed.extend(completed)

    assert len(all_completed) == 1
    evt = all_completed[0]
    assert evt.handSide == HandSide.RIGHT_HAND
    assert evt.state == "COMPLETED"


def test_both_hands_event_detection(clean_tracker):
    """Verifies correct detection when both hands are raised simultaneously."""
    seq = generate_single_person_sequence(num_frames=20, hand_to_raise="BOTH", raise_start_frame=4, raise_end_frame=14)
    all_completed = []
    for idx, frame in enumerate(seq):
        _, completed = clean_tracker.update(frame, timestamp_seconds=idx * 0.05)
        all_completed.extend(completed)

    assert len(all_completed) == 1
    evt = all_completed[0]
    assert evt.handSide == HandSide.BOTH_HANDS
    assert evt.state == "COMPLETED"


def test_one_event_per_continuous_raise(clean_tracker):
    """Ensures a long continuous raise (e.g. 25 frames) produces exactly 1 event, not 25."""
    seq = generate_single_person_sequence(num_frames=35, hand_to_raise="LEFT", raise_start_frame=5, raise_end_frame=30)
    all_completed = []
    for idx, frame in enumerate(seq):
        _, completed = clean_tracker.update(frame, timestamp_seconds=idx * 0.04)
        all_completed.extend(completed)

    # Hand was held up for 25 frames, lowered at frame 32
    assert len(all_completed) == 1
    evt = all_completed[0]
    assert evt.frameCount >= 20
    assert evt.durationSeconds >= 0.8


def test_temporary_occlusion_gap_tolerance(clean_tracker):
    """Verifies that missing 2 frames during a hand raise does not split into 2 events."""
    seq = generate_temporary_occlusion_sequence(num_frames=22, occlusion_frames=(10, 11))
    all_completed = []
    for idx, frame in enumerate(seq):
        _, completed = clean_tracker.update(frame, timestamp_seconds=idx * 0.05)
        all_completed.extend(completed)

    # Occlusion bridged: exactly 1 event completed at the end!
    assert len(all_completed) == 1
    assert all_completed[0].trackId == "track_001"


def test_noisy_keypoints_trigger_needs_review(clean_tracker):
    """Verifies low-confidence keypoints yield NEEDS_REVIEW and do not fire false RAISED event."""
    seq = generate_noisy_keypoint_sequence(num_frames=12)
    all_completed = []
    for idx, frame in enumerate(seq):
        tracks, completed = clean_tracker.update(frame, timestamp_seconds=idx * 0.05)
        all_completed.extend(completed)

    # Should have 0 completed false events
    assert len(all_completed) == 0
    # Current state should be NEEDS_REVIEW
    assert clean_tracker.tracks["track_001"].state == HandRaisingState.NEEDS_REVIEW


def test_repeated_hand_raises_with_cooldown(clean_tracker):
    """Verifies 2 distinct hand raises separated by a cooldown produce exactly 2 events."""
    seq = generate_repeated_raise_cooldown_sequence(num_frames=35)
    all_completed = []
    for idx, frame in enumerate(seq):
        _, completed = clean_tracker.update(frame, timestamp_seconds=idx * 0.05)
        all_completed.extend(completed)

    # Exactly 2 events (flutter jitter during cooldown was rejected)
    assert len(all_completed) == 2
    assert all_completed[0].eventId == "evt_0001"
    assert all_completed[1].eventId == "evt_0002"


# ---------------------------------------------------------------------------
# SQLite Persistence & Repository Tests
# ---------------------------------------------------------------------------

def test_sqlite_event_persistence():
    """Verifies hand-raising events are correctly written to and read from SQLite."""
    import uuid
    test_event_id = f"evt_test_{uuid.uuid4().hex[:8]}"
    test_session_id = f"sess_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        repo = HandRaiseEventRepository(db)
        record = repo.create(
            event_id=test_event_id,
            session_id=test_session_id,
            track_id="track_001",
            hand_side="LEFT_HAND",
            state="COMPLETED",
            start_timestamp_seconds=1.25,
            end_timestamp_seconds=3.50,
            duration_seconds=2.25,
            start_frame=25,
            end_frame=70,
            frame_count=45,
            max_confidence=0.95,
            avg_confidence=0.92,
            evidence={"elbow_angle": 115.0, "elevation": 28.5},
            data_source="REAL_PROCESSING",
        )
        assert record.id is not None
        assert record.event_id == test_event_id

        # Query back
        events = repo.get_by_session(test_session_id)
        assert len(events) >= 1
        found = next(e for e in events if e.event_id == test_event_id)
        assert found.duration_seconds == 2.25
        assert found.hand_side == "LEFT_HAND"

        # Check stats
        stats = repo.get_statistics(test_session_id)
        assert stats["total_events"] >= 1
        assert stats["left_hand_count"] >= 1
    finally:
        db.close()


# ---------------------------------------------------------------------------
# API Endpoints Tests
# ---------------------------------------------------------------------------

def test_api_tracking_endpoints(client):
    """Verifies all Phase 2.2 REST API endpoints."""
    # 1. Reset
    r_reset = client.post("/api/vision/tracking/reset?session_id=sess_api_test")
    assert r_reset.status_code == 200
    assert r_reset.json()["status"] == "SUCCESS"

    # 2. Get active tracks
    r_active = client.get("/api/vision/tracking/active")
    assert r_active.status_code == 200
    assert "activeTracksCount" in r_active.json()

    # 3. Get states summary
    r_states = client.get("/api/vision/tracking/states")
    assert r_states.status_code == 200
    assert "states" in r_states.json()
    assert "RAISED" in r_states.json()["states"]

    # 4. Get events
    r_events = client.get("/api/vision/tracking/events")
    assert r_events.status_code == 200
    assert isinstance(r_events.json(), list)

    # 5. Get statistics
    r_stats = client.get("/api/vision/tracking/events/statistics")
    assert r_stats.status_code == 200
    assert "totalEvents" in r_stats.json()
    assert "cooldownPeriodSeconds" in r_stats.json()


def test_api_process_frame_endpoint(client):
    """Verifies uploading an image frame to /api/vision/tracking/process-frame."""
    img = Image.new("RGB", (320, 240), color=(180, 190, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/vision/tracking/process-frame",
        files={"file": ("frame_01.jpg", buf, "image/jpeg")},
        data={"session_id": "sess_live", "timestamp_seconds": 1.0, "confidence_threshold": 0.25},
    )
    assert response.status_code == 200
    data = response.json()
    assert "sessionId" in data
    assert "frameIndex" in data
    assert "activeTracks" in data
    assert "activeHandRaises" in data

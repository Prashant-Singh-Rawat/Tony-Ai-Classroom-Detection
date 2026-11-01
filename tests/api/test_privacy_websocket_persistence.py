"""
tests/api/test_privacy_websocket_persistence.py — Phase 2.8 Verification Tests
=============================================================================
Verifies:
1. Server-side in-memory privacy blur execution in WebSocket frame handler.
2. Client-side blur flag propagation.
3. Automatic SQLite event persistence upon hand-raise completion during WebSocket streaming.
4. Duplicate event prevention on reconnect and idempotency via upsert.
5. Graceful DB exception handling without dropping WebSocket connection.
6. Zero webcam frame persistence to disk or database (volatile RAM only).
7. Session cleanup and db.close() lifecycle.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import uuid
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.core.config import REPO_ROOT
from backend.app.database.db import SessionLocal
from backend.app.database.models import HandRaiseEventRecord
from backend.app.database.repositories import HandRaiseEventRepository
from backend.app.main import app
from backend.app.schemas.detections import PoseDetectionResponse
from backend.app.services.tracking.synthetic_sequences import generate_single_person_sequence
from backend.app.services.tracking.temporal_tracker import temporal_tracker


@pytest.fixture
def client():
    return TestClient(app)


def _make_dummy_frame_b64() -> str:
    """Helper to generate a minimal valid JPEG image in base64 format."""
    img = Image.new("RGB", (64, 64), color=(110, 120, 130))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def test_websocket_server_side_privacy_blur_applied(client):
    """
    Verifies that when serverSideBlur is enabled (default), the WebSocket applies
    in-memory Gaussian blur and reports serverSideBlurApplied=True in metadata.
    """
    b64 = _make_dummy_frame_b64()

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()  # discard initial greeting

        # Frame with serverSideBlur=True
        ws.send_json({
            "type": "frame",
            "frame": b64,
            "detectPose": True,
            "serverSideBlur": True,
            "clientSideBlur": False,
            "sessionId": "sess_privacy_test",
        })
        reply = ws.receive_json()

        assert reply["type"] == "detections"
        assert reply["status"] == "REAL_PROCESSING"
        assert reply["serverSideBlurApplied"] is True
        assert reply["clientSideBlurDetected"] is False
        assert "privacySafeguards" in reply
        safeguards = reply["privacySafeguards"]
        assert safeguards["inMemoryOnly"] is True
        assert safeguards["diskWrites"] == 0
        assert safeguards["databaseFrameWrites"] == 0
        assert safeguards["serverSideBlurring"] is True

        # Frame with serverSideBlur=False
        ws.send_json({
            "type": "frame",
            "frame": b64,
            "detectPose": True,
            "serverSideBlur": False,
            "sessionId": "sess_privacy_test",
        })
        reply2 = ws.receive_json()
        assert reply2["serverSideBlurApplied"] is False


def test_websocket_client_side_blur_detection(client):
    """
    Verifies that clientSideBlur flag sent from frontend is correctly detected,
    distinguished from serverSideBlur, and reflected in response safeguards.
    """
    b64 = _make_dummy_frame_b64()

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()

        ws.send_json({
            "type": "frame",
            "frame": b64,
            "detectPose": True,
            "serverSideBlur": True,
            "clientSideBlur": True,
            "sessionId": "sess_client_blur_test",
        })
        reply = ws.receive_json()

        assert reply["serverSideBlurApplied"] is True
        assert reply["clientSideBlurDetected"] is True
        safeguards = reply["privacySafeguards"]
        assert safeguards["clientSideBlurring"] is True
        assert safeguards["serverSideBlurring"] is True


def test_websocket_session_reset_preserves_history(client):
    """
    Verifies that 'reset' message clears tracker in-memory tracks
    without deleting historical SQLite records.
    """
    test_session_id = f"sess_reset_test_{uuid.uuid4().hex[:6]}"

    # Seed an event directly into DB
    db = SessionLocal()
    try:
        repo = HandRaiseEventRepository(db)
        repo.create(
            event_id=f"evt_pre_{uuid.uuid4().hex[:6]}",
            session_id=test_session_id,
            track_id="track_001",
            hand_side="LEFT_HAND",
            state="COMPLETED",
            start_timestamp_seconds=1.0,
            end_timestamp_seconds=3.0,
            duration_seconds=2.0,
            start_frame=1,
            end_frame=60,
            avg_confidence=0.88,
            evidence={"peakAngleDeg": 135.0},
        )
    finally:
        db.close()

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()

        ws.send_json({
            "type": "reset",
            "sessionId": test_session_id,
        })
        reply = ws.receive_json()
        assert reply["type"] == "status"
        assert reply["status"] == "RESET_COMPLETED"

    # Verify record still exists in SQLite
    db = SessionLocal()
    try:
        events = HandRaiseEventRepository(db).get_by_session(test_session_id)
        assert len(events) >= 1
    finally:
        db.close()


def test_websocket_event_persistence_upon_completion(client):
    """
    Feeds a synthetic sequence simulating NOT_RAISED -> RAISED -> NOT_RAISED
    through WebSocket and verifies the completed event is automatically saved to SQLite.
    """
    test_session_id = f"sess_persist_{uuid.uuid4().hex[:6]}"
    temporal_tracker.reset_session(session_id=test_session_id)

    # 18-frame sequence where left hand is raised from frame 3 to 10
    seq = generate_single_person_sequence(
        num_frames=18,
        hand_to_raise="LEFT",
        raise_start_frame=3,
        raise_end_frame=10,
    )

    b64 = _make_dummy_frame_b64()

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()  # Greeting

        for frame_idx, person_detections in enumerate(seq):
            mock_pose_res = PoseDetectionResponse(
                totalPersons=len(person_detections),
                imageWidth=640,
                imageHeight=480,
                processingTimeMs=25.0,
                processingFps=40.0,
                modelName="yolov8n-pose",
                modelStatus="READY",
                inferenceDevice="cpu",
                persons=person_detections,
            )

            with patch("backend.app.api.routes.websocket.cv_service.estimate_pose", return_value=mock_pose_res):
                ws.send_json({
                    "type": "frame",
                    "frame": b64,
                    "detectPose": True,
                    "serverSideBlur": True,
                    "clientSideBlur": True,
                    "sessionId": test_session_id,
                })
                reply = ws.receive_json()
                assert reply["type"] == "detections"
                assert reply["status"] == "REAL_PROCESSING"

        # Final message should indicate saved/connected status
        assert reply["persistedEventsCount"] >= 1
        assert reply["dbPersistenceStatus"] in ("SAVED", "CONNECTED")

    # Verify in SQLite database via HandRaiseEventRepository
    db = SessionLocal()
    try:
        repo = HandRaiseEventRepository(db)
        db_events = repo.get_by_session(test_session_id)
        assert len(db_events) >= 1
        persisted_evt = db_events[0]
        assert persisted_evt.session_id == test_session_id
        assert persisted_evt.track_id == "track_001"
        assert persisted_evt.hand_side in ("LEFT", "LEFT_HAND")
        assert persisted_evt.state == "COMPLETED"
        assert persisted_evt.duration_seconds > 0.0
    finally:
        db.close()


def test_websocket_reconnection_idempotency_no_duplicates(client):
    """
    Verifies that sending multiple frame cycles or reconnecting to WebSocket
    with the same session ID does not create duplicate rows in SQLite (upsert idempotency).
    """
    test_session_id = f"sess_idemp_{uuid.uuid4().hex[:6]}"
    temporal_tracker.reset_session(session_id=test_session_id)

    seq = generate_single_person_sequence(
        num_frames=16,
        hand_to_raise="RIGHT",
        raise_start_frame=3,
        raise_end_frame=8,
    )
    b64 = _make_dummy_frame_b64()

    # Session 1: Run sequence to completion
    with client.websocket_connect("/api/ws/detections") as ws1:
        _ = ws1.receive_json()
        for person_detections in seq:
            mock_pose = PoseDetectionResponse(
                totalPersons=len(person_detections),
                persons=person_detections,
            )
            with patch("backend.app.api.routes.websocket.cv_service.estimate_pose", return_value=mock_pose):
                ws1.send_json({
                    "type": "frame",
                    "frame": b64,
                    "detectPose": True,
                    "sessionId": test_session_id,
                })
                _ = ws1.receive_json()

    # Verify event count is 1
    db = SessionLocal()
    try:
        repo = HandRaiseEventRepository(db)
        events_after_sess1 = repo.get_by_session(test_session_id)
        count_sess1 = len(events_after_sess1)
        assert count_sess1 == 1

        # Session 2: Reconnect with same session and run stationary non-raise frames
        with client.websocket_connect("/api/ws/detections") as ws2:
            _ = ws2.receive_json()
            for person_detections in seq[:3]:  # NOT_RAISED frames only
                mock_pose = PoseDetectionResponse(
                    totalPersons=len(person_detections),
                    persons=person_detections,
                )
                with patch("backend.app.api.routes.websocket.cv_service.estimate_pose", return_value=mock_pose):
                    ws2.send_json({
                        "type": "frame",
                        "frame": b64,
                        "detectPose": True,
                        "sessionId": test_session_id,
                    })
                    _ = ws2.receive_json()

        # Event count must remain exactly 1 (no duplicate rows created)
        events_after_sess2 = repo.get_by_session(test_session_id)
        assert len(events_after_sess2) == count_sess1
    finally:
        db.close()


def test_websocket_db_error_resilience(client):
    """
    Verifies that a database failure does NOT terminate or crash the WebSocket connection.
    The socket remains open and gracefully returns error status in dbPersistenceStatus.
    """
    b64 = _make_dummy_frame_b64()

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()

        # Patch SessionLocal to simulate a database session failure
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Simulated SQLite Disk I/O lock")

        with patch("backend.app.api.routes.websocket.SessionLocal", return_value=mock_db):
            ws.send_json({
                "type": "frame",
                "frame": b64,
                "detectPose": True,
                "serverSideBlur": True,
                "sessionId": "sess_db_err_test",
            })
            reply = ws.receive_json()

            # WebSocket connection was preserved and delivered valid detection response
            assert reply["type"] == "detections"
            assert reply["dbPersistenceStatus"] == "ERROR"
            assert "Simulated SQLite Disk I/O lock" in (reply.get("dbErrorMessage") or "")
            mock_db.close.assert_called_once()


def test_zero_webcam_disk_writes_guarantee(client):
    """
    Verifies that running WebSocket webcam frame processing creates 0 image/video files on disk.
    Frames remain strictly volatile in RAM.
    """
    # Count initial image/video files in project
    exts = ("*.jpg", "*.jpeg", "*.png", "*.mp4", "*.avi")
    initial_files = set()
    for ext in exts:
        for p in REPO_ROOT.glob(ext):
            initial_files.add(str(p))

    b64 = _make_dummy_frame_b64()

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()
        for _ in range(5):
            ws.send_json({
                "type": "frame",
                "frame": b64,
                "detectPose": True,
                "serverSideBlur": True,
                "clientSideBlur": True,
                "sessionId": "sess_zero_disk",
            })
            reply = ws.receive_json()
            assert reply["status"] == "REAL_PROCESSING"

    # Verify no new image/video files were written to project root
    current_files = set()
    for ext in exts:
        for p in REPO_ROOT.glob(ext):
            current_files.add(str(p))

    new_files = current_files - initial_files
    assert len(new_files) == 0, f"Prohibited frame files detected on disk: {new_files}"

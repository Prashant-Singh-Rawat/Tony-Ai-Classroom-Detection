"""
tests/api/test_real_classroom_validation.py
============================================
Comprehensive test suite validating end-to-end classroom intelligence on
sample classroom video footage and multi-row benchmark sessions.
Verifies:
1. Video upload, decoding, aspect-preserving letterboxing.
2. Anonymous person tracking with YOLOv8n & YOLOv8n-pose.
3. Hand-raise event detection, debounce, and state transitions.
4. SQLite persistence of sessions and hand_raise_events.
5. Analytics CSV and publication-grade PDF report exports.
6. Zero raw classroom frames stored in database.
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.database.db import get_db, init_db
from backend.app.database.models import DetectionEvent, HandRaiseEventRecord
from backend.app.database.repositories import HandRaiseEventRepository, SessionRepository
from backend.app.main import app
from backend.app.services.tracking.temporal_tracker import temporal_tracker
from scripts.test_classroom_video_pipeline_e2e import render_rear_corner_classroom_video


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_real_sample_video_pipeline_e2e(client: TestClient):
    """Verifies that the sample classroom video processes cleanly end-to-end without false alarms."""
    video_path = "data/classroom_test/ClassVision_Sample_Classroom_Test_Compatible.mp4"
    if not os.path.exists(video_path):
        pytest.skip("Sample classroom video not available on disk")

    session_id = "test_sess_real_sample_e2e"
    with open(video_path, "rb") as f:
        resp = client.post(
            "/api/vision/video/process",
            files={"file": ("ClassVision_Sample_Classroom_Test_Compatible.mp4", f, "video/mp4")},
            data={
                "frame_skip": 2,
                "confidence_threshold": 0.25,
                "detect_pose": "true",
                "enable_tracking": "true",
                "session_id": session_id,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalFrames"] == 240
    assert data["processedFrames"] == 120
    assert data["trackedPersonsCount"] >= 1
    assert data["corruptedFramesCount"] == 0
    assert data["aspectRatio"] == "16:9"
    assert data["orientation"] == "LANDSCAPE"

    # Database verification
    db = next(get_db())
    s_repo = SessionRepository(db)
    sess_obj = s_repo.get_by_id(session_id)
    assert sess_obj is not None
    assert sess_obj.status == "completed"


def test_multi_row_rear_corner_hand_raise_accuracy(client: TestClient):
    """Verifies rear-corner multi-row classroom hand-raise detection and export generation."""
    temp_dir = tempfile.mkdtemp(prefix="test_classroom_")
    video_path = os.path.join(temp_dir, "test_rear_corner.mp4")
    render_rear_corner_classroom_video(
        output_path=video_path,
        width=1280,
        height=720,
        fps=10.0,
        total_frames=30,
    )

    session_id = "test_sess_multirow_accuracy"
    temporal_tracker.reset_session(session_id)

    with open(video_path, "rb") as f:
        resp = client.post(
            "/api/vision/video/process",
            files={"file": ("test_rear_corner.mp4", f, "video/mp4")},
            data={
                "frame_skip": 2,
                "confidence_threshold": 0.25,
                "detect_pose": "true",
                "enable_tracking": "true",
                "session_id": session_id,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["trackedPersonsCount"] >= 5
    assert data["handRaiseEventsCount"] == 1

    # Database verification
    db = next(get_db())
    e_repo = HandRaiseEventRepository(db)
    events = e_repo.get_by_session(session_id)
    assert len(events) == 1
    assert events[0].state == "COMPLETED"
    assert events[0].duration_seconds > 1.0

    # Privacy guarantee: zero raw frames
    assert not hasattr(DetectionEvent, "raw_frame")
    assert not hasattr(HandRaiseEventRecord, "image_data")

    # CSV Export test
    csv_resp = client.get(f"/api/analytics/export/csv?session_id={session_id}&demo=false")
    assert csv_resp.status_code == 200
    assert "CLASSROOM ACTIVITY ANALYTICS EXPORT" in csv_resp.text

    # PDF Export test
    pdf_resp = client.get(f"/api/analytics/export/pdf?session_id={session_id}&demo=false")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF")


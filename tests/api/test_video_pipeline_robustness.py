"""
tests/api/test_video_pipeline_robustness.py
===========================================
Comprehensive unit and integration tests for ClassVision AI Video Processing Pipeline:
1. Multi-resolution video upload & metadata extraction (landscape & portrait).
2. Aspect-ratio preservation via letterbox (no distortion).
3. Frame decoding FPS vs. AI inference FPS separation.
4. YOLOv8n-pose video processing with hand-raise & NEEDS_REVIEW classification.
5. Resilient corrupt / truncated frame handling (zero crashes).
"""

from __future__ import annotations

import io
import os
import tempfile
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.computer_vision import cv_service
from backend.app.services.computer_vision.letterbox import (
    compute_aspect_ratio_string,
    letterbox_image,
    scale_boxes_to_original,
    scale_keypoints_to_original,
)


@pytest.fixture
def client():
    return TestClient(app)


def create_synthetic_video_bytes(
    width: int = 320,
    height: int = 240,
    num_frames: int = 10,
    fps: float = 10.0,
) -> bytes:
    """Creates an in-memory MP4 video."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_name = tmp.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(tmp_name, fourcc, fps, (width, height))
        for _ in range(num_frames):
            frame = np.full((height, width, 3), 150, dtype=np.uint8)
            cv2.rectangle(frame, (int(width * 0.2), int(height * 0.2)), (int(width * 0.8), int(height * 0.8)), (50, 100, 200), -1)
            out.write(frame)
        out.release()

        with open(tmp_name, "rb") as f:
            data = f.read()
        return data
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


# -----------------------------------------------------------------------------
# 1. Aspect Ratio & Letterbox Tests
# -----------------------------------------------------------------------------

def test_compute_aspect_ratio_string():
    assert compute_aspect_ratio_string(1920, 1080) == "16:9"
    assert compute_aspect_ratio_string(1280, 720) == "16:9"
    assert compute_aspect_ratio_string(640, 480) == "4:3"
    assert compute_aspect_ratio_string(320, 240) == "4:3"
    assert compute_aspect_ratio_string(1080, 1920) == "9:16"
    assert compute_aspect_ratio_string(720, 1280) == "9:16"
    assert compute_aspect_ratio_string(500, 500) == "1:1"


def test_letterbox_preserves_aspect_ratio_landscape():
    img = np.full((720, 1280, 3), 100, dtype=np.uint8)
    boxed, ratio, (pad_w, pad_h) = letterbox_image(img, target_shape=(640, 640), auto=False, color=(114, 114, 114))

    assert boxed.shape == (640, 640, 3)
    assert ratio == 640 / 1280  # 0.5
    assert pad_w == 0.0  # Full width utilized
    assert pad_h == float((640 - (720 * 0.5)) / 2)  # 140 top/bottom padding
    # Check that neutral border color is 114
    assert np.all(boxed[0:10, 0:10] == 114)


def test_letterbox_preserves_aspect_ratio_portrait():
    img = np.full((1920, 1080, 3), 100, dtype=np.uint8)
    boxed, ratio, (pad_w, pad_h) = letterbox_image(img, target_shape=(640, 640), auto=False, color=(114, 114, 114))

    assert boxed.shape == (640, 640, 3)
    assert ratio == 640 / 1920
    assert pad_h == 0.0  # Full height utilized
    assert pad_w > 0  # Left/right padding applied
    assert np.all(boxed[0:10, 0:10] == 114)


def test_scale_boxes_and_keypoints_to_original():
    orig_shape = (1080, 1920)
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    _, ratio, (pad_w, pad_h) = letterbox_image(img, target_shape=(640, 640), auto=False)

    # Mock box in letterboxed coordinates
    mock_boxes = np.array([[pad_w + 10, pad_h + 10, pad_w + 100, pad_h + 100]])
    scaled_boxes = scale_boxes_to_original(mock_boxes, scale_ratio=ratio, padding=(pad_w, pad_h), original_shape=orig_shape)

    # Box coordinates must be close to 10/ratio and 100/ratio in original space
    assert scaled_boxes.shape == (1, 4)
    assert np.isclose(scaled_boxes[0, 0], 10.0 / ratio, atol=1.0)
    assert np.isclose(scaled_boxes[0, 1], 10.0 / ratio, atol=1.0)

    # Mock keypoints in letterboxed space
    mock_kpts = np.array([[[pad_w + 20, pad_h + 20, 0.9]]])
    scaled_kpts = scale_keypoints_to_original(mock_kpts, scale_ratio=ratio, padding=(pad_w, pad_h), original_shape=orig_shape)
    assert scaled_kpts.shape == (1, 1, 3)
    assert np.isclose(scaled_kpts[0, 0, 0], 20.0 / ratio, atol=1.0)
    assert scaled_kpts[0, 0, 2] == 0.9  # Confidence preserved


# -----------------------------------------------------------------------------
# 2. Video API & Multi-Resolution Metadata Tests
# -----------------------------------------------------------------------------

def test_api_video_process_multi_resolution_landscape(client):
    vid_bytes = create_synthetic_video_bytes(width=640, height=360, num_frames=8)

    response = client.post(
        "/api/vision/video/process",
        files={"file": ("classroom_nhd.mp4", io.BytesIO(vid_bytes), "video/mp4")},
        data={"frame_skip": 2, "confidence_threshold": 0.25, "detect_pose": False},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["width"] == 640
    assert data["height"] == 360
    assert data["aspectRatio"] == "16:9"
    assert data["orientation"] == "LANDSCAPE"
    assert data["totalFrames"] == 8
    assert data["processedFrames"] == 4
    assert data["modelName"] == "yolov8n"
    assert "decodingFps" in data
    assert "inferenceFps" in data
    assert data["decodingFps"] > 0
    assert data["inferenceFps"] > 0
    assert "peakRamMb" in data
    assert data["peakRamMb"] > 0
    assert data["corruptedFramesCount"] == 0


def test_api_video_process_portrait(client):
    vid_bytes = create_synthetic_video_bytes(width=360, height=640, num_frames=6)

    response = client.post(
        "/api/vision/video/process",
        files={"file": ("phone_record_portrait.mp4", io.BytesIO(vid_bytes), "video/mp4")},
        data={"frame_skip": 2, "confidence_threshold": 0.25, "detect_pose": False},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["width"] == 360
    assert data["height"] == 640
    assert data["aspectRatio"] == "9:16"
    assert data["orientation"] == "PORTRAIT"


def test_api_video_process_with_pose_detection(client):
    vid_bytes = create_synthetic_video_bytes(width=320, height=240, num_frames=6)

    response = client.post(
        "/api/vision/video/process",
        files={"file": ("pose_test.mp4", io.BytesIO(vid_bytes), "video/mp4")},
        data={"frame_skip": 2, "confidence_threshold": 0.25, "detect_pose": True, "enable_tracking": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["modelName"] == "yolov8n-pose"
    assert "totalHandRaises" in data
    assert "totalNeedsReview" in data
    assert "trackedPersonsCount" in data
    assert "handRaiseEventsCount" in data
    assert isinstance(data["totalHandRaises"], int)
    assert isinstance(data["totalNeedsReview"], int)
    assert isinstance(data["trackedPersonsCount"], int)
    assert isinstance(data["handRaiseEventsCount"], int)


def test_api_video_upload_size_limit_rejected(client):
    """Verifies that an oversized file payload exceeding 500 MB returns 413 Payload Too Large."""
    from unittest.mock import AsyncMock, patch
    with patch("starlette.datastructures.UploadFile.read", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = b"x" * (501 * 1024 * 1024)
        response = client.post(
            "/api/vision/video/process",
            files={"file": ("huge_recording.mp4", io.BytesIO(b"dummy"), "video/mp4")},
        )
        assert response.status_code == 413
        assert "exceeds maximum allowed size" in response.json()["detail"]


# -----------------------------------------------------------------------------
# 3. Corrupted / Truncated Stream Resilience Tests
# -----------------------------------------------------------------------------

def test_corrupted_stream_handled_without_crash():
    with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp:
        path = tmp.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        out = cv2.VideoWriter(path, fourcc, 10.0, (160, 120))
        for _ in range(15):
            out.write(np.full((120, 160, 3), 100, dtype=np.uint8))
        out.release()

        # Truncate to simulate dropped / incomplete packets
        size = os.path.getsize(path)
        with open(path, "r+b") as f:
            f.truncate(int(size * 0.70))

        # Must process gracefully without unhandled exception
        res = cv_service.process_video_stream(path, frame_skip=1, confidence_threshold=0.25)
        assert res.totalFrames == 15
        assert res.corruptedFramesCount > 0
        assert res.processedFrames > 0
        assert res.status == "COMPLETED"
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

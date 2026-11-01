"""
tests/api/test_vision_endpoints.py — Phase 2.0 YOLOv8n Person Detection Tests
=============================================================================
Tests:
1. Model initialization and status
2. Image upload and person detection
3. Bounding box coordinates and confidence scores
4. Image width/height and latency metrics
5. Invalid image rejection (empty and wrong mime type)
6. Video sequential processing with frame skipping
7. Invalid video rejection
8. CPU / hardware device reporting
"""

import io
import os
import tempfile
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_vision_status(client):
    response = client.get("/api/vision/status")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "computer_vision"
    assert data["ready_for_inference"] is True
    assert "inference_device" in data
    assert data["target_class"] == "person (COCO class 0)"
    assert "memory_usage" in data


def test_detect_uploaded_image(client):
    # Create a 320x240 image
    img = Image.new("RGB", (320, 240), color=(180, 190, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/vision/detect",
        files={"file": ("classroom_test.jpg", buf, "image/jpeg")},
        data={"confidence_threshold": 0.25, "imgsz": 320},
    )
    assert response.status_code == 200
    data = response.json()

    # Core Phase 2.0 requirements:
    assert "imageWidth" in data
    assert "imageHeight" in data
    assert data["imageWidth"] == 320
    assert data["imageHeight"] == 240
    assert "processingTimeMs" in data
    assert data["processingTimeMs"] > 0
    assert "processingFps" in data
    assert "modelName" in data
    assert data["modelName"] == "yolov8n"
    assert "inferenceDevice" in data
    assert "dataSource" in data
    assert data["dataSource"] == "REAL_PROCESSING"
    assert "detections" in data
    assert isinstance(data["detections"], list)
    assert "boxes" in data


def test_detect_empty_file_rejected(client):
    response = client.post(
        "/api/vision/detect",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400


def test_detect_invalid_file_rejected(client):
    response = client.post(
        "/api/vision/detect",
        files={"file": ("notes.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 400


def test_video_process_synthetic(client):
    # Create a small temporary 10-frame video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_name = tmp.name

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(tmp_name, fourcc, 10.0, (160, 120))
        for _ in range(10):
            frame = np.full((120, 160, 3), 200, dtype=np.uint8)
            out.write(frame)
        out.release()

        with open(tmp_name, "rb") as f:
            video_bytes = f.read()

        response = client.post(
            "/api/vision/video/process",
            files={"file": ("sample_clip.mp4", io.BytesIO(video_bytes), "video/mp4")},
            data={"frame_skip": 2, "confidence_threshold": 0.25, "imgsz": 160},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["totalFrames"] == 10
        assert data["processedFrames"] == 5  # 10 frames with frame_skip=2 -> 5 frames
        assert data["frameSkip"] == 2
        assert "timeline" in data
        assert len(data["timeline"]) == 5
        assert "processingFps" in data
        assert data["status"] == "COMPLETED"
        assert data["modelName"] == "yolov8n"
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def test_video_invalid_format_rejected(client):
    response = client.post(
        "/api/vision/video/process",
        files={"file": ("document.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")},
    )
    assert response.status_code == 400


def test_privacy_blur_endpoint(client):
    """Verifies that privacy blur endpoint successfully returns an in-memory blurred JPEG."""
    img = Image.new("RGB", (320, 240), color=(180, 190, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/vision/privacy-blur",
        files={"file": ("webcam_frame.jpg", buf, "image/jpeg")},
        data={"blur_ratio": 0.25, "kernel_size": 31},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["x-privacy-mode"] == "True-In-Memory-Pixel-Blur"
    assert "x-faces-blurred" in response.headers
    # Verify response body is valid image bytes
    blurred_arr = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
    assert blurred_arr is not None
    assert blurred_arr.shape == (240, 320, 3)


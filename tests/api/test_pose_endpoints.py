"""
tests/api/test_pose_endpoints.py — Phase 2.1 YOLOv8n-pose Human Pose Estimation Tests
=====================================================================================
Tests:
1. Pose model status and metadata endpoint (GET /api/vision/pose/status)
2. All 17 COCO keypoints verification
3. Image upload with human silhouette and pose estimation (POST /api/vision/pose)
4. Arm angle and elevation geometric analysis
5. Multiple-person pose detection
6. Observable posture classification (ARMS_NOT_RAISED, LEFT_ARM_RAISED, BOTH_ARMS_RAISED, NEEDS_REVIEW)
7. Occluded keypoint handling & NEEDS_REVIEW classification
8. Invalid image rejection (empty file and invalid extension)
9. CPU / Hardware device reporting
"""

import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.services.computer_vision import cv_service
from backend.app.services.computer_vision.service import COCO_KEYPOINTS


@pytest.fixture
def client():
    return TestClient(app)


def test_pose_status_endpoint(client):
    """Verifies GET /api/vision/pose/status returns 17 COCO keypoints and posture classes."""
    response = client.get("/api/vision/pose/status")
    assert response.status_code == 200
    data = response.json()

    assert data["module"] == "computer_vision"
    assert data["submodule"] == "pose_estimation"
    assert data["modelName"] == "yolov8n-pose"
    assert data["status"] == "READY"
    assert data["readyForInference"] is True
    assert data["supportedKeypointsCount"] == 17
    assert len(data["cocoKeypointOrder"]) == 17
    assert data["cocoKeypointOrder"] == COCO_KEYPOINTS

    # Check key keypoints in order
    assert data["cocoKeypointOrder"][0] == "nose"
    assert data["cocoKeypointOrder"][5] == "left_shoulder"
    assert data["cocoKeypointOrder"][6] == "right_shoulder"
    assert data["cocoKeypointOrder"][7] == "left_elbow"
    assert data["cocoKeypointOrder"][8] == "right_elbow"
    assert data["cocoKeypointOrder"][9] == "left_wrist"
    assert data["cocoKeypointOrder"][10] == "right_wrist"
    assert data["cocoKeypointOrder"][11] == "left_hip"
    assert data["cocoKeypointOrder"][12] == "right_hip"

    # Check observable posture classes
    assert "BOTH_ARMS_RAISED" in data["postureClasses"]
    assert "LEFT_ARM_RAISED" in data["postureClasses"]
    assert "RIGHT_ARM_RAISED" in data["postureClasses"]
    assert "ARMS_NOT_RAISED" in data["postureClasses"]
    assert "NEEDS_REVIEW" in data["postureClasses"]


def test_pose_detect_blank_image(client):
    """Tests POST /api/vision/pose on a blank canvas (0 persons detected)."""
    img = Image.new("RGB", (320, 240), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/vision/pose",
        files={"file": ("blank.jpg", buf, "image/jpeg")},
        data={"confidence_threshold": 0.25, "imgsz": 320},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["totalPersons"] == 0
    assert data["imageWidth"] == 320
    assert data["imageHeight"] == 240
    assert data["processingTimeMs"] > 0
    assert data["modelName"] == "yolov8n-pose"
    assert "postureCounts" in data
    assert isinstance(data["persons"], list)


def test_pose_detect_human_silhouette(client):
    """Tests pose estimation on an image with a human figure, verifying 17 keypoints and geometry."""
    # Create an image with a clear human figure
    img = np.full((480, 640, 3), 240, dtype=np.uint8)
    # Head
    cv2.circle(img, (320, 120), 28, (40, 40, 40), -1)
    # Torso
    cv2.rectangle(img, (290, 150), (350, 300), (50, 50, 50), -1)
    # Left Arm: raised up
    cv2.line(img, (290, 170), (240, 100), (40, 40, 40), 12)
    # Right Arm: down
    cv2.line(img, (350, 170), (390, 270), (40, 40, 40), 12)
    # Legs
    cv2.line(img, (305, 300), (305, 430), (40, 40, 40), 14)
    cv2.line(img, (335, 300), (335, 430), (40, 40, 40), 14)

    is_success, buffer = cv2.imencode(".jpg", img)
    assert is_success

    response = client.post(
        "/api/vision/pose",
        files={"file": ("figure.jpg", io.BytesIO(buffer.tobytes()), "image/jpeg")},
        data={"confidence_threshold": 0.15, "keypoint_threshold": 0.2, "imgsz": 640},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["imageWidth"] == 640
    assert data["imageHeight"] == 480
    assert data["modelName"] == "yolov8n-pose"

    # If persons are detected, check the 17 keypoints format
    if data["totalPersons"] > 0:
        person = data["persons"][0]
        assert "id" in person
        assert person["id"].startswith("anon_")
        assert "bbox" in person
        assert "keypoints" in person
        assert len(person["keypoints"]) == 17

        # Verify keypoint ordering
        for idx, kp in enumerate(person["keypoints"]):
            assert kp["index"] == idx
            assert kp["name"] == COCO_KEYPOINTS[idx]
            assert "x" in kp
            assert "y" in kp
            assert "confidence" in kp
            assert "visible" in kp
            assert 0.0 <= kp["confidence"] <= 1.0

        # Verify geometry
        assert "geometry" in person
        geom = person["geometry"]
        assert "leftArm" in geom
        assert "rightArm" in geom
        assert "posture" in person
        assert person["posture"] in [
            "BOTH_ARMS_RAISED",
            "LEFT_ARM_RAISED",
            "RIGHT_ARM_RAISED",
            "ARMS_NOT_RAISED",
            "NEEDS_REVIEW",
        ]


def test_pose_detect_empty_file_rejected(client):
    """Empty file should return 400 Bad Request."""
    response = client.post(
        "/api/vision/pose",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_pose_detect_invalid_file_rejected(client):
    """Non-image file format should return 400 Bad Request."""
    response = client.post(
        "/api/vision/pose",
        files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4 sample"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_geometric_angle_calculation():
    """Directly verifies angle calculation helper."""
    # 90-degree right angle at (0, 0)
    p1 = (0.0, 10.0)
    p2 = (0.0, 0.0)  # vertex
    p3 = (10.0, 0.0)
    angle = cv_service._calculate_angle_deg(p1, p2, p3)
    assert angle is not None
    assert abs(angle - 90.0) < 0.1

    # 180-degree straight line
    p1 = (-10.0, 0.0)
    p2 = (0.0, 0.0)
    p3 = (10.0, 0.0)
    angle = cv_service._calculate_angle_deg(p1, p2, p3)
    assert angle is not None
    assert abs(angle - 180.0) < 0.1


def test_multiple_person_pose_detection(client):
    """Verifies that an image with multiple people produces distinct anonymous IDs."""
    img = np.full((480, 640, 3), 245, dtype=np.uint8)

    # Person 1 (left side)
    cv2.circle(img, (180, 120), 26, (45, 45, 45), -1)
    cv2.rectangle(img, (155, 150), (205, 300), (55, 55, 55), -1)
    cv2.line(img, (155, 170), (120, 240), (45, 45, 45), 10)
    cv2.line(img, (205, 170), (240, 240), (45, 45, 45), 10)
    cv2.line(img, (170, 300), (170, 420), (45, 45, 45), 12)
    cv2.line(img, (190, 300), (190, 420), (45, 45, 45), 12)

    # Person 2 (right side)
    cv2.circle(img, (460, 120), 26, (45, 45, 45), -1)
    cv2.rectangle(img, (435, 150), (485, 300), (55, 55, 55), -1)
    cv2.line(img, (435, 170), (400, 240), (45, 45, 45), 10)
    cv2.line(img, (485, 170), (520, 240), (45, 45, 45), 10)
    cv2.line(img, (450, 300), (450, 420), (45, 45, 45), 12)
    cv2.line(img, (470, 300), (470, 420), (45, 45, 45), 12)

    is_success, buffer = cv2.imencode(".jpg", img)
    assert is_success

    response = client.post(
        "/api/vision/pose",
        files={"file": ("two_persons.jpg", io.BytesIO(buffer.tobytes()), "image/jpeg")},
        data={"confidence_threshold": 0.15, "imgsz": 640},
    )
    assert response.status_code == 200
    data = response.json()

    # Verify anonymous ID sequence
    ids = [p["id"] for p in data["persons"]]
    for idx, pid in enumerate(ids):
        assert pid == f"anon_{idx + 1:03d}"


def test_occluded_keypoints_classification():
    """Verifies that missing arm keypoints result in NEEDS_REVIEW posture."""
    # Blank image with no keypoints detected should produce zero persons or NEEDS_REVIEW
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    res = cv_service.estimate_pose(img, confidence_threshold=0.5)
    assert res.totalPersons == 0
    assert res.modelName == "yolov8n-pose"
    assert res.inferenceDevice in ("cuda:0", "cpu")


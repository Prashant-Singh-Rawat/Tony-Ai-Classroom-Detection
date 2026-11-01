"""
tests/api/test_dataset_integration_and_models.py
=================================================
Verifies:
1. Multi-model registry endpoint (GET /api/model/registry).
2. Dataset inventory & split manifest endpoints.
3. Sign Language MNIST status & inference endpoints.
4. 20-Class Hand Gesture status & inference endpoints.
5. CommonLit Student Summary Scoring status & prediction endpoints.
6. Ethical boundary guarantees (isolated ASL, unmapped gestures, no student IQ scoring).
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_model_registry_endpoint(client):
    """Verifies GET /api/model/registry returns all 8 registered multimodal models."""
    response = client.get("/api/model/registry")
    assert response.status_code == 200
    data = response.json()

    assert "models" in data
    assert len(data["models"]) >= 8
    model_ids = [m["id"] for m in data["models"]]

    assert "model_yolov8n_person" in model_ids
    assert "model_yolov8n_pose" in model_ids
    assert "model_faster_whisper" in model_ids
    assert "model_easyocr_whiteboard" in model_ids
    assert "model_character_cnn_62" in model_ids
    assert "model_sign_language_cnn" in model_ids
    assert "model_hand_gesture_cnn" in model_ids
    assert "model_summary_scoring_regressor" in model_ids


def test_dataset_inventory_endpoint(client):
    """Verifies GET /api/datasets/inventory honestly reports acquired and missing datasets."""
    response = client.get("/api/datasets/inventory")
    assert response.status_code == 200
    data = response.json()

    assert "inventory" in data
    names = [d["name"] for d in data["inventory"]]

    assert "English Character Recognition" in names
    assert "Sign Language MNIST" in names
    assert "Hand Gesture Recognition" in names
    assert "CommonLit Student Summaries" in names
    assert "Human Detection Dataset" in names

    # Verify honest reporting of missing dataset
    human_ds = next(d for d in data["inventory"] if d["name"] == "Human Detection Dataset")
    assert human_ds["status"] == "MISSING_NOT_DOWNLOADED"
    assert human_ds["samples"] == 0


def test_dataset_splits_endpoint(client):
    """Verifies GET /api/datasets/splits returns split manifests for all compatible datasets."""
    response = client.get("/api/datasets/splits")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "READY"
    manifests = data["manifests"]
    assert "english_character_recognition" in manifests
    assert "sign_language_mnist" in manifests
    assert "hand_gesture" in manifests
    assert "commonlit_summaries" in manifests
    assert "common_voice" in manifests
    assert "coco_keypoints" in manifests


def test_sign_language_status_and_predict(client):
    """Verifies Sign Language MNIST model status and prediction."""
    # Status
    status_resp = client.get("/api/vision/sign-language/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["module"] == "sign_language_mnist"
    assert status_data["status"] == "READY"
    assert status_data["numClasses"] == 24

    # Predict with in-memory 28x28 grayscale image
    img = Image.new("L", (28, 28), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    pred_resp = client.post(
        "/api/vision/sign-language/predict",
        files={"file": ("sign.png", buf, "image/png")},
    )
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()

    assert pred_data["status"] == "SUCCESS"
    assert "predictedLetter" in pred_data
    assert "confidence" in pred_data
    assert len(pred_data["top3Predictions"]) == 3
    assert "strictly NOT connected" in pred_data["boundaryIsolation"]


def test_hand_gesture_status_and_predict(client):
    """Verifies 20-class Hand Gesture model status and prediction."""
    # Status
    status_resp = client.get("/api/vision/gesture/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["module"] == "hand_gesture_recognition"
    assert status_data["status"] == "READY"
    assert status_data["numClasses"] == 20

    # Predict with in-memory 50x50 grayscale image
    img = Image.new("L", (50, 50), color=200)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    pred_resp = client.post(
        "/api/vision/gesture/predict",
        files={"file": ("gesture.jpg", buf, "image/jpeg")},
    )
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()

    assert pred_data["status"] == "SUCCESS"
    assert "predictedClass" in pred_data
    assert "confidence" in pred_data
    assert len(pred_data["top3Predictions"]) == 3
    assert "not mapped to classroom" in pred_data["boundaryIsolation"].lower() or "unmapped" in pred_data["boundaryIsolation"].lower()


def test_summary_scoring_status_and_predict(client):
    """Verifies CommonLit summary scoring model status and regression inference."""
    # Status
    status_resp = client.get("/api/intelligence/summary-score/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["module"] == "student_summary_scoring"
    assert status_data["status"] == "READY"
    assert status_data["targetMetrics"] == ["content", "wording"]

    # Predict with sample student summary
    sample_text = (
        "In this chapter, the protagonist realizes that true strength comes from cooperation "
        "rather than isolated competition. The author uses vivid metaphors of the ocean to depict "
        "the turbulent emotional journey."
    )
    pred_resp = client.post(
        "/api/intelligence/summary-score/predict",
        json={"summaryText": sample_text},
    )
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()

    assert pred_data["status"] == "SUCCESS"
    assert "contentScore" in pred_data
    assert "wordingScore" in pred_data
    assert "overallQualityScore" in pred_data
    assert isinstance(pred_data["contentScore"], float)
    assert isinstance(pred_data["wordingScore"], float)
    assert "NEVER student intelligence" in pred_data["ethicalBoundary"]


def test_summary_scoring_empty_text_rejected(client):
    """Verifies empty summary text is rejected with 400 Bad Request."""
    pred_resp = client.post(
        "/api/intelligence/summary-score/predict",
        json={"summaryText": "   "},
    )
    assert pred_resp.status_code == 400

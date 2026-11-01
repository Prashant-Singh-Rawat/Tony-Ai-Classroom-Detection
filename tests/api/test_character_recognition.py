"""
tests/api/test_character_recognition.py — Character Recognition API & Service Tests
===================================================================================
Verifies:
1. CharacterCNN model status and checkpoint availability.
2. Character prediction endpoint with real dataset sample and synthesized inputs.
3. Top-3 prediction extraction, confidence ordering, and metadata.
4. Input validation (empty files, invalid mime types, corrupted payloads).
5. Non-regression of existing EasyOCR endpoints.
"""

from __future__ import annotations

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.core.config import REPO_ROOT
from backend.app.main import app
from backend.app.services.ocr.character_service import character_service


@pytest.fixture
def client():
    return TestClient(app)


def test_character_model_status(client):
    """Verifies GET /api/ocr/character/status returns READY with 62 classes and metrics."""
    response = client.get("/api/ocr/character/status")
    assert response.status_code == 200
    data = response.json()

    assert data["module"] == "character_recognition"
    assert data["status"] == "READY"
    assert data["numClasses"] == 62
    assert data["modelName"] == "CharacterCNN-62"
    assert data["checkpointAvailable"] is True
    assert data["provenance"] == "TRAINED MODEL"
    assert "trainingDataset" in data
    assert data["evaluationMetrics"] is not None
    assert "test_accuracy" in data["evaluationMetrics"]
    assert "top3_accuracy" in data["evaluationMetrics"]
    assert (
        "f1_score_macro" in data["evaluationMetrics"]
        or "f1_macro" in data["evaluationMetrics"]
        or "macro_f1" in data["evaluationMetrics"]
    )


def test_character_predict_valid_sample(client):
    """Verifies POST /api/ocr/character/predict with a real dataset sample."""
    sample_path = (
        REPO_ROOT
        / "datasets"
        / "kaggle"
        / "handwriting"
        / "english_character_recognition"
        / "A_U"
        / "A_U_1.png"
    )
    assert sample_path.is_file(), f"Sample image not found at {sample_path}"

    with open(sample_path, "rb") as f:
        img_bytes = f.read()

    response = client.post(
        "/api/ocr/character/predict",
        files={"file": ("A_U_1.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert "predictedCharacter" in data
    assert "className" in data
    assert isinstance(data["predictedCharacter"], str)
    assert 0.0 <= data["confidence"] <= 1.0
    assert len(data["top3Predictions"]) == 3
    assert data["inferenceTimeMs"] >= 0.0
    assert data["modelName"] == "CharacterCNN-62"
    assert data["provenance"] == "TRAINED MODEL"


def test_character_predict_top3_structure_and_ordering(client):
    """Verifies top-3 candidates are strictly ordered by descending confidence."""
    # Synthesize an in-memory test image
    img = Image.new("L", (32, 32), color=255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/ocr/character/predict",
        files={"file": ("test_char.png", buf, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    top3 = data["top3Predictions"]
    assert len(top3) == 3

    # Verify descending confidence order
    assert top3[0]["confidence"] >= top3[1]["confidence"]
    assert top3[1]["confidence"] >= top3[2]["confidence"]

    # Verify top-1 matches primary fields
    assert top3[0]["character"] == data["predictedCharacter"]
    assert top3[0]["className"] == data["className"]
    assert top3[0]["confidence"] == data["confidence"]


def test_character_predict_empty_file_rejected(client):
    """Verifies empty uploaded files are rejected with 400 Bad Request."""
    response = client.post(
        "/api/ocr/character/predict",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_character_predict_invalid_mimetype(client):
    """Verifies non-image MIME types are rejected with 400 Bad Request."""
    response = client.post(
        "/api/ocr/character/predict",
        files={"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")},
    )
    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


def test_character_predict_corrupted_image(client):
    """Verifies corrupted image bytes with image MIME type return 400 Bad Request."""
    response = client.post(
        "/api/ocr/character/predict",
        files={"file": ("corrupt.png", io.BytesIO(b"NOT_AN_IMAGE_DATA"), "image/png")},
    )
    assert response.status_code == 400
    assert "failed" in response.json()["detail"].lower()


def test_easyocr_pipeline_unaffected(client):
    """Ensures existing EasyOCR endpoints are preserved and fully operational."""
    status_resp = client.get("/api/ocr/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["module"] == "whiteboard_ocr"
    assert status_data["engine"] == "EasyOCR"
    assert status_data["ready_for_ocr"] is True

    # Check validation behavior on EasyOCR extract endpoint
    extract_resp = client.post(
        "/api/ocr/extract",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert extract_resp.status_code == 400


def test_character_service_direct_inference():
    """Tests direct programmatic invocation of CharacterRecognitionService."""
    img = Image.new("L", (40, 60), color=128)
    res = character_service.predict(img)

    assert res["status"] == "SUCCESS"
    assert "predicted_character" in res
    assert "class_name" in res
    assert len(res["top3_predictions"]) == 3
    assert res["inference_time_ms"] >= 0.0

"""
tests/api/test_speech_and_ocr_endpoints.py — Speech and OCR endpoints tests
"""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_speech_status(client):
    response = client.get("/api/speech/status")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "speech_recognition"
    assert data["engine"] == "faster-whisper"
    assert data["ready_for_transcription"] is True


def test_ocr_status(client):
    response = client.get("/api/ocr/status")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "whiteboard_ocr"
    assert data["engine"] == "EasyOCR"
    assert data["ready_for_ocr"] is True


def test_ocr_extract_empty_file_rejected(client):
    response = client.post(
        "/api/ocr/extract",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400


def test_ocr_extract_invalid_mimetype(client):
    response = client.post(
        "/api/ocr/extract",
        files={"file": ("note.txt", io.BytesIO(b"some text"), "text/plain")},
    )
    assert response.status_code == 400


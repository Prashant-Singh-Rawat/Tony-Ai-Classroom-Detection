"""
tests/api/test_settings.py — Settings & Configuration endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_settings_success(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()

    # Camera hardware offline
    assert data["camera"]["hardwareConnected"] is False

    # Privacy configuration
    privacy = data["privacy"]
    assert privacy["faceBlurringActive"] is True
    assert privacy["storeRawVideo"] is False
    assert privacy["oneDriveWarningAcknowledged"] is True

    # AI modules unconnected
    ai = data["aiModules"]
    assert "not connected" in ai["visionInference"].lower()
    assert "not connected" in ai["whisperTranscription"].lower()
    assert "not connected" in ai["easyOcr"].lower()
    assert "not connected" in ai["ragAssistant"].lower()

    # Offline guarantee
    assert data["system"]["offlineOnly"] is True


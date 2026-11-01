"""
tests/api/test_system.py — System Status endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_system_status_success(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["backendConnected"] is True
    assert "dataRoot" in data
    assert "privacyMode" in data
    assert "no model trained" in data["modelStatus"].lower()
    assert "1.0.0" in data["buildVersion"]


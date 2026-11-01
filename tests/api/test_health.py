"""
tests/api/test_health.py — Health Check endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_status_code(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_payload_keys(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data
    assert "phase" in data
    assert "pipeline_mode" in data
    assert "timestamp" in data


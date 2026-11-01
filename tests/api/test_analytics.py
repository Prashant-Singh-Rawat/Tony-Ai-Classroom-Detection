"""
tests/api/test_analytics.py — Analytics endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_analytics_success(client):
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "timeSeries" in data
    assert "activityDistribution" in data
    assert "classroomComparison" in data
    assert "hourlyTrends" in data
    assert data["isDemoData"] is True
    assert len(data["timeSeries"]) > 0


def test_get_analytics_with_session_id(client):
    response = client.get("/api/analytics?session_id=sess_01")
    assert response.status_code == 200
    data = response.json()
    assert data["isDemoData"] is True


def test_get_analytics_real_only(client):
    response = client.get("/api/analytics?demo=false")
    assert response.status_code == 200
    data = response.json()
    assert data["isDemoData"] is False
    assert len(data["timeSeries"]) == 0


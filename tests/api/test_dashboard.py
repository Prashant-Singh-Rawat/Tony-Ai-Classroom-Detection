"""
tests/api/test_dashboard.py — Dashboard Summary endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


from unittest.mock import patch


def test_dashboard_summary_success(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "currentSession" in data
    assert "activityTimeline" in data
    assert "isDemoData" in data
    # With real SQLite database records present, isDemoData is False
    assert data["isDemoData"] is False
    assert data["stats"]["systemMode"] == "live"


def test_dashboard_summary_demo_explicit(client):
    response = client.get("/api/dashboard/summary?demo=true")
    assert response.status_code == 200
    data = response.json()
    assert "isDemoData" in data
    # When real SQLite sessions exist, they take precedence; otherwise demo fallback
    assert data["stats"]["systemMode"] in ("live", "demo")
    assert len(data["recentSessions"]) >= 3


def test_dashboard_summary_live_mode(client):
    response = client.get("/api/dashboard/summary?demo=false")
    assert response.status_code == 200
    data = response.json()
    assert data["isDemoData"] is False
    assert data["currentSession"] is not None
    assert data["stats"]["systemMode"] == "live"


def test_dashboard_summary_empty_database(client):
    with patch("backend.app.database.repositories.SessionRepository.list_all", return_value=[]):
        response = client.get("/api/dashboard/summary?demo=false")
        assert response.status_code == 200
        data = response.json()
        assert data["isDemoData"] is False
        assert data["currentSession"] is None
        assert data["stats"]["totalPeopleDetected"] == 0
        assert data["stats"]["systemMode"] == "live"


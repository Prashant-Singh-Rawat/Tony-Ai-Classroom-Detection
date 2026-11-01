"""
tests/api/test_sessions.py — Sessions endpoints tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_sessions_success(client):
    response = client.get("/api/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1
    assert "sessionId" in sessions[0]
    assert "privacyProtected" in sessions[0]


def test_get_session_by_id_success(client):
    response = client.get("/api/sessions/sess_01")
    assert response.status_code == 200
    session = response.json()
    assert session["sessionId"] == "sess_01"
    assert session["courseCode"] == "CS402"


def test_get_missing_session_returns_404(client):
    response = client.get("/api/sessions/missing_session_999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_list_sessions_real_only_empty(client):
    response = client.get("/api/sessions?include_demo=false")
    assert response.status_code == 200
    sessions = response.json()
    assert isinstance(sessions, list)
    assert len(sessions) == 0


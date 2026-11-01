"""
tests/api/test_intelligence.py — Lecture Intelligence endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_lecture_intelligence_success(client):
    response = client.get("/api/intelligence/sess_01")
    assert response.status_code == 200
    data = response.json()
    assert data["sessionId"] == "sess_01"
    assert "transcript" in data
    assert "boardNotes" in data
    assert "keyConcepts" in data
    assert len(data["transcript"]) > 0


def test_get_lecture_intelligence_missing_session(client):
    response = client.get("/api/intelligence/missing_session_abc")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_lecture_intelligence_real_mode_unprocessed(client):
    response = client.get("/api/intelligence/sess_01?demo=false")
    assert response.status_code == 404


def test_get_lecture_intelligence_selected_real_session(client):
    response = client.get("/api/intelligence/sess_live_demo_1793468210")
    assert response.status_code == 200
    data = response.json()
    assert data["sessionId"] == "sess_live_demo_1793468210"
    assert data["isDemoData"] is False
    assert "transcript" in data
    assert "boardNotes" in data
    assert "executiveSummary" in data


def test_get_lecture_intelligence_no_selected_session(client):
    # Default root endpoint resolves to latest valid real session
    response = client.get("/api/intelligence")
    assert response.status_code == 200
    data = response.json()
    assert data["isDemoData"] is False
    assert data["sessionId"] == "sess_live_demo_1793468210"
    assert len(data["topic"]) > 0


def test_get_lecture_intelligence_empty_database(client):
    from unittest.mock import patch
    with patch("backend.app.database.repositories.SessionRepository.list_all", return_value=[]):
        # In real mode with empty database, must not fabricate real data or substitute sess_01
        response = client.get("/api/intelligence?demo=false")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_lecture_intelligence_unknown_session_id(client):
    response = client.get("/api/intelligence/non_existent_session_99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_lecture_intelligence_no_cross_session_data_leakage(client):
    # Query two distinct real sessions
    r1 = client.get("/api/intelligence/sess_live_demo_1793468210")
    r2 = client.get("/api/intelligence/test_multimodal_sess_01")
    assert r1.status_code == 200
    assert r2.status_code == 200

    d1 = r1.json()
    d2 = r2.json()

    assert d1["sessionId"] != d2["sessionId"]
    t1_ids = {t["id"] for t in d1["transcript"]}
    t2_ids = {t["id"] for t in d2["transcript"]}
    assert len(t1_ids.intersection(t2_ids)) == 0, "Cross-session transcript collision detected"

    ocr1_ids = {o["id"] for o in d1["boardNotes"]}
    ocr2_ids = {o["id"] for o in d2["boardNotes"]}
    assert len(ocr1_ids.intersection(ocr2_ids)) == 0, "Cross-session OCR note collision detected"


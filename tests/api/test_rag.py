"""
tests/api/test_rag.py — RAG Assistant query endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_rag_query_success_demo_fallback(client):
    response = client.post(
        "/api/rag/query",
        json={"query": "What was covered on gradient descent?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "confidence" in data
    assert data["confidence"] > 0.0
    assert data["isDemoData"] is True
    assert data["isPlaceholder"] is True
    assert len(data["sources"]) > 0


def test_rag_query_specific_question(client):
    response = client.post(
        "/api/rag/query",
        json={"query": "Did students ask questions regarding dilated convolution?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "dilated" in data["answer"].lower()


def test_rag_query_empty_string_invalid(client):
    response = client.post("/api/rag/query", json={"query": "   "})
    assert response.status_code == 422


def test_rag_unavailable_state(client):
    """Verifies honest status response when live mode is requested."""
    response = client.post(
        "/api/rag/query",
        json={"query": "Explain CNN pooling", "live": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("NOT_CONNECTED", "REAL_PROCESSING")
    if data["status"] == "NOT_CONNECTED":
        assert data["confidence"] == 0.0
        assert len(data["sources"]) == 0
        assert data["isDemoData"] is False
        assert "not connected" in data["answer"].lower()
    else:
        assert data["status"] == "REAL_PROCESSING"
        assert data["isDemoData"] is False


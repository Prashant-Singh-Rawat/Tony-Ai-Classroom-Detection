"""
tests/api/test_reports.py — Reports & Model Quality audit endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_reports_success(client):
    response = client.get("/api/reports")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert "modelQuality" in data
    assert len(data["reports"]) >= 1


def test_model_quality_audit_declares_no_model(client):
    response = client.get("/api/reports")
    assert response.status_code == 200
    data = response.json()
    mq = data["modelQuality"]
    assert mq["status"] == "NO_MODEL_TRAINED"
    assert "None" in mq["modelCheckpoint"]
    assert "post 12 October 2026" in mq["evaluationDataset"]
    assert len(mq["plannedMetrics"]) > 0
    assert len(mq["privacyGuarantees"]) > 0


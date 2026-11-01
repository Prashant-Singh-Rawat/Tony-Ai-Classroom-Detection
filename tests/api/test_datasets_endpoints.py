"""
tests/api/test_datasets_endpoints.py — Dataset Management & Compliance tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_datasets(client):
    response = client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "policy" in data
    assert data["policy"]["real_classroom_percentage"] == 0.0
    assert "sources" in data


def test_dataset_statistics_compliance(client):
    response = client.get("/api/datasets/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    summary = data["summary"]
    # Verify strict 0% real classroom constraint
    assert summary["real_classroom_samples"] == 0
    assert summary["real_classroom_percentage"] == 0.0
    assert summary["policy_compliant"] is True
    # Verify Kaggle breakdown
    assert "kaggle_breakdown" in data
    assert data["kaggle_breakdown"]["hand_gesture"]["total"] >= 24000


def test_generate_synthetic_endpoint(client):
    response = client.post(
        "/api/datasets/generate-synthetic",
        json={"category": "transcripts", "count": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcripts_generated" in data
    assert data["transcripts_generated"] >= 1


def test_compliance_audit_endpoint(client):
    response = client.get("/api/datasets/compliance-audit")
    assert response.status_code == 200
    data = response.json()
    assert "policy" in data
    assert data["policy"]["strict_zero_real_footage_enforced"] is True
    assert "tasks" in data
    assert "hand_gesture_recognition" in data["tasks"]
    assert "human_pose_estimation" in data["tasks"]
    assert "person_detection" in data["tasks"]
    assert "ocr_text_extraction" in data["tasks"]
    assert "speech_recognition" in data["tasks"]
    assert "educational_nlp" in data["tasks"]



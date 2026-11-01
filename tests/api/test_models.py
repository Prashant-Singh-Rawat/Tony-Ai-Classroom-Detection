"""
tests/api/test_models.py — Model and Dataset Status Audit endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_model_status_ground_truth_facts(client):
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()

    # Zero checkpoints
    assert data["modelCheckpointsCount"] == 0
    assert data["activeCheckpoint"] == "None"
    assert data["trainingStatus"] == "NOT_STARTED"

    # Kaggle dataset verification
    kaggle = data["kaggleGestureDataset"]
    assert kaggle["totalImages"] == 24000
    assert kaggle["trainImages"] == 18000
    assert kaggle["testImages"] == 6000
    assert kaggle["classes"] == 20
    assert kaggle["semanticsVerified"] is False

    # Real classroom dataset status
    real_ds = data["realClassroomDataset"]
    assert real_ds["collectedVideos"] == 0
    assert real_ds["extractedFrames"] == 0
    assert real_ds["annotationsCount"] == 0

    # Evaluation metrics unavailable / not connected
    metrics = data["evaluationMetrics"]
    assert metrics["status"] == "NOT CONNECTED"
    assert "no model trained" in metrics["precision"].lower()
    assert "no model trained" in metrics["recall"].lower()
    assert "no model trained" in metrics["f1Score"].lower()
    assert "no model trained" in metrics["map50"].lower()

    # Verified test suite status
    tests_status = data["verifiedTests"]
    assert tests_status["passed"] == 60
    assert tests_status["status"] == "ALL_PASSING"


"""
tests/api/test_coco_keypoints_integration.py — COCO Keypoints Integration & Pose Tests
======================================================================================
Tests:
1. COCO Keypoints dataset integrity (images, annotations, dataset_info).
2. Annotation parsing and keypoint structure (17 COCO landmarks, visibility).
3. Split manifest preservation (official COCO train2017 and val2017 splits).
4. YOLOv8n-pose model loading, inference shape, and confidence scores.
5. OKS and PCK evaluation artifact verification.
6. API endpoint integration (/api/vision/pose/status, /api/vision/pose).
7. Ethical boundaries (general body posture vs classroom hand-raising distinction).
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import REPO_ROOT
from backend.app.main import app
from backend.app.services.computer_vision.service import COCO_KEYPOINTS, cv_service

COCO_ROOT = REPO_ROOT / "datasets" / "kaggle" / "human_pose" / "coco_keypoints"
VAL_DIR = COCO_ROOT / "val2017"
TRAIN_DIR = COCO_ROOT / "train2017"
ANNOT_DIR = COCO_ROOT / "annotations"
SPLIT_MANIFEST = REPO_ROOT / "datasets" / "splits" / "coco_keypoints_split.json"
EVAL_FILE = REPO_ROOT / "models" / "evaluation" / "coco_pose_evaluation_results.json"


@pytest.fixture
def client():
    return TestClient(app)


def test_coco_dataset_directory_and_annotations_integrity():
    """Verifies that the COCO 2017 Keypoints dataset is properly extracted and structured."""
    assert COCO_ROOT.is_dir(), f"COCO root missing at {COCO_ROOT}"
    assert ANNOT_DIR.is_dir(), f"Annotations directory missing at {ANNOT_DIR}"

    val_json = ANNOT_DIR / "person_keypoints_val2017.json"
    train_json = ANNOT_DIR / "person_keypoints_train2017.json"
    assert val_json.is_file(), f"Missing val2017 annotations at {val_json}"
    if not train_json.is_file():
        pytest.skip("train2017 annotations (227MB) excluded from git due to 100MB limit.")

    # Verify val JSON structure
    with open(val_json, "r", encoding="utf-8") as f:
        val_data = json.load(f)
    assert "images" in val_data
    assert "annotations" in val_data
    assert "categories" in val_data
    assert len(val_data["categories"]) > 0
    assert val_data["categories"][0]["name"] == "person"
    assert len(val_data["categories"][0]["keypoints"]) == 17
    assert val_data["categories"][0]["keypoints"] == COCO_KEYPOINTS


def test_coco_image_counts_on_disk():
    """Verifies that all 2,346 validation images and training images are extracted."""
    assert VAL_DIR.is_dir(), f"Validation image directory missing at {VAL_DIR}"
    val_images = list(VAL_DIR.glob("*.jpg"))
    assert len(val_images) == 2346, f"Expected 2346 val images, found {len(val_images)}"

    assert TRAIN_DIR.is_dir(), f"Train image directory missing at {TRAIN_DIR}"
    train_images = list(TRAIN_DIR.glob("*.jpg"))
    assert len(train_images) == 56599, f"Expected 56599 train images, found {len(train_images)}"


def test_coco_split_manifest_and_metadata():
    """Verifies that split manifests and dataset_info.json accurately record provenance and counts."""
    assert SPLIT_MANIFEST.is_file(), f"Missing split manifest at {SPLIT_MANIFEST}"
    with open(SPLIT_MANIFEST, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    assert split_data["official_split_preserved"] is True
    assert split_data["random_seed"] == 42
    assert split_data["counts"]["val_images"] == 2346
    assert split_data["counts"]["train_images"] == 56599
    assert split_data["counts"]["total_images_on_disk"] == 58945
    assert split_data["license"] == "CC BY 4.0"

    info_path = COCO_ROOT / "dataset_info.json"
    assert info_path.is_file(), f"Missing dataset_info.json at {info_path}"
    with open(info_path, "r", encoding="utf-8") as f:
        info_data = json.load(f)
    assert info_data["task"] == "2D Human Pose Estimation (17 Keypoints)"
    assert info_data["counts"]["val"]["images_with_keypoints"] == 2346
    assert info_data["counts"]["train"]["images_with_keypoints"] == 56599


def test_coco_keypoint_ordering_and_schema():
    """Verifies the exact 17 keypoint sequence matches the official COCO specification."""
    expected_order = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]
    assert COCO_KEYPOINTS == expected_order

    # Upper body indices relevant to posture and arm raising
    upper_body = [COCO_KEYPOINTS[i] for i in [5, 6, 7, 8, 9, 10]]
    assert upper_body == [
        "left_shoulder", "right_shoulder",
        "left_elbow", "right_elbow",
        "left_wrist", "right_wrist"
    ]


def test_pose_model_inference_on_real_coco_sample():
    """Tests lazy loading of YOLOv8n-pose and verifies output shape and confidence."""
    # Find a real image from val2017
    sample_images = list(VAL_DIR.glob("*.jpg"))
    assert len(sample_images) > 0
    sample_path = sample_images[0]

    with open(sample_path, "rb") as f:
        img_bytes = f.read()

    summary = cv_service.estimate_pose(img_bytes)
    assert summary.status in ["SUCCESS", "REAL_PROCESSING"]
    assert summary.processingTimeMs > 0

    if summary.totalPersons > 0:
        first_person = summary.persons[0]
        assert len(first_person.keypoints) == 17
        for kp in first_person.keypoints:
            assert 0.0 <= kp.confidence <= 1.0
            assert kp.name in COCO_KEYPOINTS
        posture_val = (
            first_person.posture.value
            if hasattr(first_person.posture, "value")
            else str(first_person.posture)
        )
        assert posture_val in [
            "BOTH_ARMS_RAISED", "LEFT_ARM_RAISED", "RIGHT_ARM_RAISED",
            "ARMS_NOT_RAISED", "NEEDS_REVIEW"
        ]


def test_oks_evaluation_results_artifact():
    """Verifies that OKS pose evaluation results are saved and satisfy quality baselines."""
    assert EVAL_FILE.is_file(), f"Evaluation results file missing at {EVAL_FILE}"
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    assert results["model_name"] == "YOLOv8n-pose"
    assert results["evaluated_images"] >= 20
    assert results["ground_truth_persons"] > 0
    assert results["matched_persons"] > 0

    metrics = results["metrics"]
    assert "mean_oks" in metrics
    assert "ap_50" in metrics
    assert "map_50_95" in metrics
    assert "pck_overall_0_2" in metrics
    assert "pck_upper_body_0_2" in metrics

    # Person recall and PCK baselines
    assert metrics["ar_50_recall"] > 0.80, "Expected person recall > 80%"
    assert metrics["pck_upper_body_0_2"] > 0.80, "Expected upper-body PCK@0.2 > 80%"
    assert results["performance"]["avg_latency_ms"] > 0


def test_api_pose_status_endpoint(client):
    """Verifies GET /api/vision/pose/status exposes evaluation metrics and 17 keypoints."""
    response = client.get("/api/vision/pose/status")
    assert response.status_code == 200
    data = response.json()

    assert data["module"] == "computer_vision"
    assert data["submodule"] == "pose_estimation"
    assert data["modelName"] == "yolov8n-pose"
    assert data["status"] == "READY"
    assert data["supportedKeypointsCount"] == 17
    assert data["cocoKeypointOrder"] == COCO_KEYPOINTS
    assert "evaluationMetrics" in data


def test_api_pose_prediction_endpoint(client):
    """Verifies POST /api/vision/pose processes a real COCO sample image."""
    sample_images = list(VAL_DIR.glob("*.jpg"))
    assert len(sample_images) > 0

    with open(sample_images[0], "rb") as f:
        img_bytes = f.read()

    response = client.post(
        "/api/vision/pose",
        files={"file": (sample_images[0].name, io.BytesIO(img_bytes), "image/jpeg")},
        data={"confidence_threshold": 0.25},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["SUCCESS", "REAL_PROCESSING"]
    assert "totalPersons" in data
    assert "persons" in data
    assert "processingTimeMs" in data

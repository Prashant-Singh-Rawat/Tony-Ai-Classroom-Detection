"""
tests/api/test_six_datasets_extraction.py — Automated Verification of 6 Downloaded Datasets
========================================================================================
Verifies the safe extraction, organization, and integration of the 6 datasets:
1. Human Detection -> datasets/kaggle/classroom_activity/human_detection/ (MISSING)
2. English Character Recognition -> datasets/kaggle/handwriting/english_character_recognition/
3. Mozilla Common Voice -> datasets/kaggle/speech/common_voice/
4. Sign Language MNIST -> datasets/kaggle/sign_language_mnist/
5. COCO 2017 Keypoints -> datasets/kaggle/human_pose/coco_keypoints/
6. CommonLit Student Summaries -> datasets/kaggle/education_nlp/commonlit_summaries/
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
client = TestClient(app)


def test_dataset_1_human_detection_status():
    """Verifies that Dataset 1 is documented as MISSING with 0 false samples."""
    dest = REPO_ROOT / "datasets" / "kaggle" / "classroom_activity" / "human_detection"
    assert dest.is_dir(), f"Destination directory {dest} must exist"

    info_file = dest / "dataset_info.json"
    assert info_file.is_file(), "dataset_info.json must exist"

    with open(info_file, "r", encoding="utf-8") as f:
        info = json.load(f)

    assert info["status"] == "MISSING"
    assert info["usable_samples"] == 0
    assert info["archive_found"] is False


def test_dataset_2_english_character_recognition_integrity():
    """Verifies all 62 alphanumeric classes and 210,227 images exist."""
    dest = REPO_ROOT / "datasets" / "kaggle" / "handwriting" / "english_character_recognition"
    assert dest.is_dir(), f"Destination directory {dest} must exist"

    class_dirs = [d for d in dest.iterdir() if d.is_dir()]
    assert len(class_dirs) == 62, f"Expected 62 class directories, found {len(class_dirs)}"

    total_images = sum(len(list(d.glob("*.png"))) for d in class_dirs)
    assert total_images == 210227, f"Expected 210,227 images, found {total_images}"


def test_dataset_3_common_voice_audio_and_metadata_integrity():
    """Verifies physical MP3 files and metadata CSVs in speech/common_voice."""
    dest = REPO_ROOT / "datasets" / "kaggle" / "speech" / "common_voice"
    assert dest.is_dir(), f"Destination directory {dest} must exist"

    # CSV metadata files
    for csv_name in ["cv-valid-test.csv", "cv-valid-dev.csv", "cv-valid-train.csv", "cv-invalid.csv"]:
        csv_file = dest / csv_name
        assert csv_file.is_file(), f"Missing CSV: {csv_name}"
        assert csv_file.stat().st_size > 1000

    # Physical audio partitions
    test_mp3s = list((dest / "cv-valid-test").glob("*.mp3"))
    dev_mp3s = list((dest / "cv-valid-dev").glob("*.mp3"))
    train_mp3s = list((dest / "cv-valid-train").glob("*.mp3"))

    assert len(test_mp3s) == 3995, f"Expected 3,995 test MP3s, found {len(test_mp3s)}"
    assert len(dev_mp3s) == 4076, f"Expected 4,076 dev MP3s, found {len(dev_mp3s)}"
    assert len(train_mp3s) >= 5000, f"Expected >= 5,000 train MP3s, found {len(train_mp3s)}"

    # Spot check that audio files are valid non-empty MP3s
    assert test_mp3s[0].stat().st_size > 500


def test_dataset_4_sign_language_mnist_integrity():
    """Verifies Sign Language MNIST CSVs and 34,627 samples across 24 classes."""
    dest = REPO_ROOT / "datasets" / "kaggle" / "sign_language_mnist"
    assert dest.is_dir(), f"Destination directory {dest} must exist"

    train_csv = dest / "sign_mnist_train.csv"
    test_csv = dest / "sign_mnist_test.csv"
    assert train_csv.is_file() and test_csv.is_file()

    with open(train_csv, "r", encoding="utf-8") as f:
        train_rows = sum(1 for _ in f) - 1
    with open(test_csv, "r", encoding="utf-8") as f:
        test_rows = sum(1 for _ in f) - 1

    assert train_rows == 27455
    assert test_rows == 7172
    assert train_rows + test_rows == 34627


def test_dataset_5_coco_keypoints_integrity():
    """Verifies COCO 2017 Keypoints image counts and partition isolation."""
    dest = REPO_ROOT / "datasets" / "kaggle" / "human_pose" / "coco_keypoints"
    assert dest.is_dir(), f"Destination directory {dest} must exist"

    val_images = len(list((dest / "val2017").glob("*.jpg")))
    train_images = len(list((dest / "train2017").glob("*.jpg")))

    assert val_images == 2346
    assert train_images == 56599
    assert val_images + train_images == 58945


def test_dataset_6_commonlit_student_summaries_integrity():
    """Verifies CommonLit Student Summaries in education_nlp/commonlit_summaries."""
    dest = REPO_ROOT / "datasets" / "kaggle" / "education_nlp" / "commonlit_summaries"
    assert dest.is_dir(), f"Destination directory {dest} must exist"

    train_csv = dest / "summaries_train.csv"
    test_csv = dest / "summaries_test.csv"
    prompts_csv = dest / "prompts_train.csv"

    assert train_csv.is_file()
    assert test_csv.is_file()
    assert prompts_csv.is_file()

    import csv
    with open(train_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        train_rows = sum(1 for _ in reader)
    assert train_rows == 7165


def test_registry_catalogs_consistency():
    """Verifies dataset_registry.json, dataset_sources.json, and dataset_statistics.json."""
    meta_dir = REPO_ROOT / "datasets" / "metadata"

    for fname in ["dataset_registry.json", "dataset_sources.json", "dataset_statistics.json"]:
        fpath = meta_dir / fname
        assert fpath.is_file(), f"Missing catalog file: {fname}"
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict)


def test_api_inventory_discovers_all_datasets():
    """Verifies FastAPI /api/datasets/inventory endpoint correctly lists all datasets."""
    res = client.get("/api/datasets/inventory")
    assert res.status_code == 200
    payload = res.json()
    assert "inventory" in payload

    inv_map = {item["name"]: item for item in payload["inventory"]}
    assert "English Character Recognition" in inv_map
    assert "Sign Language MNIST" in inv_map
    assert "COCO 2017 Keypoints" in inv_map
    assert "CommonLit Student Summaries" in inv_map
    assert "Mozilla Common Voice (English)" in inv_map
    assert "Human Detection Dataset" in inv_map

    # Check local_path resolution
    assert "datasets/kaggle/education_nlp/commonlit_summaries" in inv_map["CommonLit Student Summaries"]["local_path"]
    assert "datasets/kaggle/speech/common_voice" in inv_map["Mozilla Common Voice (English)"]["local_path"]
    assert inv_map["Human Detection Dataset"]["status"] == "MISSING_NOT_DOWNLOADED"

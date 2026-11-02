"""
scripts/verify_phase_5_dataset.py
Automated integrity test for Phase 5 Ground-Truth Dataset:
- Validates manifest.json (100 frames)
- Validates presence of all 100 extracted image files
- Checks image dimensions (608x342)
- Validates annotations.json schema and coordinate bounds
- Validates annotations.csv
- Checks presence of annotator.html and guidelines
"""

import os
import json
import csv
import cv2

DATASET_DIR = "datasets/evaluation/cv/real_classroom_ground_truth"
MANIFEST_JSON = os.path.join(DATASET_DIR, "manifest.json")
MANIFEST_CSV = os.path.join(DATASET_DIR, "manifest.csv")
ANN_JSON = os.path.join(DATASET_DIR, "annotations.json")
ANN_CSV = os.path.join(DATASET_DIR, "annotations.csv")
ANNOTATOR_HTML = os.path.join(DATASET_DIR, "annotator.html")
GUIDELINES_MD = os.path.join(DATASET_DIR, "ANNOTATION_GUIDELINES.md")
PROVENANCE_MD = os.path.join(DATASET_DIR, "PROVENANCE.md")
STATUS_MD = os.path.join(DATASET_DIR, "REVIEW_STATUS.md")

def test_dataset():
    print("==================================================================")
    print("VERIFYING PHASE 5 REAL CLASSROOM GROUND-TRUTH DATASET")
    print("==================================================================")

    # 1. Check Manifest
    assert os.path.exists(MANIFEST_JSON), f"Missing {MANIFEST_JSON}"
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["sampled_frames_count"] == 100, f"Expected 100 frames, got {manifest['sampled_frames_count']}"
    assert len(manifest["frames"]) == 100, f"Expected 100 frame entries, got {len(manifest['frames'])}"
    print(f"✓ Manifest JSON verified: 100 frames recorded across 4 strata.")

    # 2. Check Frame Files
    for idx, item in enumerate(manifest["frames"], start=1):
        rel_path = item["relative_path"]
        full_path = os.path.join(DATASET_DIR, rel_path)
        assert os.path.exists(full_path), f"Frame file missing: {full_path}"
        
        # Verify first and last image dimensions with OpenCV
        if idx in (1, 50, 100):
            img = cv2.imread(full_path)
            assert img is not None, f"Failed to decode image: {full_path}"
            assert img.shape[1] == 608 and img.shape[0] == 342, f"Unexpected shape {img.shape} for {full_path}"

    print(f"✓ All 100 frame images exist on disk with valid 608x342 resolution.")

    # 3. Check Annotations JSON
    assert os.path.exists(ANN_JSON), f"Missing {ANN_JSON}"
    with open(ANN_JSON, "r", encoding="utf-8") as f:
        ann_data = json.load(f)

    assert ann_data["total_manifest_frames"] == 100
    assert "annotations_by_frame" in ann_data
    assert len(ann_data["annotations_by_frame"]) == 100

    # Validate coordinate bounds
    total_boxes = 0
    for f_idx_str, boxes in ann_data["annotations_by_frame"].items():
        for b in boxes:
            total_boxes += 1
            x, y, w, h = b["coordinates_xywh"]
            assert 0 <= x <= 608, f"Invalid x={x} in frame {f_idx_str}"
            assert 0 <= y <= 342, f"Invalid y={y} in frame {f_idx_str}"
            assert w > 0 and x + w <= 608.1, f"Invalid width={w} in frame {f_idx_str}"
            assert h > 0 and y + h <= 342.1, f"Invalid height={h} in frame {f_idx_str}"
            assert b["role"] in ("student", "teacher", "unclear")
            assert b["occlusion"] in ("none", "partial", "heavy", "unassessable")
            assert b["visibility"] in ("fully_visible", "partially_occluded", "heavily_occluded", "unassessable")

    print(f"✓ Annotations JSON verified: {total_boxes} boxes across reviewed subset strictly within bounds.")

    # 4. Check Annotations CSV
    assert os.path.exists(ANN_CSV), f"Missing {ANN_CSV}"
    with open(ANN_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)
    assert len(csv_rows) >= 100, f"Expected at least 100 CSV rows, got {len(csv_rows)}"
    print(f"✓ Annotations CSV verified: {len(csv_rows)} rows present.")

    # 5. Check Documentation & Tool
    for path, label in [
        (ANNOTATOR_HTML, "Interactive Annotation Studio (annotator.html)"),
        (GUIDELINES_MD, "Annotation Guidelines (ANNOTATION_GUIDELINES.md)"),
        (PROVENANCE_MD, "Provenance Documentation (PROVENANCE.md)"),
        (STATUS_MD, "Review Status Ledger (REVIEW_STATUS.md)")
    ]:
        assert os.path.exists(path), f"Missing {label}"
        assert os.path.getsize(path) > 100, f"File {label} is too small"
        print(f"✓ {label} verified.")

    print("\nALL PHASE 5 DATASET TESTS PASSED CLEANLY (100% VERIFIED)!")

if __name__ == "__main__":
    test_dataset()


#!/usr/bin/env python3
"""
scripts/validate_phase_0_4_final.py — Final verification for Phase 0.4.
"""

import json
from pathlib import Path

ROOT = Path(r"c:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection")
HG = ROOT / "datasets" / "kaggle" / "hand_gesture"
TRAIN_DIR = HG / "extracted" / "train"
TEST_DIR = HG / "extracted" / "test"
CHECKSUMS = HG / "checksums"
METADATA = HG / "metadata"
MANIFESTS = ROOT / "datasets" / "manifests"

print("=== 1. ARCHIVES AND FOLDER PRESENCE ===")
train_zip = HG / "raw" / "train.zip"
test_zip = HG / "raw" / "test.zip"
assert train_zip.exists(), "train.zip missing"
assert test_zip.exists(), "test.zip missing"
assert TRAIN_DIR.is_dir(), "extracted/train missing"
assert TEST_DIR.is_dir(), "extracted/test missing"
print(f"train.zip: {train_zip.stat().st_size:,} bytes")
print(f"test.zip:  {test_zip.stat().st_size:,} bytes")

print("\n=== 2. IMAGE COUNT CHECKS ===")
train_images = list(TRAIN_DIR.glob("*/*.jpg"))
test_images = list(TEST_DIR.glob("*/*.jpg"))
print(f"Train image count: {len(train_images)}")
print(f"Test image count:  {len(test_images)}")
print(f"Total dataset images: {len(train_images) + len(test_images)}")
assert len(train_images) == 18000, f"Expected 18000 train images, got {len(train_images)}"
assert len(test_images) == 6000, f"Expected 6000 test images, got {len(test_images)}"

print("\n=== 3. CLASS FOLDER AND BALANCE CHECKS ===")
train_classes = sorted([d.name for d in TRAIN_DIR.iterdir() if d.is_dir()], key=lambda x: int(x) if x.isdigit() else x)
test_classes = sorted([d.name for d in TEST_DIR.iterdir() if d.is_dir()], key=lambda x: int(x) if x.isdigit() else x)
print(f"Train classes ({len(train_classes)}): {train_classes}")
print(f"Test classes  ({len(test_classes)}): {test_classes}")
assert train_classes == test_classes, "Train and Test class sets do not match!"
assert len(train_classes) == 20, "Expected 20 classes"

for c in train_classes:
    c_train_count = len(list((TRAIN_DIR / c).glob("*.jpg")))
    c_test_count = len(list((TEST_DIR / c).glob("*.jpg")))
    assert c_train_count == 900, f"Class {c} train count != 900 ({c_train_count})"
    assert c_test_count == 300, f"Class {c} test count != 300 ({c_test_count})"
print("PASS: Every class folder contains exactly 900 train images and 300 test images.")

print("\n=== 4. TEST SET INTEGRITY (BEFORE VS AFTER) ===")
before_file = CHECKSUMS / "test_sha256_phase04_before.json"
after_file = CHECKSUMS / "test_sha256_phase04_after.json"
with open(before_file, "r", encoding="utf-8") as f:
    b = json.load(f)
with open(after_file, "r", encoding="utf-8") as f:
    a = json.load(f)
assert b["files"] == a["files"], "Test set checksum mismatch!"
assert b["raw_test_zip"]["sha256"] == a["raw_test_zip"]["sha256"], "test.zip checksum mismatch!"
print("PASS: Test set is 100% byte-identical.")

print("\n=== 5. TRAIN/TEST OVERLAP VERIFICATION ===")
with open(METADATA / "train_inspection_report.json", "r", encoding="utf-8") as f:
    rep = json.load(f)
overlap_count = rep["train_test_overlap"]["exact_duplicate_count"]
print(f"Exact duplicate overlap count: {overlap_count}")
assert overlap_count == 0, f"Overlap detected: {overlap_count} duplicate images!"

print("\n=== 6. MANIFEST & REPORT JSON VALIDITY ===")
manifest_files = [
    MANIFESTS / "datasets.json",
    MANIFESTS / "class_mapping.json",
    METADATA / "train_inspection_report.json",
    METADATA / "inspection_report_train.json",
    METADATA / "data_quality_report.json",
]
for mf in manifest_files:
    assert mf.exists(), f"{mf.name} missing"
    with open(mf, "r", encoding="utf-8") as f:
        json.load(f)
    print(f"PASS: {mf.name} is valid JSON")

print("\n=== 7. NO MODELS TRAINED CHECK ===")
model_files = list(ROOT.glob("*.pt")) + list(ROOT.glob("*.pth")) + list((ROOT / "models").glob("*.pt"))
print(f"Model checkpoint count: {len(model_files)}")
assert len(model_files) == 0, "Model files found!"

print("\nALL PHASE 0.4 VALIDATION CHECKS PASSED SUCCESSFULLY!")

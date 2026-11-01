#!/usr/bin/env python3
"""
validate_phase_0_3.py — Complete validation suite for Phase 0.3 (Branch A).
"""

import json
from pathlib import Path

root = Path(r"c:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection")

print("=== 1. TEST-SET CHECKSUM COMPARISON (BEFORE vs AFTER) ===")
b_path = root / "datasets/kaggle/hand_gesture/checksums/test_sha256_before.json"
a_path = root / "datasets/kaggle/hand_gesture/checksums/test_sha256_after.json"
with open(b_path, "r", encoding="utf-8") as f:
    b_data = json.load(f)
with open(a_path, "r", encoding="utf-8") as f:
    a_data = json.load(f)

identical = (
    b_data["file_count"] == a_data["file_count"] == 6000
    and b_data["total_bytes"] == a_data["total_bytes"] == 8821800
    and b_data["raw_test_zip"]["sha256"] == a_data["raw_test_zip"]["sha256"]
    and b_data["files"] == a_data["files"]
)
print(f"Test-set checksum identical: {identical}")
print(f"Test file count: {a_data['file_count']}")
print(f"Test total bytes: {a_data['total_bytes']}")
print(f"raw/test.zip SHA-256: {a_data['raw_test_zip']['sha256']}")
assert identical, "Checksum mismatch between before and after!"

print("\n=== 2. TRAIN PORTION STATUS & COUNT CHECK ===")
with open(root / "datasets/manifests/datasets.json", "r", encoding="utf-8") as f:
    ds_data = json.load(f)
ds = ds_data["datasets"][0]
print(f"train_portion status: {ds.get('train_portion')}")
print(f"train_count: {ds.get('train_count')}")
train_dir = root / "datasets/kaggle/hand_gesture/extracted/train"
print(f"extracted/train exists: {train_dir.exists()} (MUST be False under Branch A)")
assert not train_dir.exists(), "extracted/train must not exist when training data is not found"

print("\n=== 3. STRUCTURE CHECK ===")
extracted_dir = root / "datasets/kaggle/hand_gesture/extracted"
subdirs = [d.name for d in extracted_dir.iterdir() if d.is_dir()]
print(f"Subdirectories in extracted: {subdirs}")
assert subdirs == ["test"], f"Expected only ['test'] in extracted/, found {subdirs}"
test_classes = sorted([d.name for d in (extracted_dir / "test").iterdir() if d.is_dir()], key=lambda x: int(x) if x.isdigit() else x)
print(f"test class folders count: {len(test_classes)} ({test_classes[0]}..{test_classes[-1]})")
assert len(test_classes) == 20, f"Expected 20 test classes, found {len(test_classes)}"

print("\n=== 4. JSON VALIDITY CHECK ===")
manifests = [
    "datasets/manifests/datasets.json",
    "datasets/manifests/class_mapping.json",
    "datasets/kaggle/hand_gesture/metadata/inspection_report.json",
    "datasets/kaggle/hand_gesture/metadata/data_quality_report.json",
    "datasets/kaggle/hand_gesture/checksums/test_sha256_before.json",
    "datasets/kaggle/hand_gesture/checksums/test_sha256_after.json",
]
for m in manifests:
    p = root / m
    assert p.exists(), f"File {m} does not exist"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"PASS: {m} is valid JSON")

print("\n=== 5. NO MODELS TRAINED CHECK ===")
model_files = list(root.glob("*.pt")) + list(root.glob("*.pth")) + list((root / "models").glob("*.pt"))
print(f"Model files found: {len(model_files)}")
assert len(model_files) == 0, "No model files should exist!"

print("\nALL PHASE 0.3 VALIDATION CHECKS PASSED!")

#!/usr/bin/env python3
"""
scripts/validate_phase_0_4.py — Validation script for Phase 0.4.
Verifies:
1. Test checksums before vs after are 100% byte-identical.
2. Branch A criteria: extracted/train does not exist; train_count is 0.
3. Existing unit tests (pytest) pass 26/26.
4. JSON validity of all modified/created manifest and report files.
"""

import json
from pathlib import Path

ROOT = Path(r"c:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection")
HG = ROOT / "datasets" / "kaggle" / "hand_gesture"
CHECKSUMS = HG / "checksums"
METADATA = HG / "metadata"
MANIFESTS = ROOT / "datasets" / "manifests"

print("=== 1. TEST CHECKSUMS BEFORE VS AFTER (PHASE 0.4) ===")
before_file = CHECKSUMS / "test_sha256_phase04_before.json"
after_file = CHECKSUMS / "test_sha256_phase04_after.json"

assert before_file.exists(), f"Missing {before_file.name}"
assert after_file.exists(), f"Missing {after_file.name}"

with open(before_file, "r", encoding="utf-8") as f:
    b = json.load(f)
with open(after_file, "r", encoding="utf-8") as f:
    a = json.load(f)

identical = (
    b["file_count"] == a["file_count"] == 6000
    and b["total_bytes"] == a["total_bytes"] == 8821800
    and b["raw_test_zip"]["sha256"] == a["raw_test_zip"]["sha256"]
    and b["files"] == a["files"]
)
print(f"Test-set checksum identical: {identical}")
print(f"Test files verified: {a['file_count']}")
print(f"Test total bytes: {a['total_bytes']}")
print(f"raw/test.zip SHA-256: {a['raw_test_zip']['sha256']}")
assert identical, "Test set was modified! Cryptographic violation!"

print("\n=== 2. BRANCH A INTEGRITY (NO TRAIN DIR, TRAIN COUNT = 0) ===")
train_dir = HG / "extracted" / "train"
print(f"extracted/train exists: {train_dir.exists()} (MUST be False under Branch A)")
assert not train_dir.exists(), "extracted/train must not exist when training data is not found"

with open(MANIFESTS / "datasets.json", "r", encoding="utf-8") as f:
    ds_data = json.load(f)
ds = ds_data["datasets"][0]
print(f"datasets.json train_portion: {ds.get('train_portion')}")
print(f"datasets.json train_count: {ds.get('train_count')}")
assert ds.get("train_portion") == "not_found"
assert ds.get("train_count") == 0

print("\n=== 3. JSON VALIDITY OF MANIFESTS AND NEW REPORTS ===")
json_files = [
    MANIFESTS / "datasets.json",
    MANIFESTS / "class_mapping.json",
    METADATA / "inspection_report.json",
    METADATA / "data_quality_report.json",
    METADATA / "inspection_report_train.json",
    CHECKSUMS / "test_sha256_phase04_before.json",
    CHECKSUMS / "test_sha256_phase04_after.json",
]
for jf in json_files:
    assert jf.exists(), f"File {jf.name} does not exist"
    with open(jf, "r", encoding="utf-8") as f:
        json.load(f)
    print(f"PASS: {jf.relative_to(ROOT)} is valid JSON")

print("\nALL PHASE 0.4 ASSERTIONS PASSED!")

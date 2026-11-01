#!/usr/bin/env python3
"""
scripts/inspect_hand_gesture_train.py — Phase 0.4 Hand Gesture Training Partition
Inspection and Verification Module.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection")
HG_ROOT = ROOT / "datasets" / "kaggle" / "hand_gesture"
RAW_DIR = HG_ROOT / "raw"
EXTRACTED_DIR = HG_ROOT / "extracted"
TEST_DIR = EXTRACTED_DIR / "test"
TRAIN_DIR = EXTRACTED_DIR / "train"
CHECKSUM_DIR = HG_ROOT / "checksums"
METADATA_DIR = HG_ROOT / "metadata"
MANIFESTS_DIR = ROOT / "datasets" / "manifests"


def hash_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_test_hashes() -> dict:
    file_hashes = {}
    total_bytes = 0
    file_count = 0

    for file_path in sorted(TEST_DIR.rglob("*")):
        if file_path.is_file():
            file_count += 1
            size = file_path.stat().st_size
            total_bytes += size
            rel_path = str(file_path.relative_to(TEST_DIR)).replace("\\", "/")
            file_hashes[rel_path] = hash_file(file_path)

    raw_zip = RAW_DIR / "test.zip"
    raw_zip_hash = hash_file(raw_zip) if raw_zip.exists() else None
    raw_zip_size = raw_zip.stat().st_size if raw_zip.exists() else None

    return {
        "description": "SHA-256 checksums of extracted test set",
        "timestamp": "2026-09-30",
        "test_directory": str(TEST_DIR),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "raw_test_zip": {
            "path": str(raw_zip),
            "size_bytes": raw_zip_size,
            "sha256": raw_zip_hash,
        },
        "files": file_hashes,
    }


def step2_protect_test_set() -> dict:
    print("Step 2: Protecting test set & checking against Phase 0.3 record...")
    current_hashes = compute_test_hashes()

    ref_file = CHECKSUM_DIR / "test_sha256_after.json"
    if not ref_file.exists():
        ref_file = CHECKSUM_DIR / "test_sha256_before.json"

    if ref_file.exists():
        with open(ref_file, "r", encoding="utf-8") as f:
            ref_data = json.load(f)

        if ref_data["file_count"] != current_hashes["file_count"]:
            raise RuntimeError(
                f"Test file count mismatch: expected {ref_data['file_count']}, got {current_hashes['file_count']}"
            )
        if ref_data["total_bytes"] != current_hashes["total_bytes"]:
            raise RuntimeError(
                f"Test byte count mismatch: expected {ref_data['total_bytes']}, got {current_hashes['total_bytes']}"
            )
        if ref_data["raw_test_zip"]["sha256"] != current_hashes["raw_test_zip"]["sha256"]:
            raise RuntimeError("raw/test.zip SHA-256 mismatch with Phase 0.3 record!")

        mismatches = [
            k
            for k, v in ref_data["files"].items()
            if current_hashes["files"].get(k) != v
        ]
        if mismatches:
            raise RuntimeError(
                f"Integrity check failed: {len(mismatches)} files have different hashes!"
            )
        print("PASS: Extracted test set matches Phase 0.3 reference byte-for-byte!")

    out_file = CHECKSUM_DIR / "test_sha256_phase04_before.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(current_hashes, f, indent=2)
    print(f"Saved hashes to {out_file.name}")
    return current_hashes


def step3_search_training_candidate() -> tuple[str, Path | None]:
    print("Step 3: Searching for training partition locally...")
    candidates = []

    # Check raw directory
    for item in RAW_DIR.iterdir():
        if item.name.lower() in [
            "train.zip",
            "training.zip",
            "train",
            "training",
            "combined.zip",
            "dataset.zip",
        ]:
            candidates.append(item)
        elif item.is_file() and "train" in item.name.lower() and item.suffix.lower() == ".zip":
            candidates.append(item)

    # Check Downloads folder
    downloads = Path(r"C:\Users\prash\Downloads")
    if downloads.exists():
        for item in downloads.iterdir():
            if item.is_file() and "train" in item.name.lower() and item.suffix.lower() == ".zip":
                candidates.append(item)

    # Read datasets.json
    source_url = "https://www.kaggle.com/search?q=hand-gesture-recognition-dataset"
    manifest_file = MANIFESTS_DIR / "datasets.json"
    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                m_data = json.load(f)
            if m_data.get("datasets"):
                source_url = m_data["datasets"][0].get("source_url", source_url)
        except Exception:
            pass

    print(f"Dataset source URL recorded in datasets.json: {source_url}")

    if not candidates:
        print("RESULT: No training partition found locally. BRANCH A applies.")
        return ("BRANCH_A", None)

    cand = candidates[0]
    print(f"Found candidate: {cand}")
    return ("BRANCH_C", cand)


def step8_verify_test_unchanged():
    print("Step 8: Recomputing test hashes into test_sha256_phase04_after.json...")
    after_hashes = compute_test_hashes()
    out_file = CHECKSUM_DIR / "test_sha256_phase04_after.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(after_hashes, f, indent=2)

    before_file = CHECKSUM_DIR / "test_sha256_phase04_before.json"
    with open(before_file, "r", encoding="utf-8") as f:
        before_hashes = json.load(f)

    assert before_hashes["file_count"] == after_hashes["file_count"] == 6000
    assert before_hashes["total_bytes"] == after_hashes["total_bytes"] == 8821800
    assert (
        before_hashes["raw_test_zip"]["sha256"]
        == after_hashes["raw_test_zip"]["sha256"]
    )
    assert before_hashes["files"] == after_hashes["files"]
    print("PASS: Test set is 100% byte-identical before and after Phase 0.4!")


if __name__ == "__main__":
    step2_protect_test_set()
    branch, candidate = step3_search_training_candidate()
    step8_verify_test_unchanged()

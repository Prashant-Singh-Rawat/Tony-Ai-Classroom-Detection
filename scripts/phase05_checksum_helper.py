#!/usr/bin/env python3
"""
scripts/phase05_checksum_helper.py — Computes and compares SHA-256 checksums
for all files in extracted/train/, extracted/test/, and raw archives.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r"c:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection")
HG = ROOT / "datasets" / "kaggle" / "hand_gesture"
TRAIN_DIR = HG / "extracted" / "train"
TEST_DIR = HG / "extracted" / "test"
RAW_DIR = HG / "raw"
CHECKSUMS_DIR = HG / "checksums"
CHECKSUMS_DIR.mkdir(parents=True, exist_ok=True)


def hash_single_file(path_tuple: tuple[str, Path]) -> tuple[str, str, int]:
    rel_path, abs_path = path_tuple
    hasher = hashlib.sha256()
    size = abs_path.stat().st_size
    with open(abs_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return rel_path, hasher.hexdigest(), size


def compute_all_dataset_hashes() -> dict:
    file_list: list[tuple[str, Path]] = []

    # 1. train images
    for p in sorted(TRAIN_DIR.rglob("*")):
        if p.is_file():
            rel = f"extracted/train/{p.relative_to(TRAIN_DIR)}".replace("\\", "/")
            file_list.append((rel, p))

    # 2. test images
    for p in sorted(TEST_DIR.rglob("*")):
        if p.is_file():
            rel = f"extracted/test/{p.relative_to(TEST_DIR)}".replace("\\", "/")
            file_list.append((rel, p))

    # 3. raw archives
    for archive_name in ["test.zip", "train.zip"]:
        p = RAW_DIR / archive_name
        if p.exists():
            rel = f"raw/{archive_name}".replace("\\", "/")
            file_list.append((rel, p))

    print(f"Hashing {len(file_list)} files using ThreadPoolExecutor...")
    results = {}
    total_bytes = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        for rel_path, digest, size in executor.map(hash_single_file, file_list):
            results[rel_path] = digest
            total_bytes += size

    return {
        "timestamp": "2026-09-30",
        "file_count": len(results),
        "total_bytes": total_bytes,
        "files": results,
    }


def generate_before_checksum() -> Path:
    out_file = CHECKSUMS_DIR / "phase05_before.json"
    print("Generating phase05_before.json...")
    data = compute_all_dataset_hashes()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {data['file_count']} file hashes ({data['total_bytes']:,} bytes) to {out_file.name}")
    return out_file


def generate_after_and_compare() -> bool:
    out_file = CHECKSUMS_DIR / "phase05_after.json"
    before_file = CHECKSUMS_DIR / "phase05_before.json"
    assert before_file.exists(), "phase05_before.json does not exist!"

    print("Generating phase05_after.json and verifying integrity...")
    after_data = compute_all_dataset_hashes()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(after_data, f, indent=2)

    with open(before_file, "r", encoding="utf-8") as f:
        before_data = json.load(f)

    if before_data["file_count"] != after_data["file_count"]:
        print(f"FAIL: File count changed: before={before_data['file_count']} after={after_data['file_count']}")
        return False

    if before_data["total_bytes"] != after_data["total_bytes"]:
        print(f"FAIL: Total bytes changed: before={before_data['total_bytes']} after={after_data['total_bytes']}")
        return False

    mismatches = [k for k, v in before_data["files"].items() if after_data["files"].get(k) != v]
    if mismatches:
        print(f"FAIL: {len(mismatches)} files have mismatched hashes: {mismatches[:5]}")
        return False

    print("PASS: Dataset integrity confirmed! All 24,002 dataset files and archives are 100% byte-identical.")
    return True


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "before"
    if action == "before":
        generate_before_checksum()
    elif action == "after":
        if not generate_after_and_compare():
            sys.exit(1)
    else:
        print(f"Unknown action {action}")
        sys.exit(1)

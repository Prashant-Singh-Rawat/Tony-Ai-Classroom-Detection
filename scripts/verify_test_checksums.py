#!/usr/bin/env python3
"""
verify_test_checksums.py — Verifies that the extracted test set and test.zip remain
100% byte-identical to their pre-import state.
"""

import hashlib
import json
from pathlib import Path


def main():
    root = Path(r"c:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection\datasets\kaggle\hand_gesture")
    test_dir = root / "extracted" / "test"
    raw_zip = root / "raw" / "test.zip"
    checksum_dir = root / "checksums"
    checksum_dir.mkdir(parents=True, exist_ok=True)

    print(f"Recomputing SHA-256 for all files in {test_dir}...")
    file_hashes = {}
    total_bytes = 0
    file_count = 0

    for file_path in sorted(test_dir.rglob("*")):
        if file_path.is_file():
            file_count += 1
            size = file_path.stat().st_size
            total_bytes += size
            rel_path = str(file_path.relative_to(test_dir)).replace("\\", "/")
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            file_hashes[rel_path] = hasher.hexdigest()

    raw_zip_hash = None
    raw_zip_size = None
    if raw_zip.exists():
        raw_zip_size = raw_zip.stat().st_size
        hasher = hashlib.sha256()
        with open(raw_zip, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        raw_zip_hash = hasher.hexdigest()

    after_data = {
        "description": "SHA-256 checksums of extracted test set after Step 8 verification",
        "timestamp": "2026-09-30",
        "test_directory": str(test_dir),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "raw_test_zip": {
            "path": str(raw_zip),
            "size_bytes": raw_zip_size,
            "sha256": raw_zip_hash,
        },
        "files": file_hashes,
    }

    after_path = checksum_dir / "test_sha256_after.json"
    with open(after_path, "w", encoding="utf-8") as f:
        json.dump(after_data, f, indent=2)

    print(f"Saved after record to {after_path}")

    # Compare before vs after
    before_path = checksum_dir / "test_sha256_before.json"
    with open(before_path, "r", encoding="utf-8") as f:
        before_data = json.load(f)

    # Assertions
    assert before_data["file_count"] == after_data["file_count"], (
        f"File count mismatch: before={before_data['file_count']}, after={after_data['file_count']}"
    )
    assert before_data["total_bytes"] == after_data["total_bytes"], (
        f"Total bytes mismatch: before={before_data['total_bytes']}, after={after_data['total_bytes']}"
    )
    assert before_data["raw_test_zip"]["sha256"] == after_data["raw_test_zip"]["sha256"], (
        "raw/test.zip SHA-256 mismatch!"
    )

    mismatches = []
    missing_in_after = []
    new_in_after = []

    for rel_p, b_hash in before_data["files"].items():
        if rel_p not in after_data["files"]:
            missing_in_after.append(rel_p)
        elif after_data["files"][rel_p] != b_hash:
            mismatches.append(rel_p)

    for rel_p in after_data["files"]:
        if rel_p not in before_data["files"]:
            new_in_after.append(rel_p)

    if not mismatches and not missing_in_after and not new_in_after:
        print("RESULT: ALL 6000 FILES AND RAW/TEST.ZIP ARE 100% BYTE-IDENTICAL!")
        print("TEST INTEGRITY CHECK: PASS")
        return 0
    else:
        print("RESULT: INTEGRITY FAILURE!")
        print(f"Mismatches: {len(mismatches)}")
        print(f"Missing: {len(missing_in_after)}")
        print(f"New: {len(new_in_after)}")
        return 1


if __name__ == "__main__":
    exit(main())

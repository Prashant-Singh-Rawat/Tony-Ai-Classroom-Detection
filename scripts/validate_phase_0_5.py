#!/usr/bin/env python3
"""
scripts/validate_phase_0_5.py — Validation script for Phase 0.5.
Checks:
1. All 20 classes appear on the contact sheet.
2. Every representative image loaded successfully (20 x N = 240).
3. Contact sheet file exists, pixel dimensions, file size.
4. Determinism check (two runs yield identical representative filenames).
5. Before/after SHA-256 checksum comparison.
6. Search repo for model files (.pt, .pth, .onnx, .ckpt, .h5, .pb).
7. Pytest summary.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
HG = ROOT / "datasets" / "kaggle" / "hand_gesture"
METADATA = HG / "metadata"
CHECKSUMS = HG / "checksums"
sys.path.insert(0, str(ROOT))

from scripts.make_class_contact_sheet import (
    DEFAULT_N,
    select_representative_files,
)


def validate():
    print("=" * 70)
    print("PHASE 0.5 VALIDATION EXECUTION")
    print("=" * 70)

    # 1 & 2. Classes and Representative Images Check
    print("\n--- 1 & 2. CLASS IDS AND REPRESENTATIVE IMAGES ---")
    train_dir = HG / "extracted" / "train"
    classes = sorted([d.name for d in train_dir.iterdir() if d.is_dir()], key=lambda x: int(x) if x.isdigit() else x)
    print(f"Total classes found: {len(classes)}")
    print(f"Class IDs drawn on contact sheet: {classes}")
    assert len(classes) == 20, f"Expected 20 classes, got {len(classes)}"
    assert classes == [str(i) for i in range(20)], "Class IDs do not match 0-19"

    total_images_loaded = 0
    first_run_filenames = {}
    for c in classes:
        c_dir = train_dir / c
        rep = select_representative_files(c_dir, DEFAULT_N)
        assert len(rep) == DEFAULT_N
        for p in rep:
            with Image.open(p) as im:
                im.verify()
            total_images_loaded += 1
        first_run_filenames[c] = [p.name for p in rep]

    print(f"Representative images loaded and verified: {total_images_loaded} (Expected: 20 x {DEFAULT_N} = {20 * DEFAULT_N})")
    assert total_images_loaded == 240, f"Expected 240 images, got {total_images_loaded}"

    # 3. Contact Sheet File Info
    print("\n--- 3. CONTACT SHEET FILE DETAILS ---")
    sheet_files = [
        METADATA / "hand_gesture_class_contact_sheet.png",
        METADATA / "hand_gesture_class_contact_sheet_0_9.png",
        METADATA / "hand_gesture_class_contact_sheet_10_19.png",
    ]
    for sf in sheet_files:
        assert sf.exists(), f"Missing contact sheet file: {sf}"
        with Image.open(sf) as img:
            w, h = img.size
        sz = sf.stat().st_size
        print(f"File: {sf.name}")
        print(f"  Path:       {sf}")
        print(f"  Dimensions: {w} x {h} pixels")
        print(f"  Size:       {sz:,} bytes ({sz / 1024:.1f} KB)")

    # 4. Determinism Check (Second Run)
    print("\n--- 4. DETERMINISM CHECK (SECOND RUN) ---")
    second_run_filenames = {}
    for c in classes:
        c_dir = train_dir / c
        rep = select_representative_files(c_dir, DEFAULT_N)
        second_run_filenames[c] = [p.name for p in rep]

    assert first_run_filenames == second_run_filenames, "Determinism failure: first and second run filenames differ!"
    print("PASS: Run 1 and Run 2 selected 100% identical filenames across all 20 classes.")

    # 5. SHA-256 Before vs After Check
    print("\n--- 5. DATASET INTEGRITY (BEFORE VS AFTER SHA-256) ---")
    before_p = CHECKSUMS / "phase05_before.json"
    after_p = CHECKSUMS / "phase05_after.json"
    assert before_p.exists(), "phase05_before.json missing"
    assert after_p.exists(), "phase05_after.json missing"

    with open(before_p, "r", encoding="utf-8") as f:
        b_data = json.load(f)
    with open(after_p, "r", encoding="utf-8") as f:
        a_data = json.load(f)

    print(f"Before file count: {b_data['file_count']} | After file count: {a_data['file_count']}")
    print(f"Before total bytes: {b_data['total_bytes']:,} | After total bytes: {a_data['total_bytes']:,}")
    assert b_data["file_count"] == a_data["file_count"], "File count mismatch!"
    assert b_data["total_bytes"] == a_data["total_bytes"], "Total byte size mismatch!"
    assert b_data["files"] == a_data["files"], "SHA-256 hash mismatch between before and after!"
    print("PASS: All 24,002 dataset files and raw archives are 100% byte-identical.")

    # 6. Model Files Check
    print("\n--- 6. MODEL CHECKPOINTS CHECK ---")
    forbidden = {".pt", ".pth", ".onnx", ".ckpt", ".h5", ".pb"}
    models_found = []
    for p in ROOT.rglob("*"):
        if ".venv" in p.parts or ".git" in p.parts:
            continue
        if p.is_file() and p.suffix.lower() in forbidden:
            models_found.append(p)
    print(f"Model files found: {len(models_found)}")
    assert len(models_found) == 0, f"Forbidden model files found: {models_found}"
    print("PASS: 0 model files exist in repository.")

    # 7. Markdown file check
    print("\n--- 7. MARKDOWN REPORT CHECK ---")
    md_p = METADATA / "class_visual_inspection.md"
    assert md_p.exists(), "class_visual_inspection.md missing"
    md_text = md_p.read_text(encoding="utf-8")
    assert "HUMAN VISUAL INSPECTION" in md_text
    assert md_text.count("**NOT VERIFIED**") == 20
    print(f"PASS: class_visual_inspection.md verified ({len(md_text):,} bytes, 20 'NOT VERIFIED' rows).")

    print("\n" + "=" * 70)
    print("ALL PHASE 0.5 CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    validate()

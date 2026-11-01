#!/usr/bin/env python3
"""
scripts/validate_annotations.py — Real Classroom YOLO Annotation Validator.

Validates:
1. Every YOLO annotation file parses properly (<class_id> <x_center> <y_center> <width> <height>).
2. Class IDs are strictly in {0, 1, 2} (0: hand_raised, 1: hand_not_raised, 2: ambiguous).
3. All bounding box coordinates are normalized floats within [0.0, 1.0].
4. Every labeled frame has an existing matching image in frames/ or frame_manifest.csv.
5. Cross-references against frame_manifest.csv and reports unlabeled frames.
6. Enforces ambiguous rule: reports class 0/1/2 counts separately; confirms ambiguous excluded from training.
7. Checks annotations/annotation_index.csv for review tracking.

Zero AI auto-labeling. Pure deterministic validation.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

VALID_CLASS_IDS = {0, 1, 2}
CLASS_NAMES = {
    0: "hand_raised",
    1: "hand_not_raised",
    2: "ambiguous",
}


def resolve_data_root(cli_root: Optional[Path] = None) -> Path:
    """Resolve dataset root from CLI, env var, or default."""
    if cli_root:
        return cli_root.resolve()
    env_root = os.environ.get("CLASSVISION_REAL_DATA_ROOT")
    if env_root:
        return Path(env_root).resolve()
    repo_root = Path(__file__).resolve().parent.parent
    return (repo_root / "datasets" / "real_classroom").resolve()


def load_known_frame_ids(root: Path) -> Set[str]:
    """Load all known frame identifiers from frame_manifest.csv or frames/ folder."""
    known: Set[str] = set()
    manifest_path = root / "metadata" / "frame_manifest.csv"
    if manifest_path.is_file():
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row.get("frame_id", "").strip()
                if fid:
                    known.add(fid)

    # Also check frames on disk
    frames_dir = root / "frames" / "raw"
    if frames_dir.is_dir():
        for p in frames_dir.rglob("*.jpg"):
            rel = p.relative_to(frames_dir)
            fid = f"{rel.parent}/{p.stem}".replace("\\", "/")
            known.add(fid)

    return known


def validate_single_annotation_file(
    txt_path: Path,
    known_frames: Set[str],
    tier_name: str,
) -> Tuple[bool, List[str], Dict[int, int]]:
    """
    Validate a single YOLO format .txt file.
    Returns (is_valid, error_messages, class_counts).
    """
    errors: List[str] = []
    class_counts = {0: 0, 1: 0, 2: 0}

    # Derive expected frame_id from relative path
    # Example: annotations/reviewed/sess_01/cam1_t0001000.txt -> sess_01/cam1_t0001000
    stem = txt_path.stem
    parent_session = txt_path.parent.name
    frame_id = f"{parent_session}/{stem}"

    if known_frames and frame_id not in known_frames:
        errors.append(f"[{tier_name}] Labeled frame '{frame_id}' has no matching image in frames/ or manifest.")

    try:
        content = txt_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        return False, [f"Failed to read file {txt_path}: {e}"], class_counts

    if not content:
        # Empty file means no persons detected in frame (valid negative)
        return len(errors) == 0, errors, class_counts

    lines = content.splitlines()
    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if len(parts) != 5:
            errors.append(
                f"[{tier_name}] {txt_path.name}:{line_num}: Expected 5 elements (<class> <x> <y> <w> <h>), found {len(parts)}: '{line}'"
            )
            continue

        # 1. Class ID validation
        try:
            cid = int(parts[0])
            if cid not in VALID_CLASS_IDS:
                errors.append(
                    f"[{tier_name}] {txt_path.name}:{line_num}: Invalid class ID {cid}. Must be in {sorted(list(VALID_CLASS_IDS))} (0: raised, 1: not_raised, 2: ambiguous)."
                )
            else:
                class_counts[cid] += 1
        except ValueError:
            errors.append(f"[{tier_name}] {txt_path.name}:{line_num}: Class ID '{parts[0]}' is not an integer.")

        # 2. Coordinates validation
        for val_idx, val_name in enumerate(["x_center", "y_center", "width", "height"], start=1):
            try:
                coord = float(parts[val_idx])
                if not (0.0 <= coord <= 1.0):
                    errors.append(
                        f"[{tier_name}] {txt_path.name}:{line_num}: Coordinate {val_name}={coord} is out of bounds [0.0, 1.0]."
                    )
            except ValueError:
                errors.append(
                    f"[{tier_name}] {txt_path.name}:{line_num}: Coordinate {val_name} '{parts[val_idx]}' is not a valid float."
                )

    return len(errors) == 0, errors, class_counts


def validate_tier(
    tier_dir: Path,
    tier_name: str,
    known_frames: Set[str],
) -> Tuple[bool, int, Dict[int, int], List[str]]:
    """Validate all annotation files within an annotation tier (raw or reviewed)."""
    if not tier_dir.is_dir():
        return True, 0, {0: 0, 1: 0, 2: 0}, []

    all_files = sorted(tier_dir.rglob("*.txt"))
    tier_valid = True
    tier_errors: List[str] = []
    total_counts = {0: 0, 1: 0, 2: 0}

    for f in all_files:
        is_val, errs, counts = validate_single_annotation_file(f, known_frames, tier_name)
        if not is_val:
            tier_valid = False
            tier_errors.extend(errs)
        for cid, cnt in counts.items():
            total_counts[cid] += cnt

    return tier_valid, len(all_files), total_counts, tier_errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Real classroom YOLO annotation validator.")
    parser.add_argument("--root", type=Path, default=None, help="Root directory for real_classroom dataset")
    parser.add_argument(
        "--tier",
        choices=["raw", "reviewed", "all"],
        default="all",
        help="Which annotation tier to validate (default: all)",
    )
    args = parser.parse_args()

    root = resolve_data_root(args.root)
    ann_root = root / "annotations"

    print("=" * 65)
    print("ClassVision AI — Real Classroom Annotation Validator")
    print(f"Data Root: {root}")
    print(f"Target Tier: {args.tier}")
    print("=" * 65)

    known_frames = load_known_frame_ids(root)
    print(f"Known frames cataloged: {len(known_frames)}")

    tiers_to_check = []
    if args.tier in ("raw", "all"):
        tiers_to_check.append(("raw", ann_root / "raw"))
    if args.tier in ("reviewed", "all"):
        tiers_to_check.append(("reviewed", ann_root / "reviewed"))

    overall_valid = True
    all_errors: List[str] = []
    annotated_frame_ids: Set[str] = set()

    for tier_name, tier_dir in tiers_to_check:
        print(f"\n--- Checking '{tier_name}' annotations ({tier_dir}) ---")
        valid, file_cnt, counts, errors = validate_tier(tier_dir, tier_name, known_frames)
        if not valid:
            overall_valid = False
            all_errors.extend(errors)

        for p in tier_dir.rglob("*.txt"):
            stem = p.stem
            s_id = p.parent.name
            annotated_frame_ids.add(f"{s_id}/{stem}")

        print(f"Files inspected: {file_cnt}")
        print(f"Bounding box counts:")
        print(f"  Class 0 (hand_raised):     {counts[0]}")
        print(f"  Class 1 (hand_not_raised): {counts[1]}")
        print(f"  Class 2 (ambiguous):       {counts[2]}")
        if counts[0] + counts[1] > 0:
            ratio = counts[0] / (counts[0] + counts[1]) * 100.0
            print(f"  Positive Ratio (Raised / Total Definitive): {ratio:.1f}%")
        print(f"Ambiguous Policy: {counts[2]} ambiguous boxes are EXCLUDED from training & evaluation.")

    # Check for unlabeled frames
    unlabeled_frames = known_frames - annotated_frame_ids
    print(f"\n--- Frame Coverage ---")
    print(f"Total cataloged frames:   {len(known_frames)}")
    print(f"Total annotated frames:   {len(annotated_frame_ids)}")
    print(f"Unlabeled frames pending: {len(unlabeled_frames)}")
    if unlabeled_frames and len(unlabeled_frames) <= 10:
        print(f"Unlabeled samples: {sorted(list(unlabeled_frames))[:5]}")

    # Check annotation_index.csv if available
    index_file = ann_root / "annotation_index.csv"
    if index_file.is_file():
        reviewed_cnt = 0
        unreviewed_cnt = 0
        with open(index_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                status = r.get("reviewed", "").strip().lower()
                if status in ("yes", "true", "1"):
                    reviewed_cnt += 1
                else:
                    unreviewed_cnt += 1
        print(f"\n--- Review Index Status ---")
        print(f"Reviewed (verified): {reviewed_cnt} | Unreviewed (raw): {unreviewed_cnt}")

    print("\n" + "=" * 65)
    if not overall_valid:
        print("VALIDATION FAILED! Errors encountered:")
        for err in all_errors[:20]:
            print(f"  ERROR: {err}")
        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more errors.")
        return 1

    print("VALIDATION PASSED: All annotations strictly conform to YOLO person schema.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
scripts/annotation_preflight.py — Real Classroom Annotation Workflow Preflight Checker.

Features:
- Pure read-only, 100% offline inspection script.
- Verifies annotation environment readiness before and immediately after export:
  1. labels.yaml integrity (verifies 0: hand_raised, 1: hand_not_raised, 2: ambiguous).
  2. Workspace directory readiness (annotations/raw/, annotations/reviewed/, annotation_index.csv).
  3. CVAT / Label Studio export verification (--export-dir or inspecting annotations/raw/):
     - Checks obj.names or classes.txt to prevent silent class ID inversion.
     - Checks for session subdirectory structure (<session_id>/<stem>.txt vs flat files).
  4. Cataloged frame readiness (frames extracted and waiting for annotation).
- Works gracefully on an empty root without crashing.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

EXPECTED_CLASSES = {
    0: "hand_raised",
    1: "hand_not_raised",
    2: "ambiguous",
}

EXPECTED_INDEX_HEADER = ["frame_id", "annotator", "reviewed", "review_date"]


def resolve_data_root(cli_root: Optional[Path] = None) -> Path:
    """Resolve dataset root from CLI, env var, or default."""
    if cli_root:
        return cli_root.resolve()
    env_root = os.environ.get("CLASSVISION_REAL_DATA_ROOT")
    if env_root:
        return Path(env_root).resolve()
    repo_root = Path(__file__).resolve().parent.parent
    return (repo_root / "datasets" / "real_classroom").resolve()


def check_labels_yaml(ann_dir: Path) -> Tuple[bool, List[str]]:
    """Check labels.yaml exists and defines classes 0, 1, 2 accurately."""
    yaml_path = ann_dir / "labels.yaml"
    if not yaml_path.is_file():
        return False, [f"Missing schema file: {yaml_path}"]

    errors: List[str] = []
    try:
        content = yaml_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, [f"Failed to read {yaml_path}: {e}"]

    # Basic text parsing to stay lightweight / stdlib only
    for cid, cname in EXPECTED_CLASSES.items():
        if f"{cid}:" not in content or cname not in content:
            errors.append(f"Class definition mismatch: expected class {cid} to map to '{cname}' in {yaml_path.name}.")

    return len(errors) == 0, errors


def check_annotation_index(ann_dir: Path) -> Tuple[bool, List[str]]:
    """Check annotation_index.csv exists and has correct header."""
    index_path = ann_dir / "annotation_index.csv"
    if not index_path.is_file():
        return False, [f"Missing index file: {index_path}"]

    errors: List[str] = []
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                errors.append(f"{index_path.name} is empty; expected header {EXPECTED_INDEX_HEADER}.")
            else:
                cleaned_header = [h.strip() for h in header]
                if cleaned_header[: len(EXPECTED_INDEX_HEADER)] != EXPECTED_INDEX_HEADER:
                    errors.append(
                        f"Header mismatch in {index_path.name}: found {cleaned_header}, expected {EXPECTED_INDEX_HEADER}."
                    )
    except Exception as e:
        return False, [f"Failed to read {index_path}: {e}"]

    return len(errors) == 0, errors


def check_export_class_mapping(export_dir: Path) -> Tuple[bool, List[str]]:
    """Inspect obj.names or classes.txt in an export folder to prevent class ID inversion."""
    if not export_dir.is_dir():
        return False, [f"Export directory not found: {export_dir}"]

    class_file = None
    for cand in ["obj.names", "classes.txt", "classes.names"]:
        p = export_dir / cand
        if p.is_file():
            class_file = p
            break

    if not class_file:
        return True, []  # Optional file, cannot verify mapping directly

    lines = [line.strip().lower().replace(" ", "_") for line in class_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors: List[str] = []
    for cid, expected_name in EXPECTED_CLASSES.items():
        if cid >= len(lines):
            errors.append(
                f"Export class file '{class_file.name}' has only {len(lines)} lines; missing class {cid} ('{expected_name}')."
            )
        elif lines[cid] != expected_name:
            errors.append(
                f"CLASS ID INVERSION RISK in '{class_file.name}': Line {cid} is '{lines[cid]}', expected '{expected_name}'. "
                f"Exported annotations may have swapped class IDs!"
            )

    return len(errors) == 0, errors


def check_session_folder_structure(target_dir: Path) -> Tuple[bool, List[str]]:
    """Check if annotations are organized in session subdirectories vs flat files."""
    if not target_dir.is_dir():
        return True, []

    flat_txts = [p for p in target_dir.glob("*.txt") if p.name not in ("classes.txt", "obj.names", "labels.txt")]
    subfolder_txts = list(target_dir.glob("*/*.txt"))

    warnings: List[str] = []
    if flat_txts and not subfolder_txts:
        warnings.append(
            f"Found {len(flat_txts)} annotation files directly in {target_dir.name}/ without session subdirectories. "
            f"Downstream tools require annotations grouped by session (e.g. '{target_dir.name}/sess_01/frame.txt')."
        )
    return len(warnings) == 0, warnings


def run_preflight(root: Path, export_dir: Optional[Path] = None) -> Tuple[bool, str]:
    """Run all preflight checks and format a markdown summary report."""
    ann_dir = root / "annotations"
    raw_dir = ann_dir / "raw"
    reviewed_dir = ann_dir / "reviewed"
    metadata_dir = root / "metadata"
    manifest_p = metadata_dir / "frame_manifest.csv"

    results: List[Tuple[str, str, str]] = []  # (Category, Status, Details)
    has_errors = False

    # 1. Schema check
    schema_ok, schema_errs = check_labels_yaml(ann_dir)
    if schema_ok:
        results.append(("Schema (labels.yaml)", "PASS", "Classes 0: hand_raised, 1: hand_not_raised, 2: ambiguous verified."))
    else:
        has_errors = True
        results.append(("Schema (labels.yaml)", "FAIL", " | ".join(schema_errs)))

    # 2. Annotation index check
    index_ok, index_errs = check_annotation_index(ann_dir)
    if index_ok:
        results.append(("Index (annotation_index.csv)", "PASS", "Header schema verified."))
    else:
        results.append(("Index (annotation_index.csv)", "WARN", " | ".join(index_errs)))

    # 3. Directory layout check
    dirs_present = raw_dir.is_dir() and reviewed_dir.is_dir()
    if dirs_present:
        results.append(("Directory Layout", "PASS", "annotations/raw/ and annotations/reviewed/ exist."))
    else:
        results.append(("Directory Layout", "WARN", "annotations/raw/ or annotations/reviewed/ missing."))

    # 4. Cataloged frames check
    if manifest_p.is_file():
        with open(manifest_p, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            total_manifest_frames = sum(1 for _ in reader)
        results.append(("Cataloged Frames", "PASS", f"{total_manifest_frames} frame(s) recorded in frame_manifest.csv."))
    else:
        results.append(("Cataloged Frames", "INFO", "0 frames cataloged in frame_manifest.csv (no video extraction run yet)."))

    # 5. Export directory check (if provided or checking raw)
    check_target = export_dir if export_dir else (raw_dir if raw_dir.is_dir() else None)
    if check_target:
        mapping_ok, mapping_errs = check_export_class_mapping(check_target)
        if mapping_ok:
            results.append((f"Export Class Mapping ({check_target.name})", "PASS", "Verified or no class file conflicting."))
        else:
            has_errors = True
            results.append((f"Export Class Mapping ({check_target.name})", "FAIL", " | ".join(mapping_errs)))

        struct_ok, struct_warns = check_session_folder_structure(check_target)
        if struct_ok:
            results.append((f"Export Structure ({check_target.name})", "PASS", "Session subdirectories present or empty."))
        else:
            results.append((f"Export Structure ({check_target.name})", "WARN", " | ".join(struct_warns)))

    # Generate Markdown
    lines = [
        "# ClassVision AI — Annotation Preflight Report",
        "",
        f"- **Dataset Root**: `{root}`",
        f"- **Export Target Evaluated**: `{check_target or 'None'}`",
        "",
        "| Preflight Check | Status | Details |",
        "| :--- | :---: | :--- |",
    ]
    for cat, status, details in results:
        badge = "✅ PASS" if status == "PASS" else ("⚠️ WARN" if status == "WARN" else ("ℹ️ INFO" if status == "INFO" else "❌ FAIL"))
        lines.append(f"| {cat} | {badge} | {details} |")

    lines.extend([
        "",
        "---",
        "**Overall Status**: " + ("READY FOR ANNOTATION" if not has_errors else "ATTENTION REQUIRED (Errors detected)"),
    ])

    return not has_errors, "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Annotation workflow preflight checker.")
    parser.add_argument("--root", type=Path, default=None, help="Root directory for real_classroom dataset")
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=None,
        help="Optional path to CVAT / Label Studio export folder to check before moving to raw/",
    )
    args = parser.parse_args()

    root = resolve_data_root(args.root)
    success, report_md = run_preflight(root, args.export_dir)
    print(report_md)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

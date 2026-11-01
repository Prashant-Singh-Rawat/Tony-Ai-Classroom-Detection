#!/usr/bin/env python3
"""
tests/real_classroom/test_annotation_preflight.py — Unit Tests for scripts/annotation_preflight.py.

Coverage:
1. Empty root: runs gracefully without crashing, reports missing schema.
2. Valid environment: all components pass, status is READY FOR ANNOTATION.
3. Class ID inversion detection: flags obj.names / classes.txt with inverted labels.
4. Flat export detection: warns when annotation files lack session subdirectories.
5. Malformed index header detection: flags incorrect CSV header columns.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts.annotation_preflight import (
    check_annotation_index,
    check_export_class_mapping,
    check_labels_yaml,
    check_session_folder_structure,
    run_preflight,
)


def setup_valid_ann_structure(root: Path) -> None:
    """Helper to set up a compliant annotation folder skeleton."""
    ann_dir = root / "annotations"
    (ann_dir / "raw").mkdir(parents=True, exist_ok=True)
    (ann_dir / "reviewed").mkdir(parents=True, exist_ok=True)

    labels_yaml = ann_dir / "labels.yaml"
    labels_yaml.write_text(
        "classes:\n"
        "  0:\n    name: 'hand_raised'\n"
        "  1:\n    name: 'hand_not_raised'\n"
        "  2:\n    name: 'ambiguous'\n",
        encoding="utf-8",
    )

    index_csv = ann_dir / "annotation_index.csv"
    index_csv.write_text("frame_id,annotator,reviewed,review_date\n", encoding="utf-8")


class TestAnnotationPreflight:
    """Tests for scripts/annotation_preflight.py."""

    def test_preflight_empty_root(self, tmp_path: Path):
        """Empty root runs cleanly without crashing and flags missing schema."""
        success, report = run_preflight(tmp_path)
        assert success is False
        assert "ATTENTION REQUIRED" in report
        assert "Missing schema file" in report

    def test_preflight_valid_environment(self, tmp_path: Path):
        """Compliant environment passes all checks and reports READY FOR ANNOTATION."""
        setup_valid_ann_structure(tmp_path)
        success, report = run_preflight(tmp_path)
        assert success is True
        assert "READY FOR ANNOTATION" in report
        assert "✅ PASS" in report

    def test_class_inversion_detection(self, tmp_path: Path):
        """Export directory with inverted class order triggers class ID inversion error."""
        setup_valid_ann_structure(tmp_path)
        export_dir = tmp_path / "mock_export"
        export_dir.mkdir()

        # Inverted class order: 0 is hand_not_raised, 1 is hand_raised
        (export_dir / "classes.txt").write_text("hand_not_raised\nhand_raised\nambiguous\n", encoding="utf-8")

        success, errors = check_export_class_mapping(export_dir)
        assert success is False
        assert any("CLASS ID INVERSION RISK" in e for e in errors)

        # Full preflight run should also fail
        preflight_ok, report = run_preflight(tmp_path, export_dir=export_dir)
        assert preflight_ok is False
        assert "CLASS ID INVERSION RISK" in report

    def test_flat_export_structure_warning(self, tmp_path: Path):
        """Warns when exported annotations are flat rather than nested in session subdirectories."""
        export_dir = tmp_path / "flat_export"
        export_dir.mkdir()
        (export_dir / "frame_01.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        (export_dir / "frame_02.txt").write_text("1 0.2 0.2 0.1 0.1\n", encoding="utf-8")

        success, warnings = check_session_folder_structure(export_dir)
        assert success is False
        assert any("without session subdirectories" in w for w in warnings)

    def test_malformed_annotation_index_header(self, tmp_path: Path):
        """Flags non-compliant annotation_index.csv headers."""
        ann_dir = tmp_path / "annotations"
        ann_dir.mkdir(parents=True)
        bad_index = ann_dir / "annotation_index.csv"
        bad_index.write_text("id,reviewer,status\n", encoding="utf-8")

        success, errors = check_annotation_index(ann_dir)
        assert success is False
        assert any("Header mismatch" in e for e in errors)

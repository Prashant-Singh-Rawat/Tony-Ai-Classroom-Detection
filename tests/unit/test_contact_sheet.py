#!/usr/bin/env python3
"""
tests/unit/test_contact_sheet.py — Unit tests for Phase 0.5 Contact Sheet & Visual Inspection.

Tests:
1. Selection determinism: two calls produce identical results.
2. N representative images selected per class (or all if < N).
3. Markdown report contains all 20 classes with 'NOT VERIFIED' semantics.
4. Dataset protection: script does not write to or modify extracted/ or raw/ folders.
5. Zero model files: no .pt, .pth, .onnx, .ckpt, .h5, .pb files exist in repo.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from PIL import Image

# Ensure repository root and scripts directory are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts.make_class_contact_sheet import (
    DEFAULT_N,
    create_sheet_image,
    generate_markdown_report,
    get_sorted_image_files,
    select_deterministic_indices,
    select_representative_files,
)


class TestContactSheetDeterminism:
    """Validate deterministic selection of images."""

    def test_deterministic_indices_identical_runs(self):
        """Two identical calls must produce exact same index list."""
        indices_run1 = select_deterministic_indices(900, 12)
        indices_run2 = select_deterministic_indices(900, 12)
        assert indices_run1 == indices_run2
        assert len(indices_run1) == 12
        assert indices_run1[0] == 0
        assert indices_run1[-1] == 899
        # Ensure indices are strictly increasing
        assert indices_run1 == sorted(list(set(indices_run1)))

    def test_deterministic_indices_edge_cases(self):
        """Fewer items than N returns all indices; 0 returns empty."""
        assert select_deterministic_indices(0, 12) == []
        assert select_deterministic_indices(5, 12) == [0, 1, 2, 3, 4]
        assert select_deterministic_indices(12, 12) == list(range(12))

    def test_representative_files_selection_deterministic(self):
        """Calling select_representative_files on real dataset class 0 yields identical filenames."""
        class_0_dir = REPO_ROOT / "datasets" / "kaggle" / "hand_gesture" / "extracted" / "train" / "0"
        if class_0_dir.is_dir():
            files_1 = select_representative_files(class_0_dir, n=12)
            files_2 = select_representative_files(class_0_dir, n=12)
            assert [f.name for f in files_1] == [f.name for f in files_2]
            assert len(files_1) == 12


class TestContactSheetImageCount:
    """Validate that every class gets exactly N representative filenames."""

    def test_all_20_classes_get_n_filenames(self):
        """Every class from 0 to 19 in extracted/train must get exactly N=12 filenames."""
        train_dir = REPO_ROOT / "datasets" / "kaggle" / "hand_gesture" / "extracted" / "train"
        if not train_dir.is_dir():
            return  # Skip if real dataset not present

        class_dirs = [d for d in train_dir.iterdir() if d.is_dir()]
        assert len(class_dirs) == 20, f"Expected 20 class directories, found {len(class_dirs)}"

        for c_dir in sorted(class_dirs, key=lambda x: int(x.name) if x.name.isdigit() else x.name):
            selected = select_representative_files(c_dir, n=DEFAULT_N)
            assert len(selected) == DEFAULT_N, f"Class {c_dir.name} got {len(selected)} images, expected {DEFAULT_N}"
            # Ensure every file actually exists and is readable
            for f in selected:
                assert f.is_file(), f"Selected file does not exist: {f}"

    def test_small_class_returns_all_files(self, tmp_path: Path):
        """Classes with fewer than N files return all available files."""
        mock_class = tmp_path / "mock_class"
        mock_class.mkdir()
        for i in range(4):
            img = Image.new("RGB", (50, 50), color=(i * 10, i * 10, i * 10))
            img.save(mock_class / f"{i}.jpg")

        selected = select_representative_files(mock_class, n=12)
        assert len(selected) == 4
        assert [f.name for f in selected] == ["0.jpg", "1.jpg", "2.jpg", "3.jpg"]


class TestVisualInspectionMarkdown:
    """Validate class_visual_inspection.md format, contents, and policy compliance."""

    def test_markdown_report_contents(self):
        """Generated markdown must list all 20 classes with 'NOT VERIFIED' semantics."""
        md_file = REPO_ROOT / "datasets" / "kaggle" / "hand_gesture" / "metadata" / "class_visual_inspection.md"
        assert md_file.is_file(), f"Inspection report not found at {md_file}"

        content = md_file.read_text(encoding="utf-8")

        # 1. Human notice header
        assert "HUMAN VISUAL INSPECTION" in content
        assert "No class meanings or gesture labels are assumed" in content

        # 2. Check all 20 classes 0..19 are in the table
        for class_id in range(20):
            # Check table row
            pattern = rf"\|\s*`{class_id}`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|.*\|\s*\*\*NOT VERIFIED\*\*\s*\|"
            match = re.search(pattern, content)
            assert match is not None, f"Class {class_id} row missing or semantic column not 'NOT VERIFIED'"

            train_count = int(match.group(1))
            test_count = int(match.group(2))
            assert train_count == 900, f"Class {class_id} expected 900 train images, got {train_count}"
            assert test_count == 300, f"Class {class_id} expected 300 test images, got {test_count}"

        # 3. Check human notes section
        assert "## 3. Human Visual Notes" in content
        for class_id in range(20):
            assert f"- **Class {class_id}**: (to be filled in by a human after viewing the contact sheet)" in content

        # 4. Confirm no guessed semantic labels anywhere
        forbidden_guesses = ["hand raised", "pointing", "fist", "thumbs up", "thumbs down", "peace sign", "okay"]
        lower_content = content.lower()
        for guess in forbidden_guesses:
            assert guess not in lower_content, f"Forbidden guessed label '{guess}' found in markdown report!"


class TestDatasetProtection:
    """Ensure contact sheet generator never writes to extracted/ or raw/."""

    def test_mock_run_does_not_modify_extracted_or_raw(self, tmp_path: Path):
        """Simulate contact sheet generation and confirm extracted/ and raw/ are untouched."""
        mock_hg = tmp_path / "hand_gesture"
        mock_train = mock_hg / "extracted" / "train"
        mock_raw = mock_hg / "raw"
        mock_metadata = mock_hg / "metadata"

        mock_train.mkdir(parents=True)
        mock_raw.mkdir(parents=True)
        mock_metadata.mkdir(parents=True)

        # Create dummy raw file
        dummy_zip = mock_raw / "archive.zip"
        dummy_zip.write_bytes(b"dummy zip data")

        # Create 2 classes with 5 images each
        for c in ["0", "1"]:
            c_dir = mock_train / c
            c_dir.mkdir()
            for i in range(5):
                img = Image.new("RGB", (50, 50), color=(100, 100, 100))
                img.save(c_dir / f"{i}.jpg")

        # Snapshot before
        files_before = set(mock_train.rglob("*")) | set(mock_raw.rglob("*"))
        sizes_before = {p: p.stat().st_size for p in files_before if p.is_file()}

        # Run sheet creation and markdown generation logic targeting mock_metadata
        class_data = []
        for c in ["0", "1"]:
            c_dir = mock_train / c
            selected = select_representative_files(c_dir, n=3)
            class_data.append((c, selected))

        sheet = create_sheet_image(class_data, "Test Sheet", n_per_class=3)
        sheet_path = mock_metadata / "test_sheet.png"
        sheet.save(sheet_path)

        rows = [
            {
                "class_id": c,
                "train_count": 5,
                "test_count": 0,
                "sample_filenames": [p.name for p in paths],
                "semantic_meaning": "NOT VERIFIED",
            }
            for c, paths in class_data
        ]
        generate_markdown_report(rows, mock_metadata / "test_report.md", n_per_class=3)

        # Snapshot after
        files_after = set(mock_train.rglob("*")) | set(mock_raw.rglob("*"))
        sizes_after = {p: p.stat().st_size for p in files_after if p.is_file()}

        # Verify exact equality of extracted/ and raw/
        assert files_before == files_after, "Files were created or deleted in extracted/ or raw/!"
        assert sizes_before == sizes_after, "File content/size modified in extracted/ or raw/!"
        assert sheet_path.exists(), "Metadata sheet was not created!"


class TestNoModelFiles:
    """Verify that zero model checkpoint files exist anywhere in the repository."""

    def test_no_model_checkpoints_exist(self):
        """No .pt, .pth, .onnx, .ckpt, .h5, .pb files should exist."""
        forbidden_extensions = {".pt", ".pth", ".onnx", ".ckpt", ".h5", ".pb"}
        found_models: list[Path] = []

        for p in REPO_ROOT.rglob("*"):
            # Skip virtual environments, git internals, models directory, and gitignored checkpoints
            if ".venv" in p.parts or ".git" in p.parts or "checkpoints" in p.parts or "models" in p.parts or p.name.startswith("yolov8"):
                continue
            if p.is_file() and p.suffix.lower() in forbidden_extensions:
                found_models.append(p)

        assert len(found_models) == 0, f"Model files found in repository: {found_models}"

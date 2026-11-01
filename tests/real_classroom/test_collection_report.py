#!/usr/bin/env python3
"""
tests/real_classroom/test_collection_report.py — Unit Tests for scripts/collection_report.py.

Coverage:
1. Empty root: graceful handling, clean warning generation, no crash.
2. Normal report: multi-session dataset with balanced sessions and reviewed annotations.
3. Missing permission warning: flags sessions lacking verified permission.
4. Dominant session warning: flags sessions holding >35% of total frames.
5. Fewer than 3 sessions warning: flags datasets with <3 sessions.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts.collection_report import (
    count_yolo_annotations,
    generate_markdown_report,
    load_duplicate_report,
    load_frame_manifest,
    load_session_logs,
)


def create_fake_manifest(metadata_dir: Path, session_frame_counts: dict[str, int]) -> list[dict]:
    """Helper to generate a fake frame_manifest.csv."""
    metadata_dir.mkdir(parents=True, exist_ok=True)
    manifest_p = metadata_dir / "frame_manifest.csv"
    fieldnames = [
        "frame_id",
        "session_id",
        "source_video",
        "source_frame_index",
        "timestamp_ms",
        "extraction_fps",
        "video_fps",
        "width",
        "height",
        "file_sha256",
        "extraction_date",
    ]
    rows = []
    for sid, count in session_frame_counts.items():
        for i in range(count):
            t_ms = i * 1000
            fid = f"{sid}/vid_t{t_ms:07d}"
            rows.append(
                {
                    "frame_id": fid,
                    "session_id": sid,
                    "source_video": f"{sid}_video.mp4",
                    "source_frame_index": str(i * 30),
                    "timestamp_ms": str(t_ms),
                    "extraction_fps": "1.0",
                    "video_fps": "30.00",
                    "width": "1920",
                    "height": "1080",
                    "file_sha256": "0" * 64,
                    "extraction_date": "2026-10-12",
                }
            )
    with open(manifest_p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def create_fake_session_log(metadata_dir: Path, sessions_meta: list[dict]) -> None:
    """Helper to generate a fake session_log.csv."""
    metadata_dir.mkdir(parents=True, exist_ok=True)
    log_p = metadata_dir / "session_log.csv"
    fieldnames = [
        "session_id",
        "date",
        "classroom_label",
        "recording_start",
        "duration_min",
        "camera_position",
        "camera_distance",
        "camera_angle",
        "lighting",
        "layout",
        "approx_students_visible",
        "permission_obtained",
        "permission_ref",
        "notes",
    ]
    with open(log_p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sessions_meta)


class TestCollectionReport:
    """Unit tests for real classroom progress reporter."""

    def test_empty_root_handling(self, tmp_path: Path):
        """Empty root produces a graceful report with <3 sessions warning and no crashes."""
        manifest_rows = load_frame_manifest(tmp_path)
        duplicate_frames = load_duplicate_report(tmp_path)
        session_logs = load_session_logs(tmp_path)
        session_ann_counts, total_ann_counts, reviewed_frames_count = count_yolo_annotations(tmp_path)

        report = generate_markdown_report(
            root=tmp_path,
            manifest_rows=manifest_rows,
            duplicate_frames=duplicate_frames,
            session_logs=session_logs,
            session_ann_counts=session_ann_counts,
            total_ann_counts=total_ann_counts,
            reviewed_frames_count=reviewed_frames_count,
        )

        assert "**Total Raw Frames Extracted**: 0" in report
        assert "Minimum 3 sessions required" in report
        assert "0 / 1000 images" in report

    def test_normal_report_generation(self, tmp_path: Path):
        """Well-formed multi-session dataset produces a clean report with full stats."""
        meta_dir = tmp_path / "metadata"
        manifest_rows = create_fake_manifest(
            meta_dir, {"sess_01": 30, "sess_02": 30, "sess_03": 30}
        )

        create_fake_session_log(
            meta_dir,
            [
                {
                    "session_id": "sess_01",
                    "date": "2026-10-12",
                    "classroom_label": "Room-A",
                    "recording_start": "09:00",
                    "duration_min": "10",
                    "camera_position": "front_corner",
                    "camera_distance": "5m",
                    "camera_angle": "elevated",
                    "lighting": "daylight",
                    "layout": "tiered",
                    "approx_students_visible": "25",
                    "permission_obtained": "yes",
                    "permission_ref": "ETHICS-01",
                    "notes": "normal session",
                },
                {
                    "session_id": "sess_02",
                    "date": "2026-10-12",
                    "classroom_label": "Room-B",
                    "recording_start": "11:00",
                    "duration_min": "10",
                    "camera_position": "side_wall",
                    "camera_distance": "7m",
                    "camera_angle": "eye_level",
                    "lighting": "fluorescent",
                    "layout": "flat",
                    "approx_students_visible": "15",
                    "permission_obtained": "yes",
                    "permission_ref": "ETHICS-01",
                    "notes": "normal session",
                },
                {
                    "session_id": "sess_03",
                    "date": "2026-10-13",
                    "classroom_label": "Room-C",
                    "recording_start": "14:00",
                    "duration_min": "10",
                    "camera_position": "rear_corner",
                    "camera_distance": "8m",
                    "camera_angle": "elevated",
                    "lighting": "warm",
                    "layout": "u_shape",
                    "approx_students_visible": "20",
                    "permission_obtained": "yes",
                    "permission_ref": "ETHICS-01",
                    "notes": "normal session",
                },
            ],
        )

        # Create reviewed annotation files
        for sid in ["sess_01", "sess_02", "sess_03"]:
            s_ann_dir = tmp_path / "annotations" / "reviewed" / sid
            s_ann_dir.mkdir(parents=True)
            (s_ann_dir / "vid_t0000000.txt").write_text("0 0.5 0.5 0.2 0.3\n1 0.2 0.2 0.1 0.2\n")

        session_logs = load_session_logs(tmp_path)
        session_ann_counts, total_ann_counts, reviewed_cnt = count_yolo_annotations(tmp_path)

        report = generate_markdown_report(
            root=tmp_path,
            manifest_rows=manifest_rows,
            duplicate_frames=set(),
            session_logs=session_logs,
            session_ann_counts=session_ann_counts,
            total_ann_counts=total_ann_counts,
            reviewed_frames_count=reviewed_cnt,
        )

        assert "**Total Raw Frames Extracted**: 90" in report
        assert "**Total Sessions Discovered**: 3" in report
        assert "Minimum 3 sessions required" not in report
        assert "DOMINANCE WARNING" not in report
        assert "PERMISSION WARNING" not in report
        assert "3 / 1000 images" in report
        assert total_ann_counts[0] == 3
        assert total_ann_counts[1] == 3

    def test_missing_permission_warning(self, tmp_path: Path):
        """Flags sessions where permission is missing or not set to 'yes'."""
        meta_dir = tmp_path / "metadata"
        manifest_rows = create_fake_manifest(meta_dir, {"sess_01": 10, "sess_02": 10, "sess_03": 10})
        create_fake_session_log(
            meta_dir,
            [
                {"session_id": "sess_01", "permission_obtained": "yes", "permission_ref": "AUTH-1"},
                {"session_id": "sess_02", "permission_obtained": "no", "permission_ref": "PENDING"},
                # sess_03 has no log entry at all
            ],
        )

        session_logs = load_session_logs(tmp_path)
        report = generate_markdown_report(
            root=tmp_path,
            manifest_rows=manifest_rows,
            duplicate_frames=set(),
            session_logs=session_logs,
            session_ann_counts={},
            total_ann_counts={0: 0, 1: 0, 2: 0},
            reviewed_frames_count=0,
        )

        assert "PERMISSION WARNING" in report
        assert "sess_02" in report
        assert "sess_03" in report

    def test_dominant_session_warning(self, tmp_path: Path):
        """Flags single sessions containing >35% of total extracted frames."""
        meta_dir = tmp_path / "metadata"
        # Total frames = 100. sess_01 has 50 frames (50% > 35%)
        manifest_rows = create_fake_manifest(
            meta_dir,
            {"sess_01": 50, "sess_02": 25, "sess_03": 25},
        )
        report = generate_markdown_report(
            root=tmp_path,
            manifest_rows=manifest_rows,
            duplicate_frames=set(),
            session_logs={},
            session_ann_counts={},
            total_ann_counts={0: 0, 1: 0, 2: 0},
            reviewed_frames_count=0,
        )

        assert "DOMINANCE WARNING" in report
        assert "`sess_01` holds 50 frames (50.0% > 35% threshold)" in report

    def test_fewer_than_3_sessions_warning(self, tmp_path: Path):
        """Flags datasets with only 1 or 2 sessions as insufficient for 3-way split."""
        meta_dir = tmp_path / "metadata"
        manifest_rows = create_fake_manifest(meta_dir, {"sess_01": 20, "sess_02": 20})

        report = generate_markdown_report(
            root=tmp_path,
            manifest_rows=manifest_rows,
            duplicate_frames=set(),
            session_logs={},
            session_ann_counts={},
            total_ann_counts={0: 0, 1: 0, 2: 0},
            reviewed_frames_count=0,
        )

        assert "Only 2 session(s) detected. Minimum 3 sessions required" in report

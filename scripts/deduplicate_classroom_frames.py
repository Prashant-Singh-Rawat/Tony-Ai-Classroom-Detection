#!/usr/bin/env python3
"""
scripts/deduplicate_classroom_frames.py — Per-Session Perceptual Frame Deduplication.

Features:
- Compares perceptual hashes ONLY within the same session.
- Configurable Hamming distance threshold (--hamming-thresh, default: 6).
- Safe by default (DRY RUN): writes metadata/duplicate_report.csv without moving/copying images.
- With --apply: COPIES kept frames to frames/deduplicated/<session_id>/ without modifying frames/raw/.
- Never moves, alters, or deletes original frames in frames/raw/.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import imagehash
from PIL import Image

DEFAULT_HAMMING_THRESHOLD = 6


def resolve_data_root(cli_root: Optional[Path] = None) -> Path:
    """Resolve dataset root from CLI, env var, or default."""
    if cli_root:
        return cli_root.resolve()
    env_root = os.environ.get("CLASSVISION_REAL_DATA_ROOT")
    if env_root:
        return Path(env_root).resolve()
    repo_root = Path(__file__).resolve().parent.parent
    return (repo_root / "datasets" / "real_classroom").resolve()


def compute_image_phash(img_path: Path) -> Optional[imagehash.ImageHash]:
    """Compute perceptual hash using PIL and imagehash."""
    try:
        with Image.open(img_path) as img:
            return imagehash.phash(img)
    except Exception as e:
        print(f"Warning: Failed to hash image {img_path}: {e}", file=sys.stderr)
        return None


def find_session_frames(raw_frames_dir: Path) -> Dict[str, List[Path]]:
    """Group frames by session_id."""
    sessions: Dict[str, List[Path]] = {}
    if not raw_frames_dir.is_dir():
        return sessions

    for session_folder in sorted(raw_frames_dir.iterdir()):
        if session_folder.is_dir():
            s_id = session_folder.name
            frames = sorted(
                [p for p in session_folder.glob("*.jpg") if p.is_file()],
                key=lambda p: p.name,
            )
            if frames:
                sessions[s_id] = frames
    return sessions


def deduplicate_session(
    session_id: str,
    frame_paths: List[Path],
    hamming_threshold: int,
) -> Tuple[List[Path], List[Dict[str, str]]]:
    """
    Greedy perceptual clustering within a single session.
    Returns (kept_frames, duplicate_report_rows).
    """
    if not frame_paths:
        return [], []

    # Precompute hashes
    hashes: List[Tuple[Path, imagehash.ImageHash]] = []
    for p in frame_paths:
        h = compute_image_phash(p)
        if h is not None:
            hashes.append((p, h))

    kept_frames: List[Path] = []
    report_rows: List[Dict[str, str]] = []
    cluster_idx = 0

    # Cluster list: each cluster is a list of (Path, hash)
    # The first item in the cluster is the kept frame
    clusters: List[List[Tuple[Path, imagehash.ImageHash]]] = []

    for path, h in hashes:
        matched = False
        for cluster in clusters:
            rep_path, rep_hash = cluster[0]
            dist = h - rep_hash
            if dist <= hamming_threshold:
                cluster.append((path, h))
                report_rows.append(
                    {
                        "group_id": f"{session_id}_grp{len(clusters)}",
                        "session_id": session_id,
                        "kept_frame": rep_path.name,
                        "duplicate_frame": path.name,
                        "hamming_distance": str(dist),
                    }
                )
                matched = True
                break

        if not matched:
            clusters.append([(path, h)])

    for cluster in clusters:
        kept_frames.append(cluster[0][0])

    return kept_frames, report_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-session perceptual frame deduplication.")
    parser.add_argument("--root", type=Path, default=None, help="Root directory for real_classroom dataset")
    parser.add_argument(
        "--hamming-thresh",
        type=int,
        default=DEFAULT_HAMMING_THRESHOLD,
        help=f"Hamming distance threshold for pHash (default: {DEFAULT_HAMMING_THRESHOLD})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Copy kept frames to frames/deduplicated/ (Default: False / Dry-Run only)",
    )
    args = parser.parse_args()

    root = resolve_data_root(args.root)
    raw_frames_dir = root / "frames" / "raw"
    dedup_frames_dir = root / "frames" / "deduplicated"
    metadata_dir = root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    report_csv = metadata_dir / "duplicate_report.csv"

    print("ClassVision AI — Frame Deduplication Engine")
    print(f"Data Root: {root}")
    print(f"Mode: {'APPLY (Copying kept frames)' if args.apply else 'DRY RUN (Report only)'}")
    print(f"Hamming Distance Threshold: {args.hamming_thresh}")

    sessions = find_session_frames(raw_frames_dir)
    if not sessions:
        print(f"No frames found under {raw_frames_dir}.")
        return 0

    all_report_rows: List[Dict[str, str]] = []
    total_raw_frames = sum(len(f) for f in sessions.values())
    total_kept_frames = 0

    for s_id, frames in sessions.items():
        print(f"\nAnalyzing Session '{s_id}': {len(frames)} frames...")
        kept, rows = deduplicate_session(s_id, frames, args.hamming_thresh)
        total_kept_frames += len(kept)
        all_report_rows.extend(rows)
        print(f"  Proposed Kept: {len(kept)} | Duplicates Flagged: {len(rows)}")

        if args.apply:
            s_dedup_dir = dedup_frames_dir / s_id
            s_dedup_dir.mkdir(parents=True, exist_ok=True)
            for kf in kept:
                dest = s_dedup_dir / kf.name
                shutil.copy2(kf, dest)
            print(f"  Copied {len(kept)} kept frames to {s_dedup_dir}")

    # Write duplicate report CSV
    fields = ["group_id", "session_id", "kept_frame", "duplicate_frame", "hamming_distance"]
    with open(report_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_report_rows)

    print("\n" + "=" * 60)
    print(f"Deduplication Analysis Summary:")
    print(f"Total raw frames evaluated:   {total_raw_frames}")
    print(f"Unique frames to retain:     {total_kept_frames}")
    print(f"Duplicate frames identified: {len(all_report_rows)}")
    print(f"Duplicate report saved to:   {report_csv}")
    if not args.apply:
        print("NOTE: Executed in DRY RUN mode. No files were copied or moved.")
        print("To copy kept frames to frames/deduplicated/, rerun with --apply.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

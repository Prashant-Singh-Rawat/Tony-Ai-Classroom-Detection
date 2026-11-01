#!/usr/bin/env python3
"""
scripts/split_classroom_dataset.py — Session-Level Classroom Dataset Splitter.

Features:
- Refuses to run unless annotations/reviewed contains labels.
- Splits SESSIONS (never individual frames) to guarantee zero intra-session leakage.
- Enforces minimum 3 sessions; refuses to create splits if any partition receives 0 sessions.
- Default split target: 70% train / 15% validation / 15% test.
- Output is LIST FILES ONLY: splits/train.txt, splits/validation.txt, splits/test.txt, and splits/split_manifest.json.
- Zero image copying or moving.
- Freezes splits/test.txt: refuses to overwrite an existing test split.
- Incremental mode: --add-sessions assigns only new sessions without altering existing partitions.
- Automated leakage assertion: verifies session sets are mutually disjoint.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 digest of a text list file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_data_root(cli_root: Optional[Path] = None) -> Path:
    """Resolve dataset root from CLI, env var, or default."""
    if cli_root:
        return cli_root.resolve()
    env_root = os.environ.get("CLASSVISION_REAL_DATA_ROOT")
    if env_root:
        return Path(env_root).resolve()
    repo_root = Path(__file__).resolve().parent.parent
    return (repo_root / "datasets" / "real_classroom").resolve()


def collect_reviewed_annotations(reviewed_dir: Path) -> Dict[str, List[str]]:
    """
    Collect frame_ids from annotations/reviewed grouped by session_id.
    Returns {session_id: [frame_id, ...]}.
    """
    if not reviewed_dir.is_dir():
        return {}

    session_frames: Dict[str, List[str]] = {}
    for p in sorted(reviewed_dir.rglob("*.txt")):
        if p.name == "labels.yaml" or p.name.startswith("."):
            continue
        stem = p.stem
        # Session id is parent folder name or derived from stem
        parent_dir = p.parent
        session_id = parent_dir.name if parent_dir != reviewed_dir else stem.split("_")[0]
        frame_id = f"{session_id}/{stem}"

        if session_id not in session_frames:
            session_frames[session_id] = []
        session_frames[session_id].append(frame_id)

    return session_frames


def compute_session_partitions(
    sessions: List[str],
    seed: int,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Deterministically partition sessions targeting 70/15/15.
    Guarantees every partition has at least 1 session for N >= 3.
    """
    n = len(sessions)
    if n < 3:
        raise ValueError(
            f"Fewer than 3 sessions available ({n} found). "
            f"Dataset splitting requires at least 3 sessions to guarantee disjoint train, validation, and test splits."
        )

    # Seeded deterministic shuffle
    rng = random.Random(seed)
    shuffled = list(sessions)
    rng.shuffle(shuffled)

    # Calculate partition counts ensuring >= 1 per split
    test_count = max(1, int(round(n * 0.15)))
    val_count = max(1, int(round(n * 0.15)))
    train_count = n - test_count - val_count

    # If train_count drops below 1 due to rounding on small N
    if train_count < 1:
        if n == 3:
            train_count, val_count, test_count = 1, 1, 1
        elif n == 4:
            train_count, val_count, test_count = 2, 1, 1
        else:
            raise ValueError(f"Partition calculation resulted in 0 train sessions for N={n}.")

    train_sessions = sorted(shuffled[:train_count])
    val_sessions = sorted(shuffled[train_count : train_count + val_count])
    test_sessions = sorted(shuffled[train_count + val_count :])

    if not train_sessions or not val_sessions or not test_sessions:
        raise ValueError("A split would receive 0 sessions. Aborting split creation.")

    # Automated Data Leakage Check
    s_train, s_val, s_test = set(train_sessions), set(val_sessions), set(test_sessions)
    if s_train & s_val:
        raise RuntimeError(f"Data leakage detected! Sessions in train and val: {s_train & s_val}")
    if s_train & s_test:
        raise RuntimeError(f"Data leakage detected! Sessions in train and test: {s_train & s_test}")
    if s_val & s_test:
        raise RuntimeError(f"Data leakage detected! Sessions in val and test: {s_val & s_test}")

    return train_sessions, val_sessions, test_sessions


def write_split_files(
    splits_dir: Path,
    session_frames: Dict[str, List[str]],
    train_sessions: List[str],
    val_sessions: List[str],
    test_sessions: List[str],
    seed: int,
) -> Path:
    """Write train.txt, validation.txt, test.txt and split_manifest.json."""
    splits_dir.mkdir(parents=True, exist_ok=True)

    train_frames: List[str] = []
    val_frames: List[str] = []
    test_frames: List[str] = []

    for s in train_sessions:
        train_frames.extend(session_frames.get(s, []))
    for s in val_sessions:
        val_frames.extend(session_frames.get(s, []))
    for s in test_sessions:
        test_frames.extend(session_frames.get(s, []))

    train_frames.sort()
    val_frames.sort()
    test_frames.sort()

    train_file = splits_dir / "train.txt"
    val_file = splits_dir / "validation.txt"
    test_file = splits_dir / "test.txt"

    train_file.write_text("\n".join(train_frames) + ("\n" if train_frames else ""), encoding="utf-8")
    val_file.write_text("\n".join(val_frames) + ("\n" if val_frames else ""), encoding="utf-8")
    test_file.write_text("\n".join(test_frames) + ("\n" if test_frames else ""), encoding="utf-8")

    manifest_data = {
        "creation_date": datetime.date.today().isoformat(),
        "seed": seed,
        "total_sessions": len(train_sessions) + len(val_sessions) + len(test_sessions),
        "total_frames": len(train_frames) + len(val_frames) + len(test_frames),
        "sessions": {
            "train": train_sessions,
            "validation": val_sessions,
            "test": test_sessions,
        },
        "frame_counts": {
            "train": len(train_frames),
            "validation": len(val_frames),
            "test": len(test_frames),
        },
        "sha256": {
            "train": compute_sha256(train_file),
            "validation": compute_sha256(val_file),
            "test": compute_sha256(test_file),
        },
    }

    manifest_path = splits_dir / "split_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Session-level classroom dataset splitter.")
    parser.add_argument("--root", type=Path, default=None, help="Root directory for real_classroom dataset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic split (default: 42)")
    parser.add_argument(
        "--add-sessions",
        action="store_true",
        help="Incremental mode: assign only new sessions without modifying existing test set",
    )
    args = parser.parse_args()

    root = resolve_data_root(args.root)
    ann_reviewed_dir = root / "annotations" / "reviewed"
    splits_dir = root / "splits"

    print("=" * 65)
    print("ClassVision AI — Session-Level Dataset Splitter")
    print(f"Data Root: {root}")
    print(f"Seed: {args.seed}")
    print("=" * 65)

    # 1. Check annotations/reviewed
    session_frames = collect_reviewed_annotations(ann_reviewed_dir)
    total_reviewed_labels = sum(len(f) for f in session_frames.values())

    if not session_frames or total_reviewed_labels == 0:
        print(
            "ERROR: annotations/reviewed contains no labels. Refusing to create splits.\n"
            "Only second-person-verified reviewed annotations may be used for dataset splits and training.",
            file=sys.stderr,
        )
        return 1

    available_sessions = sorted(list(session_frames.keys()))
    print(f"Reviewed labels found: {total_reviewed_labels} frames across {len(available_sessions)} sessions.")
    print(f"Sessions: {available_sessions}")

    # 2. Check frozen test set
    test_file = splits_dir / "test.txt"
    manifest_file = splits_dir / "split_manifest.json"

    if test_file.is_file() and not args.add_sessions:
        print(
            f"ERROR: {test_file} already exists and is FROZEN to prevent data leakage.\n"
            f"Overwriting an existing test split is prohibited. Pass --add-sessions to incrementally assign new sessions.",
            file=sys.stderr,
        )
        return 1

    # 3. Handle --add-sessions mode
    if args.add_sessions and manifest_file.is_file():
        print("\nIncremental Mode (--add-sessions): Preserving existing split assignments.")
        with open(manifest_file, "r", encoding="utf-8") as f:
            old_manifest = json.load(f)

        existing_train = old_manifest["sessions"]["train"]
        existing_val = old_manifest["sessions"]["validation"]
        existing_test = old_manifest["sessions"]["test"]
        all_assigned = set(existing_train) | set(existing_val) | set(existing_test)

        new_sessions = [s for s in available_sessions if s not in all_assigned]
        if not new_sessions:
            print("No new sessions found to assign. Existing splits remain unchanged.")
            return 0

        print(f"Found {len(new_sessions)} new unassigned session(s): {new_sessions}")
        # Assign new sessions alternately to train and val, NEVER to test
        for idx, ns in enumerate(new_sessions):
            if idx % 2 == 0:
                existing_train.append(ns)
            else:
                existing_val.append(ns)

        manifest_path = write_split_files(
            splits_dir,
            session_frames,
            sorted(existing_train),
            sorted(existing_val),
            sorted(existing_test),
            old_manifest.get("seed", args.seed),
        )
        print(f"Incremental splits updated successfully: {manifest_path}")
        return 0

    # 4. Standard new split creation
    try:
        train_sess, val_sess, test_sess = compute_session_partitions(available_sessions, args.seed)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    manifest_path = write_split_files(splits_dir, session_frames, train_sess, val_sess, test_sess, args.seed)

    print("\nDataset Partition Complete:")
    print(f"  Train Sessions ({len(train_sess)}): {train_sess}")
    print(f"  Validation Sessions ({len(val_sess)}): {val_sess}")
    print(f"  Test Sessions ({len(test_sess)}): {test_sess} (FROZEN)")
    print(f"Split manifest generated: {manifest_path}")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())

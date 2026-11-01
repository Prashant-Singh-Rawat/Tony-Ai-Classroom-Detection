# ClassVision AI — Real-Time Multimodal Classroom Intelligence System

ClassVision AI is a privacy-preserving classroom analytics system fusing computer vision (hand-raise and activity detection), speech transcription, whiteboard OCR, and NLP into a unified dashboard.

---

## Important Notice: Data Privacy & OneDrive Storage

> [!WARNING]
> **PRIVACY ALERT: REPOSITORY LOCATION & ONEDRIVE SYNCHRONIZATION**
> If this repository resides within a OneDrive-synchronized folder, **DO NOT store identifiable classroom footage, video files, frames, audio recordings, or student annotation files inside this tree**.
>
> Point real classroom data to an un-synced local folder using `CLASSVISION_REAL_DATA_ROOT`:
>
> **PowerShell:**
> ```powershell
> [Environment]::SetEnvironmentVariable("CLASSVISION_REAL_DATA_ROOT", "D:\ClassVisionData\real_classroom", "User")
> ```
>
> **Command Prompt:**
> ```cmd
> setx CLASSVISION_REAL_DATA_ROOT "D:\ClassVisionData\real_classroom"
> ```
>
> Or supply `--root <PATH>` to any ingestion script.
> See [`docs/collection_plan.md`](docs/collection_plan.md) for full collection, diversity, and privacy procedures.

---

## Dataset Ingestion Architecture (Phase 0.6)

1. **Frame Extraction**: `scripts/extract_classroom_frames.py`
   - Deterministic extraction: `<session_id>/<video_stem>_t<timestamp_ms>.jpg`
   - Manifest tracking: `frame_manifest.csv`
   - Quality checks: Laplacian blur variance & mean brightness in `quality_report.csv`
   - Skips existing frames automatically without overwriting.

2. **Deduplication**: `scripts/deduplicate_classroom_frames.py`
   - Session-isolated perceptual hashing (`imagehash.phash`).
   - Dry-run by default (`duplicate_report.csv`); `--apply` copies kept frames to `frames/deduplicated/`.

3. **Annotation Validation**: `scripts/validate_annotations.py`
   - Validates YOLO-format boxes (`0: hand_raised`, `1: hand_not_raised`, `2: ambiguous`).
   - Verifies coordinate ranges $[0.0, 1.0]$ and cross-references frame existence.
   - Enforces two-tier workflow (`annotations/raw` vs `annotations/reviewed`).

4. **Session-Level Splitting**: `scripts/split_classroom_dataset.py`
   - Splits sessions (never individual frames) to eliminate cross-frame data leakage.
   - Generates `splits/train.txt`, `splits/validation.txt`, `splits/test.txt` and `splits/split_manifest.json`.
   - Freezes test split once established.

---

## Test Suite Execution
```bash
python -m pytest -v
```
All unit tests verify deterministic pipelines, boundary conditions, dataset immutability, and zero model creation.

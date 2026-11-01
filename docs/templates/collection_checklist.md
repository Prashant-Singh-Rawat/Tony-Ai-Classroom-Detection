# Real Classroom Data Collection & Curation Checklist

Use this operational checklist for every recording session to guarantee student privacy, data diversity, technical quality, and pipeline reproducibility.

---

## 1. Before Recording (Setup & Authorization)
- [ ] **Institutional & Lecturer Consent**: Signed written authorization obtained from department head and course lecturer.
- [ ] **Permission Reference**: Official consent ID recorded in `collection_session_log.csv` (e.g. `ETHICS-CV-2026-XX`).
- [ ] **Student Notification**: Verbal announcement and notice displayed outside the lecture room informing students of research video recording.
- [ ] **Storage Confirmation**: Destination storage verified to reside **OUTSIDE OneDrive** (or on a dedicated non-synced drive like `D:\ClassVisionData\`).
- [ ] **Tripod & Rig Stability**: Camera firmly mounted on a fixed tripod (no handheld or moving camera).
- [ ] **Framing Verification**: Camera framed on students' desks and upper bodies. Lens angled so student faces are not captured in close-up.
- [ ] **Resolution & Battery**: Camera set to landscape 1080p (or 720p minimum) at 24–30 FPS; battery and SD card storage verified.
- [ ] **Audio Muting**: Microphone disabled on camera (or agreement noted that audio will be discarded/stripped).

---

## 2. During Recording (Session Capture)
- [ ] **Stable Fixed View**: Camera remains completely stationary during the session duration (5–10 minutes).
- [ ] **Prompted Hand-Raise Segment**: Lecturer introduces a 1–2 minute interactive question prompt ("Raise your hand if...") to capture clear positive cases.
- [ ] **Natural Classroom Segment**: Remaining 4–8 minutes capture authentic, unscripted classroom activity (taking notes, typing, listening).
- [ ] **Environment Logging**: Lighting, student headcount, room layout, and seating density noted during the session.

---

## 3. After Recording (Transfer & Ingestion)
- [ ] **Safe Offline Transfer**: Video file copied directly from SD card to `datasets/real_classroom/videos/raw/` (or external `CLASSVISION_REAL_DATA_ROOT`).
- [ ] **Zero Cloud Sync**: Confirmed that the video directory is NOT being synced by OneDrive, Google Drive, or iCloud.
- [ ] **Session Naming**: Video named according to convention (e.g. `sess_01_lecture.mp4`).
- [ ] **Session Log Update**: Row completed in `metadata/session_log.csv` with camera angle, distance, lighting, and student count.
- [ ] **SD Card Cleanup**: Original footage securely removed from SD card once backed up to non-synced local storage.

---

## 4. Frame Extraction & Curation (Before Annotation)
- [ ] **Low-FPS Extraction**: Frames extracted at 0.5–1.0 FPS using `scripts/extract_classroom_frames.py`.
- [ ] **Manifest Verification**: Extracted frames cataloged in `metadata/frame_manifest.csv`.
- [ ] **Perceptual Deduplication (Dry Run)**: Ran `scripts/deduplicate_classroom_frames.py` in dry-run mode and inspected `metadata/duplicate_report.csv`.
- [ ] **Apply Deduplication**: Ran `scripts/deduplicate_classroom_frames.py --apply` to populate `frames/deduplicated/`.
- [ ] **Manual Human Review**: Human curator visually inspected frames; discarded unusable blurred/dark frames and redundant stationary stretches.
- [ ] **Session Budgeting**: Kept frames capped to ~100–150 per session, tracking toward the ~1,000 total reviewed target.
- [ ] **Local Tool Setup**: CVAT Local, Label Studio Local, or LabelImg launched on `localhost`. Cloud annotation tools strictly avoided.

---

## 5. Annotation & Splitting (Before ML Training)
- [ ] **Person-Level Boxes**: Bounding boxes drawn tightly around individual students (torso, arms, head).
- [ ] **Class Schema Compliance**: Every box assigned one of:
  - `0`: `hand_raised`
  - `1`: `hand_not_raised`
  - `2`: `ambiguous`
- [ ] **Ambiguous Rule Applied**: Any borderline posture, stretch, or partial occlusion labeled as `2` (excluded from training).
- [ ] **Two-Tier Review**: First-pass labels placed in `annotations/raw/`; second reviewer verified ~10% sample before moving to `annotations/reviewed/`.
- [ ] **Annotation Index**: `annotations/annotation_index.csv` updated with review status and dates.
- [ ] **Run Validator**: `python scripts/validate_annotations.py --tier reviewed` executed and returned zero errors.
- [ ] **Session Threshold Check**: Confirmed that at least 3 distinct sessions have reviewed annotations.
- [ ] **Run Splitter**: `python scripts/split_classroom_dataset.py --seed 42` executed to create `splits/train.txt`, `splits/validation.txt`, `splits/test.txt`.
- [ ] **Test Set Freeze**: Verified `splits/test.txt` and `splits/split_manifest.json` are generated and frozen.
- [ ] **Run Collection Report**: `python scripts/collection_report.py` verified to show clean diversity distribution with zero fatal warnings.

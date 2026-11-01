# ClassVision AI — Local Annotation Workflow Guide

## Context & Objectives
Real classroom data collection commences after **12 October 2026**.
This document outlines the standard operational protocol for human annotators creating bounding box labels for the real classroom dataset.

---

## 1. Annotation Unit: Person-Level Bounding Boxes

> [!IMPORTANT]
> **PERSON-LEVEL STATE LABEL, NOT A HAND-ONLY DETECTOR**
> Bounding boxes are drawn around **individual visible students**, not isolated hands.
> Each box represents an individual person's state within the classroom context.

- **Bounding Box Bounds**: Enclose the student's upper body (head to desk/lap, including shoulders, torso, and any raised or resting arm/hand).
- If a student raises an arm above head height, the bounding box expands upward to include the entire raised hand and arm.
- If a student is seated behind a desk or partially occluded by a computer screen, enclose all visible portions of their upper body.
- **Rationale**: A person-level box provides spatial context (head orientation, posture, shoulder angle) which disambiguates raised hands from background objects or neighboring students.

---

## 2. Local Annotation Tool Setup: CVAT Self-Hosted

To prevent unauthorized cloud synchronization or external transmission of student video, annotations must be performed strictly using **local offline tools**.

### CVAT (Computer Vision Annotation Tool) — Recommended Option
CVAT is an open-source, full-featured annotation tool that runs entirely on `localhost`.

#### Prerequisites
- Windows 10/11 with Docker Desktop installed (WSL 2 backend enabled).
- Git installed.

#### Setup Steps (Localhost Only)
1. Clone the official CVAT repository outside your synced folders:
   ```bash
   git clone https://github.com/cvat-ai/cvat.git C:\tools\cvat
   cd C:\tools\cvat
   ```
2. Start the local Docker containers:
   ```bash
   docker compose up -d
   ```
3. Create a local administrator account:
   ```bash
   docker exec -it cvat_server server/manage.py createsuperuser
   ```
4. Access the web interface in your browser at `http://localhost:8080`.

#### Strict Privacy & Offline Constraints
- **Localhost Binding**: CVAT must run solely on `localhost:8080` (or `127.0.0.1`).
- **No Cloud Accounts**: Do not connect CVAT to cvat.ai cloud or any remote servers.
- **No External Storage**: Mount local image directories directly; do not configure S3, Azure, or Google Cloud buckets.
- **Data Location**: Ensure all imported frames and exported labels reside inside the configured data root (e.g. `CLASSVISION_REAL_DATA_ROOT`), completely outside OneDrive-synced directories.

*(Lightweight Fallback: If Docker is unavailable on a Windows workstation, **LabelImg** or **Label Studio Local** (`pip install label-studio && label-studio start`) may be used as an offline desktop alternative.)*

---

## 3. Importing Frames & Maintaining Session Integrity

1. **Source Frames**:
   - Annotate images from the deduplicated or curated frames directory (e.g. `frames/deduplicated/<session_id>/` or curated copies).
   - **NEVER** move, rename, or edit original frames in `frames/raw/`.
2. **Preserve Filenames and Session IDs**:
   - Every frame retains its canonical name: `<session_id>/<video_stem>_t<timestamp_ms:07d>.jpg`.
   - In CVAT, create one **Task per Session** (Task name = `session_id`, e.g. `sess_01`).
3. **Exporting Annotations**:
   - Export format: **YOLO 1.1** (generates one `.txt` per image with normalized coordinates).
   - Verify exported `.txt` files retain matching stems: `<video_stem>_t<timestamp_ms:07d>.txt`.
   - Place exports into session subfolders: `annotations/raw/<session_id>/`.

---

## 4. Class Definitions & Borderline Case Guidelines

Configure three labels in the annotation tool in this exact order:
- `0`: `hand_raised`
- `1`: `hand_not_raised`
- `2`: `ambiguous`

```yaml
0: hand_raised
1: hand_not_raised
2: ambiguous
```

### Class 0: `hand_raised`
**Definition**: A distinct, intentional upward gesture where the hand or forearm is elevated to attract the instructor's attention or participate.
- **Borderline 1 (Elbow on desk)**: Student rests their elbow on the desk surface, but the forearm is vertical with hand held open/upward to answer a question -> **Class 0**.
- **Borderline 2 (Low raise)**: Student raises their hand to eye or forehead level while actively speaking during a class discussion -> **Class 0**.
- **Borderline 3 (Two hands)**: Student raises both hands simultaneously -> **Class 0** (one bounding box enclosing the student).

### Class 1: `hand_not_raised`
**Definition**: Student engaged in typical classroom activity without any signaling gesture toward the instructor.
- **Borderline 1 (Chin rest)**: Student rests their chin or cheek in their open palm or on a closed fist while looking at the whiteboard -> **Class 1**.
- **Borderline 2 (Head scratching)**: Student scratches their head, adjusts glasses, or rubs their ear -> **Class 1**.
- **Borderline 3 (Horizontal pointing)**: Student extends an index finger horizontally to point at their neighbor's textbook or laptop screen -> **Class 1**.

### Class 2: `ambiguous`
**Definition**: Gestures where the student's intent cannot be reliably deduced from the visual frame, or where severe occlusion prevents classification.
- **Borderline 1 (Stretching)**: Student extends both arms upward/backward in a full-body yawn or stretch without signaling to speak -> **Class 2**.
- **Borderline 2 (Severe occlusion)**: Student in the third row appears to raise a hand, but the hand is 70%+ blocked by a student in the front row or a laptop display -> **Class 2**.
- **Borderline 3 (Hesitant half-raise)**: Student begins raising their hand to shoulder height, hesitates, and lowers it -> **Class 2**.
- **Borderline 4 (Motion blur / Low light)**: Hand position is indistinct due to camera blur or deep shadows -> **Class 2**.

> [!TIP]
> **THE AMBIGUOUS RULE**: When unsure whether a gesture is an intentional hand raise, **always assign Class 2 (`ambiguous`)**.
> Ambiguous boxes are safely excluded from model training batches and benchmark accuracy calculations.

---

## 5. Two-Stage Workflow: Raw vs. Reviewed

Annotation quality is safeguarded via a two-tier review process:

```
[Curated Frames] 
       │
       ▼
1. Annotator creates labels in CVAT Local
       │
       ▼
2. Export YOLO .txt files to annotations/raw/<session_id>/
       │
       ▼
3. Run scripts/annotation_preflight.py on annotations/raw/
       │
       ▼
4. Second Reviewer verifies ~10% sample & resolves edge cases
       │
       ▼
5. Approved annotations moved to annotations/reviewed/<session_id>/
       │
       ▼
6. Update annotations/annotation_index.csv (reviewed=yes)
       │
       ▼
7. Run scripts/validate_annotations.py --tier reviewed
       │
       ▼
8. Run scripts/split_classroom_dataset.py
```

### Tier Definitions
1. `annotations/raw/<session_id>/`: Initial exports produced by the primary annotator.
2. `annotations/reviewed/<session_id>/`: Verified labels confirmed by a second reviewer.
   - **MANDATORY**: Only annotations residing in `annotations/reviewed/` are accepted by `scripts/split_classroom_dataset.py`.
3. **Disagreement Tracking**:
   - The second reviewer inspects a randomly selected ~10% sample of images per session.
   - Record review decisions, reviewer name, and completion date in `annotations/annotation_index.csv`:
     `frame_id,annotator,reviewed,review_date`

---

## 6. Privacy, Ethics & Data Retention Checklist

- [ ] **Written Permission**: Confirmed written permission reference exists in `collection_session_log.csv` before annotating footage.
- [ ] **No Cloud Storage**: Verified that CVAT data directories and dataset roots reside on a local drive outside OneDrive.
- [ ] **No Public Displays**: Student facial images must never be included in presentation slides, Git commits, or documentation.
- [ ] **Git Exclusion**: Ensure `annotations/**/*.txt` remain excluded from Git tracking (enforced by root `.gitignore`).
- [ ] **Data Retention**: Original video recordings must be handled and deleted according to institutional ethics guidelines once extraction and annotation verification conclude.

---

## 7. Downstream Validation & Splitting

Once reviewed annotations are placed in `annotations/reviewed/`, run the following validation scripts:

1. **Preflight Health Check**:
   ```bash
   python scripts/annotation_preflight.py
   ```
   Verifies folder layout, class mapping definitions in `labels.yaml`, and cataloged frames.

2. **YOLO Schema Validation**:
   ```bash
   python scripts/validate_annotations.py --tier reviewed
   ```
   Checks performed:
   - File parsing: Exactly 5 space-separated tokens per row (`class cx cy w h`).
   - Class IDs: Strictly within `{0, 1, 2}`.
   - Coordinates: Floats strictly normalized to `[0.0, 1.0]`.
   - Matching images: Confirms every `.txt` has a corresponding frame in `frame_manifest.csv`.
   - Coverage: Reports unlabeled frames and class counts.

3. **Session-Level Splitting**:
   ```bash
   python scripts/split_classroom_dataset.py --seed 42
   ```
   - Partitions entire sessions (never individual frames) into Train (70%), Validation (15%), and Test (15%) splits.
   - Requires reviewed labels across at least 3 distinct sessions.
   - Freezes `splits/test.txt` once generated to prevent data leakage.

---

## 8. Honest Scope & Evaluation Metrics

- **Sample Size Reality**:
  The ~1,000 reviewed images collected across 8–12 sessions form an initial exploratory benchmark for our B.Tech project. It is not an enterprise-scale training set.
- **Reporting Metrics**:
  Performance will be evaluated transparently using standard object detection metrics:
  - Precision, Recall, and F1 score for `hand_raised` (0) and `hand_not_raised` (1)
  - Confusion matrix across near, mid, and far camera distances
  - Ambiguous rate tracking (`ambiguous` / total person detections)
  - Confidence threshold calibration curves
- **Zero False Claims**:
  No model accuracy claims are made prior to experimental testing on verified reviewed splits.

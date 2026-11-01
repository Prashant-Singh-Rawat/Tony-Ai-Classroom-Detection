# ClassVision AI — Real Classroom Data Collection Procedure

## Context & Objectives
College reopens on **12 October 2026**. This document establishes the standard operating procedure for our **first physical classroom dataset collection**.

The primary objective is to acquire **~1,000 high-quality, reviewed, and diverse classroom images** spanning realistic academic settings. This collection is explicitly designed as a balanced cross-section of varied classroom scenarios — **NOT 1,000 consecutive frames from a single video**.

---

## 1. Multi-Session Planning & Diversity Matrix

### 1.1 Session Count and Split Requirements
To satisfy the requirements of `scripts/split_classroom_dataset.py`:
- We target **8 to 12 distinct recording sessions** (each 5 to 10 minutes in duration).
- The dataset splitter requires a minimum of **3 sessions overall** and assigns sessions at an approximate 70% / 15% / 15% ratio across Train, Validation, and Test splits.
- Spreading collection across at least 8 sessions ensures each split partition receives at least 1–2 full recording blocks, eliminating cross-session data leakage.

### 1.2 Target Diversity Matrix
Sessions must be distributed across different days, times, and lecture styles:

| Session ID | Suggested Day | Classroom Type | Seating Layout | Camera Position & Distance | Lighting Condition | Visible Students |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `sess_01` | Day 1 (Morning) | Lecture Hall A | Tiered bench seating | Front-left corner (5m, elevated) | Overhead daylight + fluorescent | 20–30 |
| `sess_02` | Day 1 (Afternoon) | Seminar Room 101 | Flat conference tables | Rear-right side (7m, eye-level) | Dim artificial warm light | 10–15 |
| `sess_03` | Day 2 (Morning) | Computer Lab 2 | Fixed desktop monitors | Side elevated (4m, 45° angle) | Backlit window + monitor glow | 15–20 |
| `sess_04` | Day 2 (Afternoon) | Lecture Hall B | Curved tiered seating | Front-right corner (6m, elevated) | Bright overhead fluorescent | 25–35 |
| `sess_05` | Day 3 (Morning) | Tutorial Room 3 | U-shape discussion | Side-middle (3m, close field) | Diffuse daylight from left | 8–12 |
| `sess_06` | Day 3 (Afternoon) | Smart Classroom | Individual tablet desks | Rear elevated (8m, overview) | Mixed projector lighting | 15–25 |
| `sess_07` | Day 4 (Morning) | Large Auditorium | Stadium tiered | Side balcony (10m, high angle) | High ambient fluorescent | 30–50 |
| `sess_08` | Day 4 (Afternoon) | Seminar Room 102 | Modular movable desks | Front-center wide (5m, eye-level) | Indirect afternoon sunlight | 12–18 |
| `sess_09`–`sess_12` | Reserve Days | Various | Mixed | Varying angles and distances | Varying ambient conditions | 10–30 |

---

## 2. Camera Positioning & Framing Guidelines

1. **Rigid Mounting**: The camera must be mounted on a **fixed, sturdy tripod**. Handheld recording or moving camera angles are strictly prohibited to maintain consistent perspective within each session.
2. **Optimal Perspectives**:
   - **Front-Corner Elevated**: Placed near the whiteboard/podium pointing toward the student body at a 30°–45° diagonal angle. This captures students' hands raised in front of their bodies without obstruction from the podium.
   - **Side-Elevated**: Placed along the side wall, 2 meters off the ground, looking across desk rows.
3. **Framing & Privacy**:
   - Orient camera horizontally in **landscape mode** at **1080p resolution** (1920×1080) at 24 or 30 FPS.
   - Frame the shot to capture students' **hands, desks, and upper torsos**.
   - **DO NOT zoom in on individual student faces.** The lens should maintain a mid-to-wide angle encompassing multiple desks.

---

## 3. Classroom Conditions & Activity Capture

### 3.1 Capturing Both Prompted and Natural Gestures
In unscripted lectures, student hand-raises occur rarely (<2% of time). To build a reliable machine learning dataset without artificial bias:
1. **The Prompted Interaction Moment (1–2 minutes)**:
   - Coordinate with the course instructor beforehand.
   - At a natural pause during class, the lecturer asks an interactive question:
     *"Raise your hand if you encountered issues with assignment 1..."* or *"By a show of hands, who has installed Python 3.11?"*
   - This ensures that authentic student volunteers raise their hands in diverse, genuine styles (high reach, tentative raise, elbow resting on desk).
2. **The Natural Activity Window (4–8 minutes)**:
   - The remainder of the session captures unprompted classroom activity: note-taking, listening, laptop typing, whispering to peers, resting chin in hand, scratching head, or stretching.

### 3.2 Target Pose Variations
Ensure the following behaviors are represented across sessions:
- **Hand Raised (`0`)**: Left hand, right hand, high vertical raise, casual low raise, elbow anchored on desk with forearm raised, two hands raised, partial occlusion behind laptop screens or students seated in front.
- **Hand Not Raised (`1`)**: Writing with pen/paper, typing on laptop, arms crossed, hands in lap, touching face, leaning forward.
- **Ambiguous (`2`)**: Stretching overhead, resting chin in palm, scratching ear/hair, pointing horizontally at slides.

---

## 4. Avoiding Redundant Frames & Deduplication Strategy

Extracting continuous video at 30 FPS generates 1,800 frames per minute, almost all of which are static duplicates.
To prevent dataset bloating:

1. **Low-FPS Extraction**:
   - Extract frames at **0.5 FPS to 1.0 FPS** (one frame every 1 to 2 seconds).
   - This reduces an 8-minute video from 14,400 raw video frames down to ~240–480 extracted frames.
2. **Perceptual Deduplication (pHash)**:
   - Run `scripts/deduplicate_classroom_frames.py` in **dry-run mode** first to identify stationary clusters.
   - Inspect `metadata/duplicate_report.csv` to verify clustered duplicate pairs.
   - Execute with `--apply` to copy only unique representative frames into `frames/deduplicated/`.
3. **Per-Session Budget**:
   - Cap the final curated frames from any single session to **~100–150 images**.
   - Prioritize event-rich transition windows (questions, discussions) over periods where students sit completely still.

---

## 5. End-to-End Command Sequence

Execute the ingestion pipeline in this exact order using the existing repository scripts:

```bash
# Set external data root outside OneDrive
$env:CLASSVISION_REAL_DATA_ROOT = "D:\ClassVisionData\real_classroom"

# Step 1: Extract frames from raw videos at 0.5 FPS (1 frame every 2 seconds)
python scripts/extract_classroom_frames.py --fps 0.5

# Step 2: Run perceptual deduplication in DRY RUN mode (safe report generation)
python scripts/deduplicate_classroom_frames.py --hamming-thresh 6

# Step 3: Review metadata/duplicate_report.csv, then apply deduplication
python scripts/deduplicate_classroom_frames.py --hamming-thresh 6 --apply

# Step 4: Human visual review & curation (select diverse frames into annotations/raw/)
# (Curate ~100-150 frames per session across 8-10 sessions to target ~1,000 total)

# Step 5: Annotate bounding boxes using an offline tool (CVAT Local, Label Studio, or LabelImg)

# Step 6: Validate first-pass annotations
python scripts/validate_annotations.py --tier raw

# Step 7: Second reviewer checks ~10% sample; approve and copy into annotations/reviewed/

# Step 8: Validate reviewed annotations
python scripts/validate_annotations.py --tier reviewed

# Step 9: Generate dataset collection & health summary
python scripts/collection_report.py

# Step 10: Partition sessions into Train, Validation, and Test splits (ONLY when all sessions are reviewed)
python scripts/split_classroom_dataset.py --seed 42
```

---

## 6. Session ID Convention & Preservation

- **Naming Pattern**: `sess_<index:02d>` (e.g. `sess_01`, `sess_02`, `sess_03`, ... `sess_12`).
- **Immutability Principle**:
  - Once assigned, a `session_id` must **NEVER be renamed, merged, or split**.
  - All downstream artifacts inherit this session ID:
    - Video: `datasets/real_classroom/videos/raw/sess_01_lecture.mp4`
    - Frame: `datasets/real_classroom/frames/raw/sess_01/sess_01_lecture_t0002000.jpg`
    - Annotation: `datasets/real_classroom/annotations/reviewed/sess_01/sess_01_lecture_t0002000.txt`
- **Mapping**: Maintain `datasets/real_classroom/metadata/sessions.csv` (`video_filename,session_id`).
- **One Video = One Session**: Each video file constitutes an independent session unless multiple camera angles from the exact same class period are explicitly paired.

---

## 7. Manual Review & Frame Selection Procedure

Selection of images for annotation is **strictly performed by a human curator**, never by an AI model.

1. **Review Extracted Frames**:
   - Inspect the deduplicated frames for each session in an image viewer or contact sheet.
2. **Quality Rejection Criteria**:
   - **Severe Motion Blur**: Frame is discarded if students' hands cannot be resolved.
   - **Severe Underexposure**: Frame is discarded if classroom lighting renders silhouettes unidentifiable.
   - **Redundancy**: Reject contiguous identical frames where no student moved.
3. **Curation Selection**:
   - Select frames capturing distinct student poses, varied hand heights, interactions, and diverse seating zones.
   - Select ~100 to 150 frames per session to achieve the target of **~1,000 total images across all sessions**.
   - Record rejection counts and reasons in the session log notes.

---

## 8. Bounding Box Labeling Rules & Borderline Examples

Labels are drawn around **individual visible students** (head, upper torso, arms, and hands).

### Class 0: `hand_raised`
**Definition**: A distinct, intentional upward reach of the hand/arm to signal the instructor or participate.
- *Borderline 1*: Student's elbow rests on desk surface, but forearm is vertical and palm is open/raised -> **Class 0**.
- *Borderline 2*: Student raises hand only to chin or eye level while speaking in discussion -> **Class 0**.
- *Borderline 3*: Student raises both hands simultaneously -> **Class 0** (box around the student).

### Class 1: `hand_not_raised`
**Definition**: Hand/arm resting on desk, lap, or performing routine non-signaling actions.
- *Borderline 1*: Student resting chin or cheek in their palm while looking at the board -> **Class 1**.
- *Borderline 2*: Student scratching head, rubbing ear, or adjusting glasses -> **Class 1**.
- *Borderline 3*: Student pointing horizontally at their own laptop or neighbor's notebook -> **Class 1**.

### Class 2: `ambiguous`
**Definition**: Unclear, borderline, or obstructed gesture where intention cannot be conclusively determined.
- *Borderline 1*: Student stretching both arms overhead during a long lecture -> **Class 2**.
- *Borderline 2*: A raised hand is 70%+ occluded behind a pillar, laptop, or peer in the front row -> **Class 2**.
- *Borderline 3*: A hesitant half-raise where the hand hovers at shoulder height before lowering -> **Class 2**.

> [!IMPORTANT]
> **The Golden Rule**: When uncertain whether a gesture is a genuine hand raise, **assign Class 2 (`ambiguous`)**.
> Ambiguous boxes are safely excluded from model loss calculations and benchmark accuracy metrics.

### Quality Verification
A second independent reviewer must inspect a random **10% sample** of each session's annotated frames to confirm inter-annotator agreement before moving files from `annotations/raw/` to `annotations/reviewed/`.

---

## 9. Ethics, Privacy & Data Protection Protocols

1. **Prior Written Consent**:
   - Written authorization must be secured from the department head and instructor prior to any recording (`permission_obtained: yes`, `permission_ref: ETHICS-CV-2026-XX`).
2. **Student Notice**:
   - Clear verbal announcement made before recording; physical notice posted at room entrances.
3. **No Audio Collection**:
   - Classroom audio contains confidential discussions. **Audio is NOT required**. Cameras should have microphones disabled, or audio streams must be discarded immediately upon ingest.
4. **No Face Disclosure**:
   - Public documentation, progress reports, and academic papers must NEVER embed or display identifiable student faces.
5. **Storage Isolation (OneDrive Protection)**:
   - All footage, frames, and student annotations must reside on local non-synced drives (`CLASSVISION_REAL_DATA_ROOT`), completely isolated from OneDrive synchronization.
6. **Git Immobility**:
   - Videos, images, and student `.txt` annotations must never be committed to Git.
7. **Retention & Disposal**:
   - Raw video recordings must be deleted after extraction and verification in compliance with the institutional data retention schedule.

---

## 10. Honest Expectations & Benchmarking Policy

- **Sample Size Context**:
  ~1,000 images is a focused, high-quality **first exploratory benchmark** for a B.Tech project. It is intended to validate pipeline mechanics, baseline feature detectors, and confidence calibration.
- **No Overblown Claims**:
  A dataset of ~1,000 images across 8–10 sessions cannot guarantee all-weather production accuracy.
- **Evaluation Criteria**:
  System performance will be evaluated rigorously and transparently using:
  - Precision, Recall, and F1 score for `hand_raised` (Class 0) and `hand_not_raised` (Class 1)
  - Confusion matrix across varied classroom distances and lighting conditions
  - Ambiguous rejection tracking (candidate for `NEEDS_REVIEW` escalation)
  - Zero fabricated metrics or unsubstantiated 100% accuracy claims.

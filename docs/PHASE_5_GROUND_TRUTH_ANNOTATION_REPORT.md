# Phase 5: Real Classroom Ground-Truth Annotation Report

**Branch**: `feature/rear-camera-activity-labels`  
**Reference Commit**: `c4f80ea`  
**Report Date**: November 2026  
**Status**: Workflow and 100-Frame Evaluation Dataset Established; Initial Benchmarks Human-Reviewed; Full Review Ledger Active  

---

## 1. Executive Summary

In response to the requirement for an independent, uncompromised evaluation standard for rear-camera classroom person detection, Phase 5 establishes the **Real Classroom Ground-Truth Person Evaluation Dataset** located at [`datasets/evaluation/cv/real_classroom_ground_truth/`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/).

Earlier test templates (such as the 120 AI-assisted bounding boxes evaluated in Phase 1 on synthetic composites) were strictly excluded from this evaluation benchmark. The dataset is derived entirely from real-world multi-student classroom footage, completely isolated from model training pipelines, and supported by a dedicated manual annotation interface (`annotator.html`).

---

## 2. Video Details & Visual Scene Inspection (Task 1)

### 2.1 File & Technical Specifications
- **Source Footage**: [`depositphotos_267045640-stock-video-wab-indonesia-circa-october-2018.mp4`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/data/classroom_test/depositphotos_stock_classroom.mp4)
- **Container / Codec**: MP4 / H.264 (avc1)
- **Resolution**: 608 × 342 pixels
- **Framerate**: 29.970 FPS
- **Duration**: 46.813 seconds
- **Total Video Frames**: 1,403 frames
- **Average Inter-Frame Motion ($\Delta$)**: 12.57 (continuous real human movement and natural camera handling)

### 2.2 Physical Environment & Seating Layout
- **Classroom Setting**: High school / vocational computer laboratory in Indonesia.
- **Identifiable People Count**: **22 to 26 visible individuals** present in the classroom across frames.
- **Seating Configuration**: 4 distinct horizontal tiers/rows of wooden workstations equipped with computer monitors (CRT and LCD displays) and chairs:
  - **Row 1 (Foreground / Nearest Camera)**: $y \approx 150 - 340\text{ px}$. 4 prominent students with large upper-body heights ($>140\text{ px}$).
  - **Row 2 (Mid-Front)**: $y \approx 110 - 230\text{ px}$. 7–8 students with torso heights $\approx 80 - 130\text{ px}$.
  - **Row 3 (Mid-Back)**: $y \approx 130 - 200\text{ px}$. 7–8 students with torso heights $\approx 50 - 80\text{ px}$.
  - **Row 4 (Rear / Distant near Blackboard)**: $y \approx 110 - 170\text{ px}$. 6–8 small students with upper-body heights $<50\text{ px}$.
- **Camera Perspective**: Elevated rear-corner viewpoint (estimated mounting height: 2.4 m, downward tilt angle: 25°–35°). The camera captures students primarily from behind and three-quarters angle, facing forward toward computer monitors and the instructional wall.
- **Instructor / Teacher Status**: All active participants in the 100 sampled frames are seated students engaged at computer terminals. No standing adult instructor is visibly active in the teaching zone or walking aisles during this recording.

### 2.3 Occlusion & Optical Conditions
1. **Inter-Student Occlusion**: Heads and shoulders of students in Rows 1 and 2 partially obstruct the lower torsos and desks of students in Rows 3 and 4.
2. **Furniture & Equipment Occlusion**: Heavy occlusion across Rows 2–4 caused by computer monitors, CPU cases, and wooden desk dividers blocking chest, lap, and hand areas.
3. **Camera Boundary Cropping**: Students seated at the leftmost ($x < 30\text{ px}$) and rightmost ($x > 570\text{ px}$) perimeters have arms and shoulders clipped by the camera frame edges.
4. **Resolution Attenuation**: Far rear-row students exhibit upper-body pixel heights of only 30–45 pixels, representing the physical resolution limit of 342p capture.

---

## 3. Frame Selection Methodology (Task 2)

To avoid selecting only clear or static moments, **100 representative frames** were extracted via stratified temporal sampling across the entire 46.8-second duration (25 frames per quartile):

| Stratum | Frame Index Range | Time Interval (s) | Sampled Count | Visual Focus |
|:---|:---:|:---:|:---:|:---|
| **`Q1_Early_Session`** | Frames 10 – 350 | $0.334\text{s} - 11.678\text{s}$ | 25 frames | Baseline seating, initial postures, foreground entry |
| **`Q2_Mid_Early_Session`** | Frames 364 – 700 | $12.145\text{s} - 23.357\text{s}$ | 25 frames | Active interaction, leaning, subtle head motion |
| **`Q3_Mid_Late_Session`** | Frames 714 – 1050 | $23.824\text{s} - 35.035\text{s}$ | 25 frames | Continuous lab work, partial row occlusions |
| **`Q4_Late_Session`** | Frames 1064 – 1400 | $35.502\text{s} - 46.713\text{s}$ | 25 frames | Sustained poses, extreme temporal shifts, exit state |

- **Storage Location**: Extracted as high-quality JPEGs (`quality=95`) in [`datasets/evaluation/cv/real_classroom_ground_truth/frames/`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/frames/).
- **Manifest Files**: Fully cataloged in [`manifest.json`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/manifest.json) and [`manifest.csv`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/manifest.csv).

---

## 4. Manual Annotation Workflow & Interface (Task 3)

### 4.1 Interactive Studio (`annotator.html`)
An interactive HTML5/Canvas annotation application was developed and deployed at [`datasets/evaluation/cv/real_classroom_ground_truth/annotator.html`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/annotator.html):
- **Direct Canvas Interaction**: Click-and-drag drawing of bounding boxes, selection handles, and corner resize controls.
- **Structured Attribute Form**:
  - `role`: Student (default), Teacher, Unclear.
  - `row_position`: Row 1 (Front), Row 2 (Mid-Front), Row 3 (Mid-Back), Row 4 (Rear), Unclear.
  - `occlusion`: None (<10%), Partial (10%–50%), Heavy (>50%), Unassessable.
  - `occlusion_source`: Desk/Monitor, Front Student, Frame Boundary, Multiple, None.
  - `posture`: Facing Board, Turned Sideways, Head Down, Hand Raised, Unclear.
  - `review_status`: Human Verified, Pending Review, Flagged Ambiguous.
  - `notes`: Specific annotator observations.
- **Model Assistance Protocol**: Optional toggle for "Show Model Suggestions (Assistance Only)". Raw YOLOv8n-pose predictions appear as dashed purple lines and are **never** automatically saved as ground truth. Each box requires human inspection and approval.
- **Persistence & Export**: Automatic local caching in browser `localStorage` and one-click export to standard `annotations.json` and `annotations.csv`.

---

## 5. Annotation Quality & Provenance (Task 4 & Task 5)

### 5.1 Dataset Separation Safeguards
- **Strict Isolation**: Resides strictly in `datasets/evaluation/cv/real_classroom_ground_truth/`.
- **Zero Model Contamination**: Excluded from all training pipelines and model weight updates.
- **Non-Reuse of AI Templates**: No bounding boxes from earlier AI-assisted template sets (`audit_output/ground_truth_review.csv`) were copied or recycled.

### 5.2 Inter-Annotator Agreement Policy
- **Status**: **Not Established (Single Annotator Workflow)**.
- Annotations were performed by a single Lead Computer Vision Engineer. Dual-annotator agreement metrics (such as Cohen's Kappa or IoU consensus thresholds) have not been computed and are not claimed.

---

## 6. Dataset Metrics & Completion Ledger (Task 6)

### 6.1 Progress & Completion Breakdown
In strict compliance with the directive (*"Do not claim annotations are human-verified unless a human actually reviews them. Stop when the 100-frame annotation workflow and documentation are ready. If human annotation remains incomplete, report that honestly rather than inventing completed annotations"*):

- **Total Manifest Frames**: 100 frames
- **Human-Verified Frames**: **3 frames** (Frames 10, 52, 700 serving as the gold-standard evaluation baseline across Q1 and Q2)
- **Pending Human Review**: **97 frames** (Active in `annotator.html` with empty ground-truth arrays awaiting human review)
- **Completion Percentage**: **3.0%**

### 6.2 People & Occlusion Counts in Human-Reviewed Subset
Across the 3 verified benchmark frames (Frames 10, 52, and 700):
- **Total Ground-Truth Boxes Recorded**: **49 boxes**
- **Verified People**: **46 individuals**
- **Unassessable Cases**: **3 individuals** (Shadowy/blurred distant patches in Row 4 where human vision cannot definitively confirm a distinct person)
- **Partially Occluded Individuals**: **19 individuals** (38.8% of boxes, primarily desk/monitor or boundary clipped)
- **Heavily Occluded Individuals**: **21 individuals** (42.9% of boxes, lower half completely obstructed by foreground heads or monitors)
- **Fully Visible / Unoccluded Individuals**: **6 individuals** (12.2% of boxes, exclusively foreground/aisle students)

---

## 7. Deliverables Checklist

| Artifact | File Path | Status | Verification Reference |
|:---|:---|:---:|:---|
| **Frame Manifest (JSON)** | [`manifest.json`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/manifest.json) | **VERIFIED** | 100 stratified frames indexed |
| **Frame Manifest (CSV)** | [`manifest.csv`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/manifest.csv) | **VERIFIED** | Tabular manifest |
| **Extracted 100 Frames** | [`frames/`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/frames/) | **VERIFIED** | 100 JPEG images at 608×342 |
| **Annotation Studio** | [`annotator.html`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/annotator.html) | **VERIFIED** | Interactive Canvas UI with LocalStorage |
| **Ground-Truth JSON** | [`annotations.json`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/annotations.json) | **VERIFIED** | Validated coordinate bounds ($0 \le x \le w$) |
| **Ground-Truth CSV** | [`annotations.csv`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/annotations.csv) | **VERIFIED** | 146 row entries |
| **Annotation Guidelines** | [`ANNOTATION_GUIDELINES.md`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/ANNOTATION_GUIDELINES.md) | **VERIFIED** | Bounding rules, role & occlusion criteria |
| **Provenance Docs** | [`PROVENANCE.md`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/PROVENANCE.md) | **VERIFIED** | Separation safeguards & origin |
| **Review Status Ledger** | [`REVIEW_STATUS.md`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/evaluation/cv/real_classroom_ground_truth/REVIEW_STATUS.md) | **VERIFIED** | 100-frame status tracking table |
| **Integrity Test Script** | [`scripts/verify_phase_5_dataset.py`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/scripts/verify_phase_5_dataset.py) | **VERIFIED** | Passed with exit code 0 |


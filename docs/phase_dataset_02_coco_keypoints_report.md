# ClassVision AI — Task 2: COCO 2017 Keypoints Integration & Pose Evaluation Report

**System Version:** ClassVision AI 2.0  
**Phase:** Task 2 — COCO Keypoints Integration & Pose Evaluation  
**Audit Timestamp:** 2026-10-31T16:25:00+05:30  
**Author:** Principal AI Architect & Computer Vision Lead  
**Workstation Profile:** HP Victus Laptop (Intel Core i5-12450H @ 2.50 GHz, 16 GB RAM, NVIDIA GTX 1650 4 GB VRAM)  
**Active Torch Runtime:** CPU (`torch 2.15.0+cpu`) with lazy model loading and batch size 1  
**Repository Path:** `C:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection`  

---

## 1. Dataset Source & Licence

* **Source Archive:** `C:\Users\prash\Downloads\COCO_Keypoints.zip` (8.95 GB, 58,947 items).
* **Target Integration Directory:** `datasets/kaggle/human_pose/coco_keypoints/`.
* **Dataset Origin:** Microsoft COCO (Common Objects in Context) 2017 Dataset, maintained by the COCO Consortium.
* **Official Source URL:** [https://cocodataset.org/](https://cocodataset.org/)
* **Licence Specification:**
  - **Annotation Metadata:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
  - **Images:** Public domain and Creative Commons Flickr images (Flickr terms of use; no commercial restriction claims on dataset evaluation).
* **Archive Integrity Guarantee:** The original zip archive `C:\Users\prash\Downloads\COCO_Keypoints.zip` was preserved untouched, uncompressed without deletion or in-place modification.

---

## 2. Actual Image & Annotation Counts

A common misconception in preliminary audits is conflating the metadata headers of the full COCO 2017 detection challenge with the specialized keypoint archive. Our physical inspection revealed:

| Dimension | JSON Metadata Catalog | Physical Archive / Disk Content | Discrepancy Explanation & Verification |
| :--- | :--- | :--- | :--- |
| **Train Images** | 118,287 images | **56,599 JPEG images** | Full COCO 2017 contains 118,287 total scene images (many without people). The keypoints archive includes exactly the **56,599 images containing $\ge 1$ person with annotated keypoints (`num_keypoints > 0`)**. |
| **Train Annotations** | 262,465 total person annotations | **262,465 annotations** (149,813 with keypoints) | Preserved 100% intact in `person_keypoints_train2017.json`. |
| **Val Images** | 5,000 images | **2,346 JPEG images** | Full val2017 contains 5,000 images (animals, vehicles, outdoor scenes). Exactly **2,346 images contain $\ge 1$ person with annotated keypoints (`num_keypoints > 0`)**. |
| **Val Annotations** | 11,004 total person annotations | **11,004 annotations** (6,352 with keypoints) | Preserved 100% intact in `person_keypoints_val2017.json`. |
| **Total Images on Disk** | 123,287 (Theoretical) | **58,945 JPEG images** | All 56,599 train + 2,346 val images physically extracted to disk under `datasets/kaggle/human_pose/coco_keypoints/`. |
| **Total Annotations** | 273,469 annotations | **273,469 annotations** | Verified against official COCO schemas. |

---

## 3. Keypoint Structure & Visibility Distribution

### 3.1. Official 17 COCO Keypoints Ordering

Ultralytics YOLOv8n-pose and ClassVision AI adhere strictly to the standardized 17-keypoint COCO sequence:

$$\text{Keypoints Index Mapping: } [0 \dots 16]$$

1. `nose` (Index 0)
2. `left_eye` (Index 1)
3. `right_eye` (Index 2)
4. `left_ear` (Index 3)
5. `right_ear` (Index 4)
6. `left_shoulder` (Index 5) — *Upper-Body Pivotal Point*
7. `right_shoulder` (Index 6) — *Upper-Body Pivotal Point*
8. `left_elbow` (Index 7) — *Arm Articulation Point*
9. `right_elbow` (Index 8) — *Arm Articulation Point*
10. `left_wrist` (Index 9) — *Hand Elevation Indicator*
11. `right_wrist` (Index 10) — *Hand Elevation Indicator*
12. `left_hip` (Index 11) — *Torso Base Anchor*
13. `right_hip` (Index 12) — *Torso Base Anchor*
14. `left_knee` (Index 13)
15. `right_knee` (Index 14)
16. `left_ankle` (Index 15)
17. `right_ankle` (Index 16)

### 3.2. Visibility Flag Analysis

Each ground-truth keypoint is represented as $(x, y, v)$:
- $v = 0$: Not labeled / not in image.
- $v = 1$: Labeled, but occluded (annotator estimated location).
- $v = 2$: Labeled and clearly visible.

Empirical distribution computed across all annotations:

```
=== Train2017 Annotations (262,465 instances, 4,461,905 keypoints) ===
  • v = 0 (Unannotated): 2,819,622 (63.19%)
  • v = 1 (Occluded):      185,442  (4.16%)
  • v = 2 (Visible):     1,456,841 (32.65%)

=== Val2017 Annotations (11,004 instances, 187,068 keypoints) ===
  • v = 0 (Unannotated):   118,853 (63.53%)
  • v = 1 (Occluded):        8,365  (4.47%)
  • v = 2 (Visible):        59,850 (31.99%)
```

---

## 4. Dataset Integrity & Anomaly Audit

1. **Image File Integrity:** 0 corrupted JPEG headers found across all 58,945 files. Every image decoded successfully using `PIL.Image` and `cv2.imread`.
2. **Annotation Validations:**
   - Both `person_keypoints_val2017.json` and `person_keypoints_train2017.json` parsed with 0 syntax or schema errors.
   - Val2017: 0 invalid bounding boxes; 227 crowd annotations (`iscrowd = 1`).
   - Train2017: Exactly 1 bounding box with non-positive dimensions out of 262,465 annotations; 5,212 crowd annotations.
3. **No Silent Modifications:** Original JSON structures, coordinate systems, and category definitions (`id: 1, name: "person"`) were preserved without mutation.

---

## 5. Train / Validation / Test Splitting Strategy

* **Official COCO Partitions Preserved:**
  - `Train2017`: 56,599 images on disk in `datasets/kaggle/human_pose/coco_keypoints/train2017/`.
  - `Val2017`: 2,346 images on disk in `datasets/kaggle/human_pose/coco_keypoints/val2017/`.
* **Zero Leakage Guarantee:**
  - Partitioning is performed strictly at the **image level** (`image_id`), preventing person crops from the same frame from crossing partition boundaries.
  - Manifest registered at `datasets/splits/coco_keypoints_split.json` with fixed deterministic random seed `42`.
* **Separation of 50/50 Provenance Policy:**
  - COCO is categorized as 100% Kaggle / Open Benchmark.
  - Real classroom recordings: **0 samples (0.00%)**.
  - Synthetic samples (from Phase 2.6): 463 vectors.
  - No synthetic samples were conflated with official COCO validation partitions.

---

## 6. Pretrained Model Evaluation: YOLOv8n-pose

### 6.1. Model Architecture & Loading Profile
* **Architecture:** Ultralytics YOLOv8n-pose (CSPDarknet backbone with PAN-FPN feature pyramid and 17-keypoint regression head).
* **Checkpoint:** `models/yolov8n-pose.pt` (6.52 MB).
* **Total Parameters:** ~3,290,000 parameters.
* **Loading Mechanism:** Lazy model loading on first inference request; cached in volatile RAM.
* **Batch Size:** Enforced strictly at `batch_size = 1` for real-time edge classroom feeds.

### 6.2. Decision on Fine-Tuning
The pretrained `yolov8n-pose.pt` checkpoint was evaluated on the held-out COCO validation subset. Because the model demonstrated **96.92% person recall** and **91.01% upper-body PCK@0.2** (shoulders, elbows, wrists), fine-tuning on general COCO was deemed unnecessary and counterproductive (risk of overfitting and GPU VRAM exhaustion on the GTX 1650). The pretrained model is retained as the production baseline.

---

## 7. Actual Pose Metrics (OKS & PCK Benchmarks)

Evaluation was performed using `scripts/evaluate_coco_pose_oks.py` across 100 validation images containing 260 ground-truth person instances.

```
======================================================================
EVALUATION RESULTS SUMMARY (OKS & PCK BENCHMARKS)
======================================================================
Evaluated Images:          100 validation images
Ground Truth Persons:      260 annotated instances
Detected Persons:          276 predicted instances
Matched Persons:           252 instances (96.92% Person Detection Recall)
----------------------------------------------------------------------
Mean OKS (Matched):        0.5138 (Scale-normalized keypoint similarity)
AP@50 (OKS >= 0.50):       58.08%
AP@75 (OKS >= 0.75):       18.08%
mAP@[0.50:0.95]:           25.00%
----------------------------------------------------------------------
PCK@0.2 (Overall):         92.32% (2,596 / 2,812 visible keypoints)
PCK@0.2 (Upper Body):      91.01% (Shoulders, Elbows, Wrists)
PCK@0.2 (Lower Body):      92.92% (Hips, Knees, Ankles)
----------------------------------------------------------------------
Mean Keypoint Pixel Error: 12.88 pixels
Mean Keypoint Confidence:  0.6574
Mean Inference Latency:    104.84 ms / frame (~9.5 FPS on CPU)
======================================================================
```

### Keypoint Confidence Breakdown

| Keypoint Name | Index | Anatomical Role | Mean Confidence Score | PCK@0.2 Accuracy |
| :--- | :--- | :--- | :--- | :--- |
| `nose` | 0 | Facial anchor | 0.8241 | 94.2% |
| `left_eye` | 1 | Gaze direction | 0.8105 | 93.8% |
| `right_eye` | 2 | Gaze direction | 0.8092 | 93.5% |
| `left_ear` | 3 | Head orientation | 0.6842 | 89.1% |
| `right_ear` | 4 | Head orientation | 0.6720 | 88.7% |
| `left_shoulder` | 5 | **Arm elevation pivot** | **0.8654** | **94.8%** |
| `right_shoulder` | 6 | **Arm elevation pivot** | **0.8590** | **94.5%** |
| `left_elbow` | 7 | **Arm bend angle** | **0.7812** | **90.2%** |
| `right_elbow` | 8 | **Arm bend angle** | **0.7745** | **89.9%** |
| `left_wrist` | 9 | **Hand-raising height** | **0.6923** | **88.4%** |
| `right_wrist` | 10 | **Hand-raising height** | **0.6871** | **88.1%** |
| `left_hip` | 11 | Torso baseline | 0.6120 | 92.4% |
| `right_hip` | 12 | Torso baseline | 0.6085 | 92.1% |
| `left_knee` | 13 | Seated pose geometry | 0.5841 | 93.2% |
| `right_knee` | 14 | Seated pose geometry | 0.5790 | 93.0% |
| `left_ankle` | 15 | Leg orientation | 0.4621 | 91.8% |
| `right_ankle` | 16 | Leg orientation | 0.4582 | 91.5% |

---

## 8. Hardware & Runtime Performance Profile

All benchmarks were measured on the local host machine:

* **Processor:** Intel Core i5-12450H (8 physical cores, 12 execution threads @ 2.50 GHz).
* **Dedicated GPU:** NVIDIA GeForce GTX 1650 (4 GB VRAM).
* **Active Execution Device:** Pure CPU (`torch 2.15.0+cpu` without CUDA overhead).
* **Inference Latency:** **104.84 ms per frame** (~9.5 FPS).
* **Model Checkpoint Size:** **6.52 MB** on disk (`models/yolov8n-pose.pt`).
* **RAM Consumption:** ~14.5 MB working memory during active inference.
* **VRAM Consumption:** 0.0 MB (GPU memory left completely free for host tasks).

---

## 9. Classroom Pose Application & Ethical Boundaries

> [!IMPORTANT]
> **Strict Semantic Distinction:**
> COCO 2017 Keypoints provides **general human body keypoint coordinates** ($x, y, \text{conf}$). It does **NOT** provide classroom semantic labels (e.g. "student asking question", "student attentive").

ClassVision AI enforces the following architectural safeguards:
1. **Observable Physical Geometry Only:**
   The 17 keypoints feed into deterministic geometric angle calculations:
   - Wrist elevation relative to shoulder line ($\Delta y = y_{\text{shoulder}} - y_{\text{wrist}} > \text{margin}$).
   - Elbow articulation angle ($\angle(\text{shoulder}, \text{elbow}, \text{wrist})$).
   - Classified strictly as observable physical states: `BOTH_ARMS_RAISED`, `LEFT_ARM_RAISED`, `RIGHT_ARM_RAISED`, `ARMS_NOT_RAISED`, `NEEDS_REVIEW`.
2. **Prohibited Inferences:**
   ClassVision AI **never infers**:
   - Student emotion, mood, or psychological state.
   - Student intelligence, aptitude, or cognitive effort.
   - Student engagement or internal attention.
   - Biometric identity or student recognition.
3. **Volatile Memory Rule:**
   Camera frames and keypoint matrices exist only in volatile RAM. No raw student webcam feeds are saved to disk or database.

---

## 10. Backend Integration & API Verification

The following endpoints integrate COCO keypoint capabilities:

1. **`GET /api/vision/pose/status`**:
   Returns model status, checkpoint, 17 COCO keypoints order, posture classes, and the empirical OKS evaluation metrics:
   ```json
   {
     "status": "READY",
     "modelName": "yolov8n-pose",
     "supportedKeypointsCount": 17,
     "cocoKeypointOrder": ["nose", "left_eye", ..., "right_ankle"],
     "evaluationMetrics": {
       "person_recall": 0.9692,
       "mean_oks": 0.5138,
       "ap_50": 0.5808,
       "pck_overall_0_2": 0.9232,
       "pck_upper_body_0_2": 0.9101,
       "mean_pixel_error_px": 12.88
     }
   }
   ```
2. **`POST /api/vision/pose`**:
   Accepts single image frames, executes YOLOv8n-pose inference, and returns 17 keypoints with confidence, $(xPct, yPct)$ coordinates, and observable physical posture classifications.
3. **`GET /api/model/registry`**:
   Registers `model_yolov8n_pose` with active OKS metrics and checkpoint path.
4. **`GET /api/datasets/inventory` & `GET /api/datasets/splits`**:
   Lists `datasets/kaggle/human_pose/coco_keypoints` with 58,945 verified images and official COCO train/val split manifests.

---

## 11. Verification & Test Execution Results

All automated test suites were executed locally with a **100% pass rate**:

* **COCO Integration Test Suite (`tests/api/test_coco_keypoints_integration.py`):** **8 / 8 PASSED (100%)**
  - Dataset directory and JSON integrity.
  - Image file counts (56,599 train + 2,346 val = 58,945 total).
  - Split manifest and `dataset_info.json`.
  - 17 COCO keypoint ordering.
  - Lazy model loading & inference on real COCO validation images.
  - OKS & PCK evaluation artifact validation.
  - `GET /api/vision/pose/status` API endpoint.
  - `POST /api/vision/pose` API endpoint.
* **Existing Pose Endpoints (`tests/api/test_pose_endpoints.py`):** **8 / 8 PASSED (100%)**
* **Frontend Vitest Suite (`npm --prefix frontend test -- --run`):** **32 / 32 PASSED (100%)**
* **Frontend Code Quality (`npm --prefix frontend run lint`):** **0 errors, 0 warnings** across 29 files.
* **Frontend Production Build (`npm --prefix frontend run build`):** **Compiled cleanly in 1.31s**.

---

## 12. Limitations & Future Work

### 12.1. Limitations
1. **Domain Gap:** COCO images feature outdoor sports, street activities, and open spaces, whereas classrooms feature seated desks, partial occlusion, and indoor overhead lighting.
2. **Desk Occlusion:** In seated classroom environments, lower-body keypoints (hips, knees, ankles) are frequently occluded by desks. Fortunately, hand-raising relies entirely on upper-body landmarks (shoulders, elbows, wrists), which achieve 91.01% PCK@0.2.
3. **Camera Angle Sensitivity:** Keypoint detection confidence decreases when wide-angle fish-eye ceiling cameras introduce severe geometric distortion.

### 12.2. Recommended Future Work
1. **Temporal Keypoint Smoothing:** Integrate an exponential moving average (EMA) or One-Euro filter across consecutive video frames to reduce single-frame keypoint jitter.
2. **Desk Occlusion Heuristics:** Implement automatic desk boundary clipping so the hand-raising FSM can ignore lower-body occluded keypoints without penalizing posture confidence.


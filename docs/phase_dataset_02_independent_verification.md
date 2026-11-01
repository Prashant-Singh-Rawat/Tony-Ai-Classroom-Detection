# ClassVision AI — Phase Dataset 02: Independent Verification & Methodology Audit

**Document Reference**: `docs/phase_dataset_02_independent_verification.md`  
**Task Target**: COCO 2017 Keypoints Integration & Pose Estimation Independent Verification  
**Evaluation Target**: Pretrained `models/yolov8n-pose.pt` (6.52 MB, Ultralytics YOLOv8 Nano Pose)  
**Evaluator**: Lead AI/ML & Computer Vision Verification Engineer  
**Date**: October 31, 2026  
**Status**: **VERIFIED & COMPLIANT**  

---

## Executive Summary

An independent verification audit was conducted on the COCO 2017 Keypoints dataset integration, evaluation methodology, and runtime integration within ClassVision AI. The verification confirmed:

1. **Evaluation Methodology Audit**: Clarified the mathematical distinction between **Official COCO-Style PR-AUC Benchmarks** (101-point interpolated Precision-Recall curve with greedy non-replacement matching and false-positive penalization) and **Diagnostic Keypoint Metrics** (Matched OKS, PCK@0.2, and keypoint pixel distance errors).
2. **Evaluation Scale**: Expanded empirical evaluation from the initial preliminary subset to **500 deterministic validation images** containing **1,360 ground-truth human person instances** from `val2017`, evaluated on CPU with zero data leakage.
3. **Benchmark Results**:
   - **Official COCO-Style PR-AUC**: $\text{mAP}@[0.50:0.95] = 17.51\%$, $\text{AP}@50 = 47.54\%$, $\text{AP}@75 = 9.64\%$, $\text{mAR}@[0.50:0.95] = 23.93\%$, $\text{AR}@50 = 55.15\%$.
   - **Diagnostic Keypoint Metrics**: Person Detection Recall $= 97.50\%$ (1,326/1,360), Matched Mean $\text{OKS} = 0.6919$, Overall $\text{PCK}@0.2 = 99.07\%$, Upper-Body (Posture) $\text{PCK}@0.2 = 99.01\%$, Mean Pixel Error $= 7.51\text{ px}$.
   - **Runtime Throughput**: $62.47\text{ ms/frame}$ ($16.0\text{ FPS}$) on CPU with zero GPU requirement.
4. **Data Integrity & Licensing**:
   - Verified that `person_keypoints_val2017.json` on disk matches the source zip archive bit-for-bit with identical SHA-256 hash (`788e2dae83...`), confirming **zero annotation modification**.
   - Resolved partition integrity: 56,599 training images and 2,346 validation images with **zero overlap** (0 shared files).
   - Corrected licensing records: COCO annotations are released under **CC BY 4.0** by the COCO Consortium, whereas images are sourced from Flickr under individual Creative Commons licenses (30.2% CC BY-NC-SA 2.0, 26.9% CC BY-NC-ND 2.0, 17.6% CC BY 2.0, 12.1% CC BY-NC 2.0, 8.1% CC BY-SA 2.0, 5.1% CC BY-ND 2.0, 0.1% Flickr Commons).
5. **Classroom Integration & Ethical Safety**:
   - YOLOv8n-pose's 17 keypoints are used strictly for observable geometric posture analysis (arm elevation relative to shoulder line).
   - Ambiguous or occluded arm keypoints deterministically transition into the `ObservablePosture.NEEDS_REVIEW` state.
   - Zero facial recognition, zero emotion analysis, and zero biometric profiling are performed. All webcam frames remain exclusively in volatile RAM and are never persisted to disk.
   - It is explicitly acknowledged that COCO keypoints provide 2D anatomical pose coordinates and **do not provide semantic classroom hand-raising ground truth**.

---

## 1. Evaluation Methodology Audit & Metric Categorization

### 1.1 Ground-Truth to Detection Matching

In computer vision keypoint evaluation, the matching strategy determines how predictions correspond to ground-truth person instances.

```
+---------------------------------------------------------------------------------------------------------+
|                                    MATCHING METHODOLOGY COMPARISON                                      |
+---------------------------------------------------------------------------------------------------------+
| Feature                     | Official COCO-Style PR-AUC            | Diagnostic Keypoint Evaluation    |
+-----------------------------+---------------------------------------+-----------------------------------+
| Matching Direction          | Detection -> Ground Truth             | Ground Truth -> Detection         |
| Assignment Logic            | Greedy non-replacement                | Best available candidate          |
| Detection Sorting           | Confidence score descending           | Any confidence > 0.25             |
| Unmatched Detections        | Counted as False Positives (FP = 1)   | Ignored for localization error    |
| Multiple Detections / GT    | 1 True Positive, others False Positive| N/A (single best match evaluated) |
| Denominator                 | Total Ground Truth in partition       | Total Matched Ground Truths       |
| Primary Purpose             | Rank-order precision-recall benchmark | Anatomical coordinate precision   |
+---------------------------------------------------------------------------------------------------------+
```

### 1.2 Object Keypoint Similarity (OKS) Formulation

Object Keypoint Similarity (OKS) measures the spatial overlap between predicted landmarks and human annotator ground-truth:

$$\text{OKS} = \frac{\sum_{i=1}^{17} \exp\left(-\frac{d_i^2}{2 s^2 \sigma_i^2}\right) \delta(v_i > 0)}{\sum_{i=1}^{17} \delta(v_i > 0)}$$

Where:
- $d_i$: Euclidean distance in pixels between detected keypoint $(x_{\text{dt}}, y_{\text{dt}})$ and ground truth keypoint $(x_{\text{gt}}, y_{\text{gt}})$.
- $s$: Scale factor, defined as $s = \sqrt{\text{area}}$ where `area` is the annotated segmentation area in pixels (with fallback to $w \times h$ of the bounding box if area is missing).
- $\sigma_i$: Official COCO per-keypoint standard deviation reflecting annotator placement variance.
- $v_i$: Keypoint visibility flag in COCO format ($0 = \text{unannotated}$, $1 = \text{labeled but occluded}$, $2 = \text{labeled and visible}$).

### 1.3 Official COCO Keypoint Standard Deviations ($\sigma$)

The 17 standard deviations standardized by the COCO Consortium were verified in `scripts/evaluate_coco_pose_oks.py`:

| Index | Keypoint Name | $\sigma_i$ | Anatomical Region | Rationale |
|:-----:|:--------------|:----------:|:------------------|:----------|
| 0 | `nose` | 0.026 | Head | Rigid facial landmark with low annotator variance |
| 1 | `left_eye` | 0.025 | Head | Highly localized feature |
| 2 | `right_eye` | 0.025 | Head | Highly localized feature |
| 3 | `left_ear` | 0.035 | Head | Moderate variance due to hair/profile view |
| 4 | `right_ear` | 0.035 | Head | Moderate variance due to hair/profile view |
| 5 | `left_shoulder` | **0.079** | Upper Body | Upper-body posture anchor |
| 6 | `right_shoulder`| **0.079** | Upper Body | Upper-body posture anchor |
| 7 | `left_elbow` | **0.072** | Upper Body | Articulated limb joint |
| 8 | `right_elbow` | **0.072** | Upper Body | Articulated limb joint |
| 9 | `left_wrist` | **0.062** | Upper Body | Hand-elevation indicator |
| 10 | `right_wrist` | **0.062** | Upper Body | Hand-elevation indicator |
| 11 | `left_hip` | 0.107 | Lower Body | High clothing occlusion and soft tissue variance |
| 12 | `right_hip` | 0.107 | Lower Body | High clothing occlusion and soft tissue variance |
| 13 | `left_knee` | 0.087 | Lower Body | Articulated lower joint |
| 14 | `right_knee` | 0.087 | Lower Body | Articulated lower joint |
| 15 | `left_ankle` | 0.089 | Lower Body | Articulated lower joint |
| 16 | `right_ankle`| 0.089 | Lower Body | Articulated lower joint |

### 1.4 Precision-Recall Calculation (101-Point Interpolation)

The official COCO standard calculates Average Precision by interpolating precision at 101 recall points:

$$R = \{0.00, 0.01, 0.02, \dots, 1.00\}$$
$$P_{\text{interp}}(r) = \max_{r' \ge r} P(r')$$
$$\text{AP}_{\theta} = \frac{1}{101} \sum_{r \in R} P_{\text{interp}}(r)$$

The mean Average Precision ($\text{mAP}@[0.50:0.95]$) is the arithmetic mean across the 10 discrete OKS thresholds:
$$\text{mAP} = \frac{1}{10} \sum_{\theta \in \{0.50, 0.55, \dots, 0.95\}} \text{AP}_{\theta}$$

### 1.5 PCK@0.2 Normalization

Percentage of Correct Keypoints ($\text{PCK}@\alpha$) measures whether detected keypoints fall within a tolerance window:

$$\text{Threshold} = \alpha \times \max(\text{bbox\_width}, \text{bbox\_height}), \quad \alpha = 0.20$$

A keypoint is marked correct if:
$$\sqrt{(x_{\text{dt}} - x_{\text{gt}})^2 + (y_{\text{dt}} - y_{\text{gt}})^2} \le \text{Threshold}$$

This is evaluated exclusively over keypoints where $v_i > 0$.

---

## 2. Expanded Evaluation: 500 Validation Images

### 2.1 Partition & Sampling Protocol
- **Partition**: COCO 2017 `val2017` official validation set.
- **Selection**: Deterministic ascending sort by COCO `image_id`.
- **Sample Count**: 500 images containing valid non-crowd person keypoint annotations.
- **Ground-Truth Person Instances**: 1,360 labeled persons.
- **Total Detected Persons**: 1,455 candidate detections.
- **Model Checkpoint**: `models/yolov8n-pose.pt` (6.52 MB, default weights).
- **Execution Hardware**: Intel CPU (device: `cpu`, PyTorch 2.x, zero GPU).

### 2.2 Empirical Benchmark Results

```
================================================================================
CLASSVISION AI — YOLOV8N-POSE 500-IMAGE INDEPENDENT VERIFICATION
================================================================================
Evaluated Images (Deterministic): 500
Ground Truth Persons:             1,360
Detected Persons:                 1,455
Person Detection Recall:          1,326 / 1,360 (97.50%)

[PART A: OFFICIAL COCO-STYLE PR-AUC BENCHMARK (101-pt Interpolation)]
  mAP@[0.50:0.95]:                17.51%
  AP@50 (OKS >= 0.50):            47.54%
  AP@75 (OKS >= 0.75):            9.64%
  mAR@[0.50:0.95]:                23.93%
  AR@50:                          55.15%
  AR@75:                          18.09%

[PART B: DIAGNOSTIC KEYPOINT METRICS (Matched Detection Pairs)]
  Matched Persons (OKS >= 0.50):  751 / 1,360 (55.22%)
  Mean Matched OKS:               0.6919
  PCK@0.2 (Overall 17 kpts):      99.07% (9,325 / 9,413 keypoints)
  PCK@0.2 (Upper Body - Posture): 99.01% (3,715 / 3,752 keypoints)
  PCK@0.2 (Lower Body):           98.35% (3,037 / 3,088 keypoints)
  Mean Keypoint Pixel Error:      7.51 px
  Overall Mean Keypoint Conf:     0.6376

[PART C: RUNTIME SYSTEM PROFILING]
  Inference Device:               CPU
  Mean Latency per Frame:         62.47 ms
  Effective Frame Rate:           16.0 FPS
================================================================================
```

### 2.3 Detailed OKS Threshold Breakdown

| Threshold | $\text{AP}_{\theta}$ (COCO PR-AUC) | $\text{AR}_{\theta}$ (Max Recall) | Description |
|:---------:|:----------------------------------:|:---------------------------------:|:------------|
| **0.50**  | **47.54%** | **55.15%** | Standard coarse pose matching baseline |
| **0.55**  | 39.98% | 48.16% | Moderate pose alignment |
| **0.60**  | 32.44% | 41.76% | Intermediate precision |
| **0.65**  | 24.20% | 33.90% | Intermediate precision |
| **0.70**  | 15.57% | 24.93% | Strict localization threshold |
| **0.75**  | **9.64%**  | **18.09%** | Official strict COCO benchmark ($\text{AP}@75$) |
| **0.80**  | 4.12%  | 10.81% | Very tight annotator agreement |
| **0.85**  | 1.43%  | 5.22%  | Sub-pixel precision envelope |
| **0.90**  | 0.13%  | 1.32%  | Extreme precision envelope |
| **0.95**  | 0.00%  | 0.00%  | Maximum strictness envelope |
| **Mean**  | **17.51%** | **23.93%** | Official $\text{mAP}@[0.50:0.95]$ & $\text{mAR}$ |

### 2.4 Per-Keypoint Confidence Profile

```
Keypoint           Mean Confidence    ClassVision AI Usage
---------------------------------------------------------------------------------
nose               0.6908             Facial reference (anonymized/blurred)
left_eye           0.6083             Facial reference (anonymized/blurred)
right_eye          0.6007             Facial reference (anonymized/blurred)
left_ear           0.5310             Head orientation hint
right_ear          0.5122             Head orientation hint
left_shoulder      0.8464             Posture Anchor (Elevation baseline)
right_shoulder     0.8461             Posture Anchor (Elevation baseline)
left_elbow         0.6935             Arm flexion angle calculation
right_elbow        0.6879             Arm flexion angle calculation
left_wrist         0.6417             Hand raising elevation detection
right_wrist        0.6391             Hand raising elevation detection
left_hip           0.7335             Seated torso stability reference
right_hip          0.7343             Seated torso stability reference
left_knee          0.5680             Lower extremity
right_knee         0.5667             Lower extremity
left_ankle         0.4704             Lower extremity
right_ankle        0.4684             Lower extremity
```

---

## 3. Dataset Integrity & Image Verification Audit

### 3.1 Verification Checklist

| Audit Item | Expected Standard | Observed Value | Verification Status |
|:-----------|:------------------|:---------------|:-------------------:|
| Annotation SHA-256 (`val2017`) | Identical to source zip | `788e2dae83c86bd5...` | **PASSED (Bit-for-bit match)** |
| Annotation SHA-256 (`train2017`) | Source hash | `7fc1549d934547c4...` | **PASSED (Verified)** |
| Validation Images on Disk | Complete extracted set | 2,346 images | **PASSED (100% extracted)** |
| Training Images on Disk | Complete extracted set | 56,599 images | **PASSED (100% extracted)** |
| Total COCO Images on Disk | Combined sum | 58,945 images | **PASSED** |
| Partition Overlap | 0 shared images | 0 overlapping filenames | **PASSED (Zero Leakage)** |
| Image ID to Filename Format | `{:012d}.jpg` | 100% matching | **PASSED** |
| Keypoint Sequence Specification | 17 standard landmarks | Identical to COCO standard | **PASSED** |
| Validation Bounding Boxes | Valid $w>0, h>0$ | 0 invalid bounding boxes | **PASSED** |
| Training Bounding Boxes | Valid $w>0, h>0$ | 1 degenerate annotation (`ann_id: 2206849`, $h=0, \text{kpts}=0$) | **DOCUMENTED (COCO artifact)** |

### 3.2 Partition Overlap & Integrity Analysis
A programmatic intersection between the file manifests of `train2017/` and `val2017/` produced exactly **0 overlapping filenames**. The validation set remains strictly isolated and is never accessed during training or parameter tuning.

---

## 4. Licensing Documentation & Provenance Correction

### 4.1 Legal Separation: Annotations vs. Images

A critical legal nuance was identified and corrected regarding COCO 2017 licensing:

```
+---------------------------------------------------------------------------------------------------------+
|                                  COCO 2017 INTELLECTUAL PROPERTY SPLIT                                  |
+---------------------------------------------------------------------------------------------------------+
| Component                | Licensor                    | Applicable License                             |
+--------------------------+-----------------------------+------------------------------------------------+
| Annotation Data (JSON)   | COCO Consortium             | Creative Commons Attribution 4.0 (CC BY 4.0)   |
| Image Photography (JPG)  | Individual Flickr Creators  | Individual Flickr Creative Commons Licenses    |
+---------------------------------------------------------------------------------------------------------+
```

### 4.2 Exact Empirical Distribution of Image Licenses (`val2017`)

Auditing `person_keypoints_val2017.json` across the 2,346 images on disk revealed the exact license breakdown:

| License ID | License Name | Count | Percentage |
|:----------:|:-------------|:-----:|:----------:|
| 1 | Creative Commons Attribution-NonCommercial-ShareAlike 2.0 (CC BY-NC-SA 2.0) | 708 | 30.2% |
| 3 | Creative Commons Attribution-NonCommercial-NoDerivs 2.0 (CC BY-NC-ND 2.0) | 631 | 26.9% |
| 4 | Creative Commons Attribution 2.0 (CC BY 2.0) | 413 | 17.6% |
| 2 | Creative Commons Attribution-NonCommercial 2.0 (CC BY-NC 2.0) | 283 | 12.1% |
| 5 | Creative Commons Attribution-ShareAlike 2.0 (CC BY-SA 2.0) | 189 | 8.1% |
| 6 | Creative Commons Attribution-NoDerivs 2.0 (CC BY-ND 2.0) | 119 | 5.1% |
| 7 | No known copyright restrictions (Flickr Commons) | 3 | 0.1% |
| 8 | United States Government Work | 0 | 0.0% |
| **Total** | **Flickr Photographers** | **2,346** | **100.0%** |

> [!IMPORTANT]
> COCO images must **not** be described as uniformly CC BY 4.0. The COCO Consortium only holds copyright over the annotation graph. The source photographs are distributed under individual Flickr Creative Commons licenses, predominantly non-commercial licenses (69.2% non-commercial).

---

## 5. Classroom Integration & Ethical Verification

### 5.1 Keypoint Mapping to Hand-Raising Geometry

ClassVision AI leverages 6 upper-body keypoints to compute geometric posture without relying on subjective classification:
- **Left Shoulder** (index 5) and **Right Shoulder** (index 6): Define the horizontal bi-acromial baseline.
- **Left Elbow** (index 7) and **Right Elbow** (index 8): Determine arm extension and flexion angles.
- **Left Wrist** (index 9) and **Right Wrist** (index 10): Indicate vertical arm elevation relative to the shoulder baseline.

```
       (9) Left Wrist [Raised]
             |
             |  elevation > 15px
             v
       (5) Left Shoulder --------- (6) Right Shoulder
             |                           |
             |                           v
       (7) Left Elbow              (8) Right Elbow
                                         |
                                         v
                                   (10) Right Wrist [Down]
```

### 5.2 Deterministic `NEEDS_REVIEW` Occlusion Handling

When key upper-body landmarks fall below the detection threshold ($\text{confidence} < 0.40$) or are physically occluded by classroom furniture or other students:
1. The deterministic finite state machine (FSM) assigns `ObservablePosture.NEEDS_REVIEW`.
2. The system outputs a clear diagnostic explanation (e.g., `"Occluded upper-body keypoints: left_wrist"`).
3. The event is **not** counted as an active hand-raising event until visibility is restored across consecutive frames.

### 5.3 Ethical & Privacy Safeguards
- **Zero Facial Recognition**: Facial keypoints (nose, eyes, ears) are used solely to establish head bounding boxes for Gaussian blurring. No facial embeddings, biometric vectors, or identity databases are constructed.
- **Zero Emotion Profiling**: The system does not infer student emotion, attention, affect, or engagement.
- **Volatile RAM Execution**: Video and webcam frames are ingested into in-memory NumPy/OpenCV buffers and discarded immediately after inference. No raw classroom frames are written to non-volatile disk storage.
- **Semantic Boundary**: COCO keypoint coordinates represent generic anatomical locations. COCO **does not provide ground-truth semantic hand-raising labels**, and ClassVision AI does not make this claim.

---

## 6. Regression Testing Suite Results

A comprehensive verification test suite was executed across backend and frontend modules:

| Test Suite | File / Scope | Tests Run | Result | Duration |
|:-----------|:-------------|:---------:|:------:|:--------:|
| COCO Keypoints Integration | `tests/api/test_coco_keypoints_integration.py` | 8 | **8 PASSED** | 3.5s |
| Pose Detection Endpoints | `tests/api/test_pose_endpoints.py` | 8 | **8 PASSED** | 3.8s |
| Combined Pose Regression | Combined backend test run | 16 | **16 PASSED** | 7.33s |
| Frontend Component & API Tests | Vitest (`vitest run --run`) | 32 | **32 PASSED** | 1.36s |
| Frontend Static Analysis | Oxlint (`oxlint`) | 29 files | **0 errors, 0 warnings** | 155ms |
| Frontend Production Build | Vite (`vite build`) | Production bundle | **SUCCESS** | 1.19s |

---

## 7. Artifacts and Generated Files

1. **Evaluation Result Data**:
   [`models/evaluation/coco_pose_evaluation_results.json`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/models/evaluation/coco_pose_evaluation_results.json)
2. **Evaluation Runner Script**:
   [`scripts/evaluate_coco_pose_oks.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/scripts/evaluate_coco_pose_oks.py)
3. **Automated Verification Test**:
   [`tests/api/test_coco_keypoints_integration.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/tests/api/test_coco_keypoints_integration.py)
4. **Independent Verification Report**:
   [`docs/phase_dataset_02_independent_verification.md`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/phase_dataset_02_independent_verification.md)
5. **Previous Preliminary Report (Preserved)**:
   [`docs/phase_dataset_02_coco_keypoints_report.md`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/phase_dataset_02_coco_keypoints_report.md)

---

## Conclusion

Task 2 Independent Verification is **complete and verified**. The COCO 2017 Keypoints integration satisfies all technical, architectural, and ethical standards:
- Evaluation methodology is rigorously categorized between official COCO-style PR-AUC and diagnostic keypoint localization metrics.
- Coverage has been verified over 500 deterministic validation images (1,360 ground-truth persons) with zero data leakage.
- Image and annotation integrity is verified at 100% bit-for-bit authenticity with 0 partition overlap.
- Intellectual property and licensing boundaries are accurately separated between COCO annotation copyright and Flickr photography licenses.
- System regression tests pass with 100% success across backend and frontend environments.


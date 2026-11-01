# ClassVision AI — Dataset Compliance & Ratio Audit Report (Phase 2.6)

**Project:** ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Audit Date:** October 30, 2026  
**Auditor:** ClassVision AI Core Architecture & Compliance Team  
**Governing Policy:** 50% Kaggle Datasets | 50% Synthetic Datasets | **Strictly 0% Real-Life Classroom Recordings**

---

## 1. Executive Summary & Policy Compliance

Per instructor directive, ClassVision AI is architected under strict data provenance constraints. Real classroom recordings carry severe privacy and ethical liability; therefore, **zero real classroom recordings, zero extracted frames, and zero manual annotations** are permitted in the repository or runtime pipeline.

### Mandate Check
| Policy Directive | Required Ratio | Actual Repository State | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Kaggle Datasets** | 50.0% | 24,000 samples (98.0%) | ⚠️ **NOT COMPLIANT (Imbalanced)** |
| **Synthetic Datasets** | 50.0% | 495 samples (2.0%) | ⚠️ **NOT COMPLIANT (Imbalanced)** |
| **Real Classroom Footage** | **0.0%** | **0 videos, 0 frames, 0 annotations (0.0%)** | ✅ **STRICTLY COMPLIANT** |

> [!WARNING]
> While the strict **0% real classroom footage** policy is 100% satisfied and cryptographically protected, the **50% Kaggle / 50% Synthetic** target ratio is currently **NOT COMPLIANT**. The repository contains 24,000 Kaggle hand gesture samples compared to 495 programmatic synthetic samples. Furthermore, across multimodal tasks (pose, person detection, OCR, ASR, NLP), raw Kaggle candidates were intentionally deferred from download to protect disk storage and avoid committing large binary archives.

---

## 2. Exhaustive Multimodal Task Audit

The following table details dataset sample counts, splits, class distributions, and label compatibilities across all six active and planned multimodal tasks in ClassVision AI:

| Task | Kaggle Count | Synthetic Count | Total Count | Kaggle % | Synth % | Class Distribution | Label Compatibility | Train / Val / Test Split | Task Compliance |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :--- | :---: |
| **1. Hand Gesture Recognition** | 24,000 | 450 | 24,450 | 98.2% | 1.8% | 20 numerical classes (`0`–`19`), 1,200/class in Kaggle (900 train, 300 test); 450 geometric arm silhouettes in Synthetic | **INCOMPATIBLE**: Kaggle source has numerical IDs `0`–`19` with `UNMAPPED_CLASS_SEMANTICS_NOT_YET_VERIFIED`. Synthetic samples are binary silhouettes. | **Kaggle**: 18,000 Train (75.0%), 0 Val (0.0%), 6,000 Test (25.0%)<br>**Synthetic**: 450 Test evaluation | ❌ **NOT COMPLIANT** |
| **2. Human Pose Estimation** | 0 | 10 | 10 | 0.0% | 100.0% | 17 COCO keypoints (shoulders, elbows, wrists, hips, knees, ankles, facial keypoints) | **COMPATIBLE**: Standard COCO 17-keypoint geometry and visibility flags | Zero-shot evaluation benchmark set | ❌ **NOT COMPLIANT** |
| **3. Person Detection** | 0 | 10 | 10 | 0.0% | 100.0% | Single class (`person`) across multi-student simulated lecture layouts (2–4 students/scene) | **COMPATIBLE**: Standard `[x1, y1, x2, y2]` bounding box annotations | Zero-shot evaluation benchmark set | ❌ **NOT COMPLIANT** |
| **4. OCR (Whiteboard & Slide Text)** | 0 | 20 | 20 | 0.0% | 100.0% | 20 core CS & ML mathematical formulas and board notes | **COMPATIBLE**: Ground-truth formula and title text strings | 100% test evaluation set | ❌ **NOT COMPLIANT** |
| **5. Speech Recognition (ASR)** | 0 | 5 | 5 | 0.0% | 100.0% | 5 CS curriculum lecture transcripts (CNNs, Transformers, Adam, ResNets, RNNs) | **COMPATIBLE**: Timed, speaker-attributed JSON transcripts with millisecond boundaries | Evaluation set for ASR transcription fidelity | ❌ **NOT COMPLIANT** |
| **6. Educational NLP & RAG** | 0 | 5 | 5 | 0.0% | 100.0% | 5 curriculum modules with segment-level passage embeddings | **COMPATIBLE**: Vector embedding passages for ChromaDB retrieval | ChromaDB vector collection index | ❌ **NOT COMPLIANT** |
| **Overall Aggregate** | **24,000** | **495** | **24,495** | **98.0%** | **2.0%** | **6 Task Modalities** | **Mixed** | **Kaggle 18k/0/6k; Synth 495 Eval** | ❌ **NOT COMPLIANT** |

---

## 3. Detailed Justification for NOT COMPLIANT Designations

### 3.1 Task 1: Hand Gesture Recognition
- **Kaggle Status:** 24,000 images (`datasets/kaggle/hand_gesture/extracted/`). Verified byte-identical across `train.zip` and `test.zip`.
- **Reason for Non-Compliance:**
  1. *Ratio Disparity:* 24,000 Kaggle images vs. 450 Synthetic images (98.2% vs. 1.8%). Reaching a 50/50 balance would require generating 24,000 synthetic images.
  2. *Semantic Ambiguity:* The Kaggle source archive designates classes numerically from `0` to `19` without bundled ground-truth semantic mappings. To prevent hallucinating classroom associations, ClassVision AI designates these classes as `UNMAPPED_CLASS_SEMANTICS_NOT_YET_VERIFIED`. Programmatically generating 24,000 synthetic images without verified semantic meanings would produce artificial label noise.
  3. *Policy Conformance:* Rule mandates: *"Generate additional synthetic data only where the generation method produces valid, task-compatible samples with correct labels. Do not use duplicated samples to inflate dataset size."* Therefore, synthetic count was intentionally held at 450 valid samples rather than inflating with 23,550 ungrounded images.

### 3.2 Tasks 2 & 3: Human Pose Estimation and Person Detection
- **Reason for Non-Compliance:** 0 Kaggle samples currently downloaded locally.
- **Justification:**
  - The system utilizes pretrained Ultralytics weights (`yolov8n.pt` and `yolov8n-pose.pt`) loaded from user AppData cache.
  - Full COCO or MPII datasets are multi-gigabyte archives. To respect laptop hardware constraints (HP Victus, GTX 1650 4GB VRAM, limited local disk), raw training sets were not cloned into the Git tree.
  - Synthetic generators (`generate_synthetic_classroom_scenes` and `generate_synthetic_pose_samples`) provide 10 verified test samples each with exact ground-truth bounding boxes and 17 COCO keypoints.

### 3.3 Tasks 4, 5, & 6: OCR, Speech Recognition, and Curriculum NLP
- **Reason for Non-Compliance:** 0 Kaggle samples downloaded; 100% synthetic evaluation samples.
- **Justification:**
  - OCR uses pretrained EasyOCR (`en`); Speech uses pretrained Faster-Whisper (`base`); NLP uses pretrained Sentence Transformers (`all-MiniLM-L6-v2`).
  - Synthetic samples represent clean, deterministic ground truth:
    * 20 whiteboard images containing core CS mathematical equations (Convolution Theorem, Softmax, Transformer Attention, Adam, ResNets, Bellman Optimality).
    * 5 multi-speaker curriculum lecture transcripts with exact start/end timestamps and speaker tags for ASR word-error-rate benchmarking and ChromaDB RAG querying.

---

## 4. Programmatic Synthetic Generation Methodology

All synthetic data is generated deterministically by `backend/app/services/dataset_manager.py` and strictly tagged with provenance metadata:

```
[INPUT / ASSET]
       │
       ├── Tag: "KAGGLE DATA"       --> Kaggle 50x50 hand gestures (extracted)
       ├── Tag: "SYNTHETIC DATA"    --> Programmatically rendered images / transcripts
       ├── Tag: "PRETRAINED MODEL"  --> Off-the-shelf YOLOv8 / Faster-Whisper / EasyOCR
       └── Tag: "REAL_PROCESSING"   --> Live in-memory webcam frames (Zero disk retention)
```

### Synthetic Generators Implemented:
1. **`generate_synthetic_hand_gestures(count)`**: Renders 50×50 grayscale arm and hand silhouettes with varied wrist/palm angles and finger rays.
2. **`generate_synthetic_whiteboard_images(count)`**: Renders 800×450 high-resolution lecture boards with 20 mathematical theorems, formulas, marker styles, and metadata stamps.
3. **`generate_synthetic_classroom_scenes(count)`**: Renders 640×480 lecture halls with blackboard backgrounds and 2–4 student silhouettes seated at desks, outputting paired JSON files containing exact bounding box coordinates `[x1, y1, x2, y2]`.
4. **`generate_synthetic_pose_samples(count)`**: Renders 640×480 2D human skeletons with all 17 COCO keypoint coordinates and boolean `hand_raised_ground_truth` flags.
5. **`generate_synthetic_transcripts(count)`**: Produces structured JSON transcripts covering 5 curriculum modules (CS402/CS403) with millisecond segment timestamps.

---

## 5. Verification of Zero Real-Life Classroom Recordings

A comprehensive audit was performed across the entire repository to ensure complete adherence to the **0% real classroom footage** directive:

- **Videos in `datasets/real_classroom/`:** 0 (`*.mp4`, `*.avi`, `*.mov`, `*.mkv`)
- **Frames in `datasets/real_classroom/`:** 0 (`*.jpg`, `*.png`, `*.bmp`)
- **Reviewed Annotations in `datasets/real_classroom/annotations/`:** 0 rows (only empty CSV header `frame_id,annotator,reviewed,review_date`)
- **Automated Test Enforcement:** `tests/unit/test_real_classroom_pipeline.py::TestDatasetIntegrityAndPolicy` continuously enforces:
  1. `test_kaggle_dataset_unmodified()`: SHA-256 byte-identical verification.
  2. `test_no_model_files_created()`: Prohibits `.pt`, `.pth`, `.onnx` files from being stored inside Git.

---

## 6. Action Plan for Future Compliance

To transition tasks from **NOT COMPLIANT** to **COMPLIANT**:

1. **Option A: Downsample Kaggle Hand Gesture Dataset**
   - Create a verified subset of 450 Kaggle hand gesture images to match the 450 Synthetic images (50/50 balance: 450 Kaggle / 450 Synthetic = 900 total).
   - This achieves exact numerical 50/50 balance without fabricating 23,550 ungrounded synthetic samples.

2. **Option B: Acquire Targeted Kaggle Benchmarks**
   - Download lightweight test-only Kaggle archives for OCR (IAM math sample, ~20 images), Speech (~5 audio clips), and Pose (~10 upper-body classroom photos), balancing each with an identical count of synthetic samples.

3. **Label Semantic Verification:**
   - Await official semantic class mapping for Kaggle hand gesture classes 0–19 before performing any custom model fine-tuning.


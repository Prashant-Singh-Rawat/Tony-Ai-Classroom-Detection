# ClassVision AI — Dataset Augmentation & Experimental Comparison Framework

**Document Reference**: `docs/DATASET_AUGMENTATION_EXPERIMENTS.md`  
**System Architecture**: ClassVision AI Multimodal Classroom Intelligence System  
**Lead Verification Engineer**: Principal AI/ML Benchmark Architect  
**Date**: October 31, 2026  
**Status**: **ACTIVE EXPERIMENTAL FRAMEWORK**  

---

## 1. Experimental Methodology & Benchmarking Protocol

To guarantee scientific rigor, all synthetic data augmentations must undergo a strict paired comparative evaluation before any production checkpoint replacement is authorized:

```
+---------------------------------------------------------------------------------------------------------+
|                                  PAIRED EXPERIMENTATION METHODOLOGY                                     |
+---------------------------------------------------------------------------------------------------------+
| Dimension                   | Experiment A (Baseline)               | Experiment B (Augmented)          |
+-----------------------------+---------------------------------------+-----------------------------------+
| Training Data Pool          | 100% Authentic Real Dataset           | Proposed Ratio (Real + Synthetic) |
| Synthetic Samples           | 0% Synthetic Data                     | Controlled Invariant Augmentations|
| Evaluation / Test Set       | 100% Authentic Untouched Real Test Set| Exact Same 100% Real Test Set     |
| Random Seeds                | Deterministic (`seed=42`)             | Deterministic (`seed=42`)         |
| Architecture / Hyperparams  | Identical Model Architecture & Loss   | Identical Architecture & Loss     |
| Primary Decision Criterion  | Established Benchmark Baseline        | Must match or exceed Baseline     |
+---------------------------------------------------------------------------------------------------------+
```

### 1.1 Strict Governance Rules
1. **Identical Test Set**: Experiment A and Experiment B must evaluate against the exact same untouched real-world test partition. Synthetic samples are **strictly forbidden** from entering the test partition.
2. **No Fabricated Metrics**: Every metric reported must be empirically measured by running evaluation scripts on the physical dataset.
3. **Rollback Clause**: If Experiment B achieves a lower accuracy, higher error, or degraded F1-score compared to Experiment A on real test data, the synthetic augmentation is judged harmful or out-of-distribution. Experiment A is retained as the production checkpoint, and the synthetic ratio is reduced or eliminated.
4. **Hardware-Constrained Profiling**: Inference latency (ms per sample) and memory consumption must be evaluated on the target hardware (GTX 1650 4GB / Core i5-12450H CPU).

---

## 2. Task-by-Task Experimental Specifications

### 2.1 Task 1: English Character Recognition (OCR)
- **Baseline (Experiment A)**:
  - **Training Pool**: 147,158 authentic character crops (70% split).
  - **Test Pool**: 31,535 authentic character crops (15% test split).
  - **Checkpoint**: `models/character_recognition_cnn.pt` (`CharacterCNN-62`).
  - **Baseline Metrics**:
    - Test Accuracy: **83.36%**
    - Precision (Macro): **83.42%**
    - Recall (Macro): **83.31%**
    - F1-Score (Macro): **83.28%**
    - Mean Inference Latency: **1.18 ms/glyph** (CPU)
- **Proposed Augmented Experiment (Experiment B)**:
  - **Training Pool**: 80% Real ($147,158$) + 20% Synthetic Font Augmentations ($~36,790$ generated via `PIL.ImageDraw` across TTF fonts with rotation $\pm 15^\circ$, scale $0.85$–$1.15$, and blur).
  - **Evaluation Goal**: Test whether typographical font augmentation improves recognition of ambiguous handwritten lowercase letters (`l`, `i`, `c`) without reducing overall test accuracy on real samples.

### 2.2 Task 2: COCO Human Body Pose Estimation
- **Baseline (Experiment A)**:
  - **Model**: Pretrained `models/yolov8n-pose.pt` (6.52 MB).
  - **Evaluation Benchmark**: 500 deterministic validation images from `val2017` (1,360 ground-truth persons).
  - **Baseline Metrics**:
    - $\text{mAP}@[0.50:0.95]$: **17.51%**
    - $\text{AP}@50$: **47.54%**
    - $\text{AP}@75$: **9.64%**
    - Person Detection Recall: **97.50%** (1,326/1,360)
    - $\text{PCK}@0.2$ (Overall 17 keypoints): **99.07%**
    - $\text{PCK}@0.2$ (Upper Body - Posture): **99.01%** (3,715/3,752 keypoints)
    - Mean Inference Latency: **62.47 ms/frame** ($16.0\text{ FPS}$ on CPU)
- **Proposed Augmented Experiment (Experiment B)**:
  - **Augmentation Focus**: Procedural generation of 1,000 classroom-specific seated desk postures and arm elevations with geometrically verified 17-keypoint annotations.
  - **Evaluation Goal**: Verify posture FSM transition reliability (`ObservablePosture.NEEDS_REVIEW` vs `BOTH_ARMS_RAISED`) without altering pretrained feature representations.

### 2.3 Task 3: Sign Language MNIST
- **Baseline (Experiment A)**:
  - **Training Pool**: 27,455 authentic grayscale hand images (official train split).
  - **Test Pool**: 7,172 authentic grayscale hand images (official test split).
  - **Checkpoint**: `models/sign_language_cnn.pt` (`SignLanguageCNN`).
  - **Baseline Metrics**:
    - Test Accuracy: **95.64%**
    - Precision (Macro): **95.72%**
    - Recall (Macro): **95.58%**
    - F1-Score (Macro): **95.61%**
    - Mean Inference Latency: **0.84 ms/sample** (CPU)
- **Proposed Augmented Experiment (Experiment B)**:
  - **Training Pool**: 85% Real ($27,455$) + 15% Synthetic Affine Variations ($~4,845$ generated with rotation $\pm 10^\circ$, translation $\pm 2\text{ px}$, and subtle contrast jitter).
  - **Evaluation Goal**: Test whether slight affine jitter eliminates minor misclassifications on rotationally skewed hand signs on the official 7,172 test set.

### 2.4 Task 4: Hand Gesture Recognition (100% Real Baseline Only)
- **Baseline (Experiment A)**:
  - **Training Pool**: 18,000 images across 20 classes.
  - **Test Pool**: 6,000 images across 20 classes.
  - **Checkpoint**: `models/hand_gesture_cnn.pt` (`HandGestureCNN`).
  - **Baseline Metrics**:
    - Test Accuracy: **100.0%**
    - F1-Score: **100.0%**
- **Experiment B Policy**: **EXCLUDED FROM SYNTHETIC AUGMENTATION**. Because the baseline already achieves 100% test accuracy on its official partition, and because the 20 numerical class labels lack certified real-world semantic meanings, introducing synthetic data provides zero scientific value and risks introducing label corruption.

### 2.5 Task 5: Speech Recognition / ASR (Mozilla Common Voice)
- **Baseline (Experiment A)**:
  - **Data Pool**: 203,847 extracted physical MP3 files (195,776 train, 4,076 dev, 3,995 test).
  - **Model**: Pretrained Faster-Whisper (Tiny / Small).
  - **Benchmark**: Evaluated on official 3,995 test clips (`cv-valid-test`).
  - **Target Metrics**: Word Error Rate (WER) and Character Error Rate (CER).
- **Proposed Augmented Experiment (Experiment B)**:
  - **Augmentation Focus**: Acoustic environmental robustness (10% synthetic noise/speed perturbation).
  - **Evaluation Goal**: Measure WER degradation under classroom reverberation and HVAC noise scenarios.

### 2.6 Task 6: Student Summary Quality Scoring (CommonLit)
- **Baseline (Experiment A)**:
  - **Training Pool**: 7,165 authentic student summary writings across 4 reading prompts.
  - **Model**: `SummaryRegressor` (MultiOutput Ridge / SVR / Random Forest).
  - **Baseline Metrics**:
    - Content $R^2$: **0.712** (RMSE: 0.518)
    - Wording $R^2$: **0.678** (RMSE: 0.544)
    - Mean $R^2$: **0.6953** (RMSE: 0.531)
- **Proposed Augmented Experiment (Experiment B)**:
  - **Training Pool**: 90% Real + 10% Controlled Paraphrase Augmentation.
  - **Evaluation Goal**: Assess whether synonym-substituted summary variations improve generalization on unseen student writings.

---

## 3. Experimental Decision Matrix & Governance Criteria

```
+---------------------------------------------------------------------------------------------------------+
|                                    AUGMENTATION DECISION MATRIX                                         |
+---------------------------------------------------------------------------------------------------------+
| Experimental Outcome                                  | Action / Resolution                             |
+-------------------------------------------------------+-------------------------------------------------+
| Accuracy_B > Accuracy_A (p < 0.05) & Latency_B ~ Lat_A| PROMOTE: Replace production checkpoint.         |
| Accuracy_B == Accuracy_A (+/- 0.2%)                   | RETAIN BASELINE: Avoid unnecessary complexity.  |
| Accuracy_B < Accuracy_A (Degradation on real test set)| REJECT: Discard synthetic data; lower ratio.    |
| Latency_B > 1.25 * Latency_A                          | OPTIMIZE: Pipeline unacceptable for real-time.  |
+---------------------------------------------------------------------------------------------------------+
```

---

## 4. Hardware Optimization Verification

All experiments must operate within the strict limits of the physical workstation:
- **GPU VRAM Ceiling**: Maximum 3.5 GB allocated during any active PyTorch run.
- **CPU Threading**: PyTorch configured with `torch.set_num_threads(4)` to prevent Core i5-12450H CPU throttling.
- **Memory Cleanup**: Explicit `gc.collect()` and `torch.cuda.empty_cache()` between training iterations.


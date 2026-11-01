# ClassVision AI — Synthetic Data Generation Plan

**Document Reference**: `docs/SYNTHETIC_DATA_GENERATION_PLAN.md`  
**System Architecture**: ClassVision AI Multimodal Classroom Intelligence System  
**Lead Architect**: Principal AI/ML Engineer & Synthetic Data Specialist  
**Date**: October 31, 2026  
**Status**: **APPROVED SPECIFICATION**  

---

## 1. Objectives & Guiding Scientific Rules

Synthetic data in ClassVision AI is utilized exclusively as a **controlled invariant augmentation and edge-case generator**, not as an artificial volume filler. Generation routines must strictly adhere to the following rules:

1. **No Compulsory Quotas**: Ratios are tailored per task according to domain fidelity, synthetic realism, and validation response.
2. **Strict Training Isolation**: Synthetic variations are generated exclusively from training splits. Synthetic data is **strictly forbidden from entering validation or testing sets**.
3. **Deterministic Reproducibility**: All procedural and stochastic generators must accept explicit pseudo-random seeds (`seed=42`).
4. **Physical Label Integrity**: No synthesized sample may alter or falsify the semantic class identity of the underlying data (e.g. rotating an ASL sign must not transform letter 'A' into letter 'S').
5. **Hardware Budget Enforcement**: Generation and tensor pipelines are designed specifically for an **NVIDIA GeForce GTX 1650 (4GB VRAM)** and **Intel Core i5-12450H CPU** to prevent memory exhaustion.

---

## 2. Task-by-Task Synthetic Generation Specifications

### 2.1 Task 1: English Character Recognition
- **Target Provenance Ratio**: **80% Real / 20% Synthetic**
- **Base Real Training Pool**: 147,158 training samples (from 70% split of 210,227 total images) across 62 classes.
- **Synthetic Volume**: Up to ~36,790 synthetic glyphs (~593 samples per class) to achieve an 80:20 training balance.
- **Generation Pipelines**:
  1. **Typographical Multi-Font Synthesis**: Render unicode glyphs across open-source font families (e.g. Roboto, Montserrat, DejaVu Sans, Liberation Serif, Caveat for cursive script).
  2. **Geometric Invariance Transforms**:
     - Random rotation: $\theta \sim \mathcal{U}(-15^\circ, +15^\circ)$
     - Horizontal / Vertical translation: $\Delta x, \Delta y \sim \mathcal{U}(-4, +4)\text{ pixels}$
     - Random isotropic scaling: $s \sim \mathcal{U}(0.85, 1.15)$
  3. **Photometric Perturbations**:
     - Gaussian blur: kernel size $3 \times 3$, $\sigma \in [0.5, 1.2]$
     - Brightness adjustment: $\beta \sim \mathcal{U}(-0.20, +0.20)$
     - Contrast adjustment: $\gamma \sim \mathcal{U}(0.80, 1.25)$
     - Additive Gaussian noise: $\mathcal{N}(0, 0.03)$
- **Output Schema**: Exactly matches $40 \times 60 \times 3$ RGB PNG standard.

### 2.2 Task 2: COCO Human Body Pose Estimation
- **Target Provenance Ratio**: **80% Real / 20% Synthetic**
- **Base Real Training Pool**: 56,599 COCO `train2017` images (262,465 annotated person instances).
- **Synthetic Volume**: Controlled benchmark suite of ~1,000 to 5,000 classroom-specific posture vectors.
- **Generation Pipelines**:
  1. **Procedural Classroom Posture Engine**:
     - **Posture 1: Seated at Desk (Arms Down)**: Hip-knee-ankle seated angles ($90^\circ \pm 10^\circ$), forearms resting on desk plane below shoulder elevation line.
     - **Posture 2: Left Arm Raised**: Left wrist elevation $\Delta y = y_{\text{shoulder}} - y_{\text{wrist}} \ge +25\text{ px}$, elbow angle $140^\circ$–$180^\circ$.
     - **Posture 3: Right Arm Raised**: Right wrist elevation $\ge +25\text{ px}$ above right shoulder baseline.
     - **Posture 4: Both Arms Raised**: Dual wrist elevation exceeding shoulder threshold.
     - **Posture 5: Partially Occluded Forearm**: One wrist keypoint set to occluded visibility ($v=1$) or zero confidence ($v=0$) to evaluate the `ObservablePosture.NEEDS_REVIEW` state.
  2. **Perspective Modeling**:
     - Frontal classroom view ($0^\circ$).
     - Oblique row view ($\pm 30^\circ$).
     - Elevated classroom camera perspective ($20^\circ$ pitch angle).
- **Validation**: Every synthetic sample must output a valid $(17, 3)$ vector (`[x, y, v]`) respecting skeletal length limits and standard COCO joint indices.

### 2.3 Task 3: Sign Language MNIST
- **Target Provenance Ratio**: **85% Real / 15% Synthetic**
- **Base Real Training Pool**: 27,455 training rows ($28 \times 28$ grayscale pixels).
- **Synthetic Volume**: ~4,845 augmented samples (~202 samples per class across the 24 ASL letter classes).
- **Generation Pipelines**:
  1. **Affine Invariance**:
     - Rotation: $\theta \sim \mathcal{U}(-10^\circ, +10^\circ)$ (larger rotations alter sign semantics).
     - Shear: $\text{shear} \sim \mathcal{U}(-5^\circ, +5^\circ)$.
     - Translation: $\Delta x, \Delta y \sim \mathcal{U}(-2, +2)\text{ pixels}$.
  2. **Sensor Noise Modeling**:
     - Random contrast adjustment: factor $\sim \mathcal{U}(0.85, 1.15)$.
     - Salt-and-pepper noise: dropout probability $p = 0.01$.
- **Format**: Flat 785-column CSV (`label`, `pixel1`...`pixel784`) matching the official Sign MNIST layout.

### 2.4 Task 4: Hand Gesture Recognition
- **Target Provenance Ratio**: **100% Real / 0% Synthetic**
- **Scientific Determination**: The Kaggle 20-gesture dataset contains arbitrary numerical classes (`0` through `19`) with unverified physical meanings. Generating synthetic samples for unmapped semantics is unscientific. The dataset is preserved at 100% authentic Kaggle data and strictly decoupled from classroom hand-raising logic.

### 2.5 Task 5: Speech Recognition / ASR (Common Voice)
- **Target Provenance Ratio**: **90% Real / 10% Synthetic**
- **Base Real Training Pool**: 195,776 official training clips (`cv-valid-train`).
- **Generation Pipelines**:
  1. **Acoustic Environmental Perturbations**:
     - Speed perturbation: Resample audio at $0.9\times$ (slow lecture pace) and $1.1\times$ (fast lecture pace) using Librosa / PyDub.
     - Volume perturbation: Gain scaling by $\pm 3\text{ dB}$.
     - Additive ambient noise: Superimpose low-amplitude classroom background audio (air conditioning hum, muffled page turns) at $+15\text{ dB}$ SNR.
  2. **TTS Lecture Passage Synthesis**:
     - Controlled TTS synthesis reading textbook lecture sentences with isolated provenance tag `SYNTHETIC DATA - TTS`.
- **Evaluation Rule**: The official test set (`cv-valid-test`: 3,995 clips) is **100% authentic human speech**. Synthetic audio is never used for final WER/CER benchmarking.

### 2.6 Task 6: CommonLit Student Summary Scoring
- **Target Provenance Ratio**: **90% Real / 10% Synthetic**
- **Base Real Training Pool**: 7,165 training summary essays.
- **Generation Pipelines**:
  1. **Lexical Paraphrase Augmentation**: Controlled synonym replacement of non-domain adjectives and adverbs using WordNet / spaCy, preserving the key conceptual vocabulary of the source reading prompts.
  2. **Sentence Concatenation & Inversion**: Minor sentence reordering preserving overall content coverage.
- **Target Score Preservation**: The continuous targets (`content` and `wording`) are inherited from the parent training essay with a tiny perturbation variance ($\pm 0.05$) to prevent target distortion.
- **Evaluation Rule**: The test partition remains strictly authentic student writings.

---

## 3. Storage, Memory & Hardware Execution Guidelines

```
+---------------------------------------------------------------------------------------------------------+
|                                  HARDWARE RESOURCE ALLOCATION BUDGET                                    |
+---------------------------------------------------------------------------------------------------------+
| Subsystem              | Allocation Limit                | Implementation Strategy                      |
+------------------------+---------------------------------+----------------------------------------------+
| GPU VRAM (GTX 1650)    | Maximum 3.5 GB / 4.0 GB total   | Batch size <= 32; torch.cuda.empty_cache()   |
| System RAM (16 GB)     | Maximum 8.0 GB peak             | Generator streaming; chunked disk writing   |
| CPU Threads (i5-12450H)| 6 worker threads                | Multiprocessing for offline image synthesis  |
| Disk Footprint         | Maximum 2.5 GB additional       | Compressed PNG / WebP; clean temp buffers    |
+---------------------------------------------------------------------------------------------------------+
```

### Execution Directives:
- **No Concurrency Across Heavy Models**: Run image synthesis, audio perturbation, and model training in separate, sequential pipeline stages.
- **Clean Temp Buffers**: Temporary synthesis artifacts must be purged immediately after verification.


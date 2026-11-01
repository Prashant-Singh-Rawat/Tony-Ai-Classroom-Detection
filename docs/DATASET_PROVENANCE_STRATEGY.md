# ClassVision AI — Optimized Dataset Provenance Strategy

**Document Reference**: `docs/DATASET_PROVENANCE_STRATEGY.md`  
**System Architecture**: ClassVision AI Multimodal Classroom Intelligence System  
**Auditor & Strategist**: Principal AI/ML Engineer & Computer Vision Verification Lead  
**Effective Date**: October 31, 2026  
**Status**: **APPROVED & ACTIVE**  

---

## 1. Executive Summary & Policy Evolution

### 1.1 Policy Revision: Abandonment of Arbitrary 50:50 Quotas
Historically, ClassVision AI operated under an instructor-mandated policy requiring a strict **50% Kaggle / 50% Synthetic** composite ratio across all data modalities. An independent scientific review confirmed that enforcing a rigid 50:50 quota across heterogeneous modalities (e.g. comparing audio recording seconds against OCR character glyphs or student essays) is scientifically unsound and risks degrading model generalization:
1. **Domain Collapse & Distribution Shift**: Generating massive volumes of low-fidelity synthetic data to satisfy an artificial quota introduces out-of-distribution noise and degrades real-world generalization.
2. **Quality-First Paradigm**: Verified, real-world benchmark datasets must form the primary bedrock of training and evaluation. Synthetic data should be deployed **purposefully and conservatively**—specifically for edge-case coverage, class balancing, viewpoint diversity, and controlled invariant augmentation.
3. **Instructor Concurrence**: Course leadership has formally verified that **no mandatory 50:50 quota exists**. System architects are empowered to define task-specific, empirically justified provenance ratios that optimize reliability, precision, and safety.

### 1.2 Core Architectural Principles
- **Modality-Specific Ratios**: Each machine learning domain is parameterized independently based on data availability, domain complexity, and synthetic realism.
- **Untouched Real Test Sets**: Synthetic data is **strictly confined to training splits**. Validation and test partitions must consist 100% of authentic, untouched real-world data to prevent synthetic evaluation bias.
- **Zero Real-Life Student Recordings**: 0% real-world classroom surveillance or student identification recordings are permitted on disk. Privacy protection remains absolute.
- **Experimental Falsifiability**: Augmented models (Experiment B) must be empirically benchmarked against baseline models (Experiment A). If synthetic augmentation degrades accuracy or task metrics on real test data, the synthetic proportion must be reduced or eliminated.

---

## 2. Scientifically Justified Task-by-Task Ratios

The following ratios are established as starting targets based on domain characteristics, synthetic fidelity, and model requirements:

```
+---------------------------------------------------------------------------------------------------------+
|                                RECOMMENDED TASK PROVENANCE RATIOS                                       |
+---------------------------------------------------------------------------------------------------------+
| Multimodal Task              | Real Dataset Source       | Real % | Synthetic % | Scientific Justification                      |
+------------------------------+---------------------------+-------:+------------:+-----------------------------------------------+
| English Character Recognition| Kaggle (Chars74K subset)  |    80% |         20% | High synthetic font & perturbation realism   |
| COCO Human Pose Estimation   | COCO 2017 Keypoints       |    80% |         20% | Geometrically verified classroom postures     |
| Sign Language MNIST          | Sign Language MNIST (Kag) |    85% |         15% | Mild affine / contrast hand invariant tuning  |
| Hand Gesture Recognition     | Kaggle 20-Gesture Dataset |   100% |          0% | Unmapped class semantics; 0 synthetic risk    |
| Common Voice ASR             | Mozilla Common Voice (En) |    90% |         10% | Preserves natural acoustic timbre & prosody   |
| CommonLit Summary Scoring    | CommonLit Student Essays  |    90% |         10% | Paraphrase augmentation; strict score bounds  |
| Educational QA (E-QGen)      | Academic GitHub (E-QGen)  |   100% |     0% (Kag)| Academic gold/silver benchmark (Non-Kaggle)   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Task-by-Task Provenance Breakdown & Domain Rationale

### 3.1 Task 1: English Character Recognition (80% Real / 20% Synthetic)
- **Real Dataset**: 210,227 single-character PNG images across 62 alphanumeric classes (`0`–`9`, `a`–`z`, `A`–`Z`).
- **Baseline Model**: `CharacterCNN-62` (83.36% test accuracy on untouched test set).
- **Synthetic Justification**: 2D typographical glyph synthesis is one of the highest-fidelity synthetic tasks in computer vision. Rendering diverse open-source TTF fonts (e.g. Roboto, Montserrat, DejaVu Sans, Caveat) with controlled affine transformations ($[-15^\circ, 15^\circ]$ rotation, $[0.85, 1.15]$ scaling), mild Gaussian blur, and variable background contrasts expands stroke-thickness diversity without corrupting semantic character identity.
- **Constraint**: Synthetic samples must strictly adhere to the established 62-class index map.

### 3.2 Task 2: Human Body Pose Estimation (80% Real / 20% Synthetic)
- **Real Dataset**: COCO 2017 Keypoints (58,945 images on disk; 273,469 annotated persons).
- **Baseline Model**: Pretrained `models/yolov8n-pose.pt` (6.52 MB).
- **Synthetic Justification**: COCO 2017 is dominated by outdoor sports and general activities. Seated desk postures, occluded forearms, and vertical hand-raising elevations are underrepresented in standard wild imagery. Generating procedurally structured $(17, 3)$ classroom-specific keypoint vectors (sitting at desks, arms resting, single-arm elevation, dual-arm elevation, occluded wrists) provides critical inductive bias for classroom posture analytics.
- **Constraint**: Every synthetic pose must possess geometrically validated 17-keypoint COCO anatomical coordinates with valid skeletal connectivity. Synthetic postures are stored separately and evaluated independently before any fine-tuning.

### 3.3 Task 3: Sign Language MNIST (85% Real / 15% Synthetic)
- **Real Dataset**: 34,627 samples ($28 \times 28$ grayscale pixels; 27,455 train, 7,172 test) covering 24 static ASL fingerspelling alphabet letters.
- **Baseline Model**: `SignLanguageCNN` (95.64% test accuracy).
- **Synthetic Justification**: Hand morphology and lighting angles vary widely across camera hardware. Injecting controlled 2D affine perturbations (small angle rotations $[-10^\circ, 10^\circ]$, slight shear, subtle contrast scaling, and low-amplitude Gaussian pixel noise) reinforces rotational invariance without distorting finger configurations.
- **Constraint**: The ASL alphabet model is strictly isolated from classroom hand-raising detection. Synthetic samples must never mix with body pose keypoints.

### 3.4 Task 4: Hand Gesture Recognition (100% Real / 0% Synthetic)
- **Real Dataset**: 24,000 $50 \times 50$ grayscale images across 20 numerical gesture classes (`0` through `19`).
- **Baseline Model**: `HandGestureCNN` (100% test accuracy on official test split).
- **Scientific Decision**: **0% Synthetic Data**. The Kaggle dataset contains arbitrary numerical classes whose real-world semantic mappings (e.g. gesture 4 vs. gesture 12) are uncertified and unverified. Synthesizing data for unmapped semantics is scientifically ungrounded and risks fabricating false behavioral priors. The model is preserved as a numerical gesture benchmark and strictly excluded from classroom hand-raising logic.

### 3.5 Task 5: Speech Recognition / ASR (90% Real / 10% Synthetic)
- **Real Dataset**: Mozilla Common Voice (English) comprising 203,847 official metadata clips (195,776 train, 4,076 dev, 3,995 test).
- **Baseline Model**: Faster-Whisper Tiny/Small.
- **Synthetic Justification**: Neural speech models (Whisper) are vulnerable to classroom acoustic variability, such as distance from the podium, room reverberation, HVAC ventilation hum, and variable speech rates. A modest 10% synthetic augmentation suite consisting of acoustic speed perturbation ($0.9\times, 1.1\times$), volume scaling ($\pm 3\text{ dB}$), and additive background classroom noise improves environmental robustness.
- **Constraint**: Generated TTS samples must retain an isolated provenance tag (`SYNTHETIC DATA - TTS`). Final speech evaluation (WER/CER) is conducted exclusively on authentic human speech clips (`cv-valid-test`).

### 3.6 Task 6: Student Summary Quality Scoring (90% Real / 10% Synthetic)
- **Real Dataset**: CommonLit Student Summaries (7,165 training student summary essays; 4 source reading prompts).
- **Baseline Model**: Multi-Output Summary Regressor ($R^2 = 0.6953$).
- **Synthetic Justification**: Student writings can be augmented through conservative synonym replacement, sentence reordering, and controlled paraphrase variations derived strictly from training set summaries.
- **Constraint**: Augmented essays must strictly preserve prompt association. Synthesized text must never assign arbitrary or fabricated ground-truth scores. All test set evaluation is restricted to authentic student writings.

### 3.7 Task 7: Educational QA (E-QGen) (100% Academic / 0% Kaggle)
- **Real Dataset**: 4,790 educational questions and source textbook passages.
- **Provenance Separation**: Maintained under `datasets/nlp/eqgen/` as distinct academic research data. The Golden (human-validated), Silver (filtered), and GPT-generated partitions are preserved in separate manifests.
- **Leakage Rule**: Paragraph IDs are grouped atomically across splits to ensure no source textbook paragraph appears in both training and test partitions.

---

## 4. Hardware Budgets & Execution Constraints

The target execution environment consists of:
- **GPU**: NVIDIA GeForce GTX 1650 (4 GB VRAM, Turing architecture).
- **CPU**: Intel Core i5-12450H (8 cores / 12 threads).
- **System Memory**: 16 GB DDR4/DDR5.

### Engineering Directives:
1. **Lightweight Batching**: Computer vision training and generation routines must operate with batch sizes $\le 32$ to prevent VRAM overflow.
2. **Sequential Model Invocation**: Multiple heavy models (e.g. YOLOv8n-pose alongside Faster-Whisper or PyTorch CNNs) must never be loaded into GPU memory simultaneously. Models must follow a lazy-load / explicit-unload pattern.
3. **CPU Fallback Architecture**: All preprocessing, data generation, and tabular/text operations execute on CPU threads, reserving GPU memory exclusively for tensor matrix multiplication during inference or backpropagation.
4. **Storage Ceilings**: Synthetic generation routines must enforce hard sample caps to prevent disk exhaustion.

---

## 5. Provenance Catalog Schema

All datasets in ClassVision AI are cataloged with standardized provenance tags:
- `KAGGLE DATA`: Authentic public datasets downloaded from Kaggle repositories.
- `SYNTHETIC DATA`: Programmatically generated or augmented variations with verified parameters and seeds.
- `ACADEMIC GITHUB`: Peer-reviewed academic research datasets (e.g. E-QGen).
- `PRETRAINED MODEL`: Weights released by upstream research consortia (e.g. Ultralytics YOLOv8, OpenAI/Systran Whisper).
- `DEMONSTRATION DATA`: Lightweight in-memory sample inputs for unit tests.

These provenance definitions are stored in [`datasets/metadata/dataset_sources.json`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/datasets/metadata/dataset_sources.json) and exposed via `/api/datasets` endpoints.


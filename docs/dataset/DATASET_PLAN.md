# ClassVision AI — Dataset Strategy and Data Plan

## 1. Executive Summary
ClassVision AI employs a strictly partitioned multi-source data strategy. To ensure rigorous scientific validity, prevent data leakage, and honor classroom privacy, datasets are segregated into four isolated categories across all stages of development:
1. **Kaggle / Public Datasets** (`datasets/kaggle/`)
2. **Synthetic Data** (`datasets/synthetic/`)
3. **Real Classroom Data** (`datasets/real_classroom/`)
4. **Final Evaluation Benchmark Data** (`datasets/evaluation/`)

---

## 2. Dataset Categories

### 2.1 Kaggle & Public Datasets (`datasets/kaggle/`)
- **Scope**: Open-source, permissively licensed datasets from Kaggle, academic publications, and public machine learning repositories.
- **Coverage**:
  - `hand_gesture/`: Canonical static and dynamic hand gesture datasets for hand-raise detection.
  - `classroom_activity/`: Action classification corpora containing labels for student behaviors (sitting, writing, reading, standing).
  - `education_nlp/`: Lecture transcripts, educational Q&A corpora, textbook passages, and subject taxonomy trees.
- **Role**: Baseline model development, transfer learning, backbone feature extractor pre-training, and initial hyperparameter search.
- **Access Rule**: Read-only once downloaded and verified. Every dataset must have a recorded entry in `manifests/datasets.json` and a completed `dataset_info.md`.

### 2.2 Synthetic Data (`datasets/synthetic/`)
- **Scope**: Artificially generated images, 2D/3D pose sequences, simulated classroom scenarios, and synthetic lecture dialogues.
- **Coverage**:
  - `hand_raise/`: Procedurally generated poses, rotated/scaled arms, synthetic silhouettes with varied arm angles and occlusion patterns.
  - `classroom_activity/`: Algorithmic combinations of student poses, varied desk layouts, synthetic noise, lighting shifts, and head angle variations.
  - `lecture_text/`: Synthetic lecture transcripts with deliberately injected speech recognition anomalies, phonetic typos, and domain-specific terminology for RAG stress testing.
- **Role**: Data augmentation, edge-case coverage (rare gestures, severe partial occlusions, difficult lighting), and bootstrap training when real data is scarce.
- **Strict Boundary**: Synthetic data is strictly confined to training sets. Under no circumstances may synthetic data appear in validation or testing splits.

### 2.3 Real Classroom Data (`datasets/real_classroom/`)
- **Scope**: Primary observations recorded in real academic classroom environments under explicit institutional consent and ethical clearance.
- **Coverage**:
  - `images/`: High-resolution snapshots of classroom layouts, desks, and student postures with anonymous bounding boxes.
  - `videos/`: Multi-angle continuous classroom footage capturing natural interactions, transitions, and teacher-student exchanges.
  - `audio/`: Dedicated instructor lapel and ambient classroom audio recordings of lecture delivery.
  - `board/`: High-contrast captures of blackboards and whiteboards containing handwritten equations, diagrams, and printed projection slides.
- **Role**: Domain adaptation, fine-tuning of vision and acoustic models, and domain-specific evaluation.
- **Privacy Protections**: Anonymous identifiers only (e.g., `TRACK_101`). Absolute prohibition of facial recognition or student identification. Faces are blurred at ingestion before permanent storage.

### 2.4 Final Evaluation Benchmark Data (`datasets/evaluation/`)
- **Scope**: A frozen, curated set of multi-modal classroom test samples capturing diverse environmental conditions, acoustics, and classroom architectures.
- **Sub-benchmarks**:
  - `cv/`: Hand-raise detection mAP, action recognition top-1/top-5 accuracy, multi-object tracking precision (MOTP/MOTA).
  - `nlp/`: Lecture topic segmentation accuracy, RAG retrieval precision@k, question-answering fidelity.
  - `ocr/`: Board text extraction Character Error Rate (CER) and Word Error Rate (WER).
  - `speech/`: Automated Speech Recognition Word Error Rate (WER) across teacher and student speech.
  - `end_to_end/`: Multi-modal timeline synchronization, anomaly event detection, and latency metrics.
- **Immutable Rule**: This test set is completely frozen. Model training or hyperparameter tuning against this benchmark is strictly forbidden to prevent subtle test set leakage.

---

## 3. Why Data Pools Are Kept Strictly Separate

Segregation of these four data streams is enforced at the filesystem, manifest, and script execution levels for five foundational reasons:

1. **Prevention of Target Distribution Leakage**:
   Public datasets collected in lab settings or distinct cultural contexts do not reflect the physical acoustics and desk geometries of local classrooms. Mixing public and real data without boundary tags risks severe distribution skew that masks real-world model failure.

2. **Integrity of Synthetic Isolation**:
   Generative data generation algorithms often repeat latent artifacts (such as common rendering patterns or template phrasing). If synthetic samples are mixed into validation or test partitions, models score artificially high by recognizing generative artifacts rather than semantic features. Synthetic data is restricted to `train` splits only.

3. **Ground Truth Sanctity of the Frozen Evaluation Set**:
   To establish honest, scientifically defensible accuracy metrics, the evaluation suite (`datasets/evaluation/`) must remain pristine. No image, video, audio snippet, or text segment in the evaluation pool may ever be viewed by a training loop. Hash-based verification (SHA-256 deduplication) is executed prior to any training run to guarantee zero cross-contamination.

4. **Privacy, Compliance, and Data Governance**:
   Real classroom data contains sensitive environmental recordings and requires strict local data residency, face blurring, and anonymization pipelines. Public and synthetic datasets carry no such constraints. Physical separation ensures that privacy scrubbing workflows (face-blurring, audio sanitization) are reliably applied to all real data without overhead or accidental publishing.

5. **Licensing and Attribution Auditing**:
   Public datasets operate under varying licenses (e.g., CC BY 4.0, MIT, Research Only). Maintaining distinct provenance boundaries prevents viral license contamination of proprietary or institutional project artifacts.

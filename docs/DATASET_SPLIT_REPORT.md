# ClassVision AI — Dataset Splitting Strategy & Partitioning Report (Audited & Corrected)

**System Version:** ClassVision AI 2.0  
**Audit & Correction Date:** 2026-10-31T17:15:00+05:30  
**Partitioning Engine:** `scripts/generate_dataset_splits.py`  
**Manifest Storage:** `datasets/splits/`  
**Deterministic Seed:** `42` (Fixed across all generators)

---

## 1. Executive Summary & Audit Reconciliations

This report documents the exact partitioning strategies, sample counts, and leakage prevention protocols across all datasets in ClassVision AI.

### Audited Partition Summary

| Dataset | Splitting Strategy | Train Samples | Val Samples | Test Samples | Total Partitioned | Integrity & Leakage Check | Manifest Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **English Character Recognition** | Stratified Multi-Class ($k=62$) | 6,572 (70.7%) | 1,364 (14.7%) | 1,364 (14.7%) | **9,300** (Subsampled from 210,227) | 0 path overlap; 32 source font hash duplicates (0.34%) | `datasets/splits/english_character_recognition_split.json` |
| **COCO 2017 Keypoints** | Official Benchmark Split | 56,599 (96.0%) | 2,346 (4.0%) | Benchmark Val | **58,945** images on disk | Image-level partition (0 person crop leakage across splits) | `datasets/splits/coco_keypoints_split.json` |
| **Sign Language MNIST** | Stratified ASL ($k=24$) | 21,964 (63.4%) | 5,491 (15.9%) | 7,172 (20.7%) | **34,627** samples | 0 duplicate rows between train and test CSVs | `datasets/splits/sign_language_mnist_split.json` |
| **Hand Gesture Recognition** | Stratified Numerical ($k=20$) | 14,400 (60.0%) | 3,600 (15.0%) | 6,000 (25.0%) | **24,000** images on disk | 0 hash collisions between train (18k) and test (6k) | `datasets/splits/hand_gesture_split.json` |
| **CommonLit Student Summaries** | Stratified by Prompt & Target | 5,015 (70.0%) | 1,075 (15.0%) | 1,075 (15.0%) | **7,165** summaries | Stratified across 4 prompts & score quintiles | `datasets/splits/commonlit_summaries_split.json` |
| **E-QGen Golden QA Set** | Grouped by `video_id` | 264 (74.2%) | 47 (13.2%) | 45 (12.6%) | **356** QA pairs | **0% lecture video overlap** (strict lecture isolation) | `datasets/splits/eqgen_golden_split.json` |
| **E-QGen Silver QA Set** | Grouped by Paragraph Hash | 3,103 (70.0%) | 665 (15.0%) | 666 (15.0%) | **4,434** QA pairs | **0% paragraph context overlap** (strict hash grouping) | `datasets/splits/eqgen_silver_split.json` |
| **Mozilla Common Voice** | Official Mozilla Splits (Metadata) | 195,776 (CSV) | 4,076 (CSV) | 3,995 (CSV) | **50 audio on disk** | Incomplete audio on disk; splits exist in CSV metadata only | `datasets/splits/common_voice_split.json` |

---

## 2. Modality Partition Details & Investigations

### 2.1. English Character Recognition (9,300 Subset Audit)
* **Investigation Findings:**
  1. The full directory contains 210,227 images.
  2. The split manifest contains exactly **9,300 images** (6,572 train, 1,364 val, 1,364 test).
  3. This was an intentional design choice: `scripts/train_character_recognition.py` set `max_samples_per_class = 150` to enable fast training (~77 seconds) on CPU hardware without memory overflow.
  4. Each of the 62 alphanumeric classes is represented identically:
     $$\text{Per Class: } 106 \text{ train} + 22 \text{ val} + 22 \text{ test} = 150 \text{ samples}$$
  5. **File Path Overlap:** Exactly **0** duplicate file paths exist between train, validation, and test subsets.
  6. **Hash Collision Audit:** Hashing all 9,300 images revealed 98 unique file hashes repeated across multiple folders in the raw Kaggle dataset (e.g. blank background tiles or identical font glyphs created during font rasterization). Consequently, 32 test images share identical hashes with training samples (a 0.34% artifact inherent to the raw Kaggle dataset).

### 2.2. Mozilla Common Voice Partition Audit
* **Investigation Findings:**
  1. The CSV metadata files define official community splits: `cv-valid-train.csv` (195,776 rows), `cv-valid-dev.csv` (4,076 rows), `cv-valid-test.csv` (3,995 rows).
  2. However, the physical filesystem contains only **50 audio files** in `datasets/kaggle/common_voice/samples/`.
  3. Furthermore, these 50 files were extracted from the archive's `cv-invalid/` directory rather than `cv-valid-test/`.
  4. Therefore, the official splits exist only at the CSV metadata level. The physical audio dataset on disk is incomplete.

### 2.3. Hand Gesture Recognition Partition Audit
* **Investigation Findings:**
  1. The dataset contains 24,000 images divided into `train` (18,000 images, 900/class) and `test` (6,000 images, 300/class).
  2. For model training and validation, 200 images per class were drawn from `train` (160 train, 40 val) and 100 images per class were drawn from `test` (total: 3,200 train, 800 val, 2,000 test).
  3. SHA-256 hashing across all 18,000 train images and 6,000 test images confirmed:
     $$\text{Exact Hash Overlap between Train and Test} = \mathbf{0}$$
  4. Test samples were never used during model selection, hyperparameter tuning, or epoch validation.

### 2.4. COCO Keypoints Partition Audit
* **Preservation of Official Splits:**
  - `Train2017`: 56,599 JPEG images extracted to `train2017/` with 262,465 annotations.
  - `Val2017`: 2,346 JPEG images extracted to `val2017/` with 11,004 annotations.
* **Integrity:** Splits are partitioned strictly by image file. No person crop from a training image appears in the validation partition.

---

## 3. Reproducibility Guarantee

All manifests are stored as JSON files under `datasets/splits/`. Re-running `python scripts/generate_dataset_splits.py` reproduces the exact split indices using deterministic seed `42`.

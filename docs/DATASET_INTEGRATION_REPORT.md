# ClassVision AI — Dataset Integration Report (Audited & Corrected)

**System Version:** ClassVision AI 2.0  
**Audit & Correction Date:** 2026-10-31T17:15:00+05:30  
**Auditor:** Principal AI Architect & Data Engineering Lead  
**Repository:** `C:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection`  

---

## 1. Executive Summary & Audit Corrections

This audited report provides a verified accounting of all datasets integrated into the ClassVision AI repository. Following an independent audit, several critical corrections have been applied:
1. **Physical File vs. Metadata Distinction:** Corrected the mischaracterization of Mozilla Common Voice. The local disk contains **50 audio files** in `samples/`, while the 203,847 count represents unextracted CSV metadata references from the 380,368-file archive. Common Voice is explicitly marked as **INCOMPLETE on disk**.
2. **Subsampling Transparency:** Transparently documented that English Character Recognition contains **210,227 total images** on disk, but the active training/evaluation split uses a **uniform 9,300-image stratified benchmark** (150 images $\times$ 62 classes) for tractable CPU training.
3. **COCO Keypoints Physical Inventory:** Reconciled COCO 2017 counts: the archive specifically contains **58,945 JPEG images** (56,599 train + 2,346 val) matching instances with annotated keypoints (`num_keypoints > 0`), alongside 273,469 total annotations.
4. **Provenance Separation:** Clarified that E-QGen originates from an **Academic GitHub Research Repository**, NOT Kaggle.

---

## 2. Verified Dataset Inventory (Audited Physical Counts)

| Dataset Name | Domain / Modality | Physical Path | Formats | Verified Samples on Disk | Classes / Targets | Verification Status | Source & License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **English Character Recognition** | Computer Vision / OCR | `datasets/kaggle/handwriting/english_character_recognition/` | PNG | **210,227** images (9,300 in active split) | 62 alphanumeric (`0-9`, `A-Z`, `a-z`) | **VERIFIED ON DISK** (Full archive extracted; 9.3k active) | Kaggle / Open Source (License UNKNOWN) |
| **COCO 2017 Keypoints** | Pose Estimation | `datasets/kaggle/human_pose/coco_keypoints/` | JPEG + JSON | **58,945** images (56,599 train, 2,346 val), 273,469 annots | 17 COCO body keypoints | **VERIFIED & EXTRACTED** | COCO Consortium / CC BY 4.0 |
| **Sign Language MNIST** | Computer Vision / ASL | `datasets/kaggle/sign_language_mnist/` | CSV ($28 \times 28$) | **34,627** samples (27,455 train + 7,172 test) | 24 static letters (`A-Y`, excl. `J`, `Z`) | **VERIFIED ON DISK** | Kaggle / CC0 Public Domain |
| **Hand Gesture Recognition** | Computer Vision / Gestures | `datasets/kaggle/hand_gesture/extracted/` | PNG ($50 \times 50$) | **24,000** images (18,000 train + 6,000 test) | 20 numerical classes (`0` to `19`) | **VERIFIED ON DISK** | Kaggle / Open Access |
| **CommonLit Student Summaries** | Educational NLP | `datasets/kaggle/commonlit_summaries/` | CSV / Text | **7,165** summaries + 4 prompts | 2 continuous targets (`content`, `wording`) | **VERIFIED ON DISK** | Kaggle / CC BY-NC-SA 4.0 |
| **E-QGen Educational NLP** | Educational NLP / QA | `datasets/nlp/eqgen/` | CSV | **4,790** pairs (356 golden + 4,434 silver) | Lecture QA pairs + transcripts | **VERIFIED ON DISK** | Academic GitHub / MIT Research |
| **Mozilla Common Voice (Subset)** | Speech / ASR | `datasets/kaggle/common_voice/` | CSV + MP3 | **50 audio files on disk** (203k rows in CSVs) | Transcripts + metadata | **INCOMPLETE ON DISK** (Partial extraction) | Mozilla / CC0 |
| **Human Detection Dataset** | Computer Vision / Detection | N/A | N/A | **0 samples** | N/A | **MISSING / NOT DOWNLOADED** | Missing Archive |

---

## 3. Detailed Modality Audits & Discrepancy Findings

### 3.1. English Character Recognition
- **Total Archive Content:** 210,227 images across 62 folders (`0-9`, `A-Z`, `a-z`), with ~3,400 images per class.
- **Active Benchmark Split:** Exactly **9,300 images** (6,572 train, 1,364 val, 1,364 test).
- **Subsampling Rationale:** Intentionally subsampled at `max_samples_per_class = 150` to enable rapid CPU training (~77s) on the HP Victus laptop without memory thrashing.
- **Hash Collision Audit:** While path overlap across splits is strictly **0%**, 98 unique image hashes are duplicated across different folders in the original Kaggle archive (e.g. blank background tiles or identical font glyphs). This results in 32 test images sharing hashes with train images (0.34% artifact inherent to the source data).
- **All 62 Classes Represented:** Verified. Exactly 106 train, 22 val, and 22 test samples per class.

### 3.2. Mozilla Common Voice
- **Archive vs. Disk Finding:** The source archive `C:\Users\prash\Downloads\cv folder.zip` contains **380,368 MP3 audio files** (~20 GB). However, only the 7 official CSV metadata files and a subfolder of **50 MP3 sample files** (`sample-000000.mp3` through `sample-000049.mp3`) were extracted to disk.
- **Root Cause of 99.56% WER:** The 50 sample files on disk originated from the archive's `cv-invalid/` directory. When `scripts/evaluate_baselines.py` evaluated these invalid files, it compared them against reference text from `cv-valid-test.csv`. Because the audio content and reference sentences were completely mismatched, an artificial 99.56% Word Error Rate was recorded.
- **Genuine Transcription Verification:** When genuine audio from `cv-valid-test/sample-000000.mp3` was extracted and tested, Faster-Whisper transcribed it accurately ("Without the data set, the article is useless." vs. reference "without the dataset the article is useless").
- **Audit Verdict:** The local Common Voice dataset is **INCOMPLETE on disk** (50 audio files). We do not claim successful whole-dataset ASR evaluation.

### 3.3. COCO 2017 Keypoints
- **Inventory Verification:** All **58,945 JPEG images** (56,599 train + 2,346 val) and both official annotation files (`person_keypoints_train2017.json` and `person_keypoints_val2017.json`) are physically extracted to `datasets/kaggle/human_pose/coco_keypoints/`.
- **Integrity:** 0 corrupted image files; 1 invalid bounding box in train (out of 262,465 annotations), 0 in val.
- **Evaluation Expanded:** Evaluated on a representative **250-image validation subset** (667 ground-truth persons), achieving **96.40% person detection recall**, **0.5102 mean OKS**, and **90.64% upper-body PCK@0.2**.

### 3.4. Hand Gesture Recognition
- **Inventory Verification:** Exactly 24,000 images (18,000 train + 6,000 test) across 20 classes (`0` through `19`).
- **Hash Integrity:** SHA-256 hashing across all 18,000 train images and 6,000 test images revealed **0 exact hash collisions** between train and test.
- **100% Accuracy Cause:** The dataset consists of tightly centered, high-contrast $50 \times 50$ grayscale hand silhouettes on uniform backgrounds. Inter-class MSE distance (22,130) is over 7 times greater than intra-class distance (3,006), making linear separation trivial.
- **Strict Boundary:** Classes are numerical tokens `0` through `19` and **must remain strictly unmapped to classroom behaviors**.

### 3.5. E-QGen Educational NLP
- **Correction:** E-QGen originates from the academic paper *“Educational Question Generation from Lecture Videos”* (lead-ai/E-QGen on GitHub), NOT Kaggle.
- **Sample Count:** 4,790 pairs (356 golden + 4,434 silver).

### 3.6. Human Detection Dataset
- **Status:** **MISSING / NOT DOWNLOADED (0 samples)**. Honestly reported.

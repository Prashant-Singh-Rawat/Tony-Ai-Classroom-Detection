# ClassVision AI — Dataset Provenance & Policy Compliance Report (Audited & Corrected)

**System Version:** ClassVision AI 2.0  
**Audit & Correction Date:** 2026-10-31T17:15:00+05:30  
**Auditor:** Principal AI Architect & Data Engineering Lead  
**Governing Policy:** 50% Compatible Kaggle / 50% Compatible Synthetic / 0% Real-Life Classroom Recordings  

---

## 1. Executive Summary & Audit Correction Standards

Following the dataset audit, the provenance accounting has been corrected:
1. **Disaggregation of Modalities:** We reject the practice of combining unrelated modalities (audio seconds, text summaries, image crops, and body keypoints) into a single artificial composite ratio. Each compatible task must be evaluated and balanced separately.
2. **Physical Data Counting Only:** Unextracted CSV metadata rows (e.g. 203,847 rows in Common Voice) are not counted as physical data samples.
3. **Source Integrity:** E-QGen is classified strictly as **Academic Research NLP**, NOT Kaggle data.
4. **0% Real-Life Classroom Recordings:** **100% COMPLIANT**. Zero student recordings exist on disk.

---

## 2. Task-by-Task Provenance Breakdown (Audited Physical Counts)

| Compatible Task / Domain | Kaggle Samples on Disk | Academic GitHub Samples | Synthetic Samples on Disk | Real Classroom Samples | Current Ratio (Kaggle:Synthetic:Real) | Compliance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Character Recognition (OCR)** | 210,227 (9.3k active) | 0 | 0 | 0 | 100.0% / 0.0% / 0.0% | Synthetic Shortfall |
| **ASL Fingerspelling (Sign MNIST)** | 34,627 | 0 | 0 | 0 | 100.0% / 0.0% / 0.0% | Synthetic Shortfall |
| **Hand Gesture Recognition** | 24,000 | 0 | 0 | 0 | 100.0% / 0.0% / 0.0% | Synthetic Shortfall |
| **Human Body Pose (COCO)** | 58,945 (273k annots) | 0 | 463 vectors | 0 | 99.2% / 0.8% / 0.0% | Synthetic Shortfall |
| **Student Summary Scoring** | 7,165 | 0 | 0 | 0 | 100.0% / 0.0% / 0.0% | Synthetic Shortfall |
| **Speech Recognition (Common Voice)** | 50 (physical clips) | 0 | 0 | 0 | 100.0% / 0.0% / 0.0% | Incomplete / Shortfall |
| **Educational QA (E-QGen)** | 0 | 4,790 | 0 | 0 | Non-Kaggle Academic | Academic Research Benchmark |
| **Human Detection** | 0 (missing) | 0 | 0 | 0 | 0 / 0 / 0 | Missing Archive |

---

## 3. Real Classroom Recording Audit (0% Target: Fully Compliant)

ClassVision AI maintains zero physical storage of student surveillance feeds:
- **Volatile Execution:** Webcam feeds reside strictly in RAM buffers and are dropped immediately after inference.
- **Client & Server Anonymization:** Dual-layer Gaussian and canvas blurring obscures facial features before and after WebSocket transmission.
- **Anonymous Session Identifiers:** SQLite events store temporary track IDs (`track_id: 1`, `track_id: 2`) that expire upon track timeout and never link to student names or biometrics.

---

## 4. Realistic Synthetic Data Generation Plan (Per-Task Roadmap)

To achieve the 50% Kaggle / 50% Synthetic balance without artificial duplication, the following realistic synthesis pipelines are proposed:

### 4.1. Task 1: Character Recognition
* **Shortfall:** 9,300 active synthetic samples (or 210,227 for the full archive).
* **Generation Method:** Python `PIL.ImageDraw` rendering 100+ open-source Google TTF fonts across all 62 alphanumeric glyphs (`0-9`, `A-Z`, `a-z`) with parameterized elastic distortions, shear, Gaussian noise, and contrast perturbations.
* **Compatibility:** Exactly matches $128 \times 128 \times 3$ PNG single-character format.

### 4.2. Task 2: Human Body Pose Estimation
* **Shortfall:** 58,482 synthetic keypoint vectors (to balance 58,945 COCO images).
* **Generation Method:** Scale the existing Phase 2.6 procedural classroom pose engine (`generate_synthetic_pose_stream()`) to generate 58,482 structured $(17, 3)$ COCO-format vectors modeling seated desk posture, hand-raising elevation, writing, and turning postures.
* **Compatibility:** 100% compatible with the official 17 COCO keypoint schema and skeleton connections.

### 4.3. Task 3: ASL Fingerspelling (Sign Language MNIST)
* **Shortfall:** 34,627 synthetic samples.
* **Generation Method:** Procedural 3D hand mesh rendering (via Blender API or MediaPipe hand joint parameterizations) projecting 24 static letter hand poses onto $28 \times 28$ grayscale pixel arrays with random rotation $[-\pi/6, \pi/6]$.
* **Compatibility:** Flat 785-column CSV matching Sign MNIST format.

### 4.4. Task 4: Hand Gesture Recognition
* **Shortfall:** 24,000 synthetic images.
* **Generation Method:** Morphological dilation, rotation, and affine warping across the 20 archetype hand gesture masks, generating 1,200 synthetic $50 \times 50$ grayscale PNG images per class.

### 4.5. Task 5: Student Summary NLP Scoring
* **Shortfall:** 7,165 synthetic summaries.
* **Generation Method:** Template-based educational summary generation with rule-based grammar and lexical perturbations calibrated against CommonLit rubric dimensions (content coverage and wording quality).

### 4.6. Task 6: Speech Recognition (ASR)
* **Shortfall:** 50 matching synthetic audio files (matching the 50 physical clips on disk).
* **Generation Method:** Text-to-speech synthesis (Edge-TTS / Piper) reading lecture transcript passages with additive background classroom noise (HVAC hum, page turns).

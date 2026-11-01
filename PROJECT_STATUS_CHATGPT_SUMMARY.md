# ClassVision AI — Comprehensive Project Summary & Handover Document
> **Purpose**: Copy-paste this entire document into ChatGPT, Claude, or any LLM to give it full context on what the project is, what has been completed, what is mocked, current roadblocks, dataset status, model details, and the next implementation steps.

---

## 1. Executive Summary & Project Identity

- **Project Name:** ClassVision AI — Real-Time Multimodal Classroom Intelligence System
- **Academic Context:** Final-Year B.Tech Capstone Project
- **Primary Goal:** Build a real-time, privacy-preserving classroom analytics system fusing:
  1. **Computer Vision (CV):** Person detection, upper-body bounding boxes, hand-raise detection, student activity classification, and pose estimation.
  2. **Audio / Speech Recognition (ASR):** Automated speech-to-text of lecture audio using `faster-whisper`.
  3. **Board / Whiteboard OCR:** Slide and blackboard/whiteboard text extraction using `EasyOCR`.
  4. **Natural Language Processing (NLP):** Topic segmentation, sentiment/confusion tracking, and keyword extraction.
  5. **Retrieval-Augmented Generation (RAG):** Curriculum-aligned semantic search and student Q&A assistant over lecture transcripts and whiteboard notes using a local vector store (`ChromaDB`).
  6. **Unified Analytics Dashboard:** Real-time and post-session monitoring UI displaying student engagement, participation trends, hand raises, and teacher delivery insights.

- **Honest Engineering Philosophy:** 
  The project strictly rejects fake accuracy numbers and paper claims. If a model has not been trained, metrics are marked **"Unavailable, no model trained / NOT CONNECTED"**. All demo values in the UI are explicitly tagged with visual badges (`[REAL]`, `[DEMO DATA]`, `[NOT CONNECTED]`).

---

## 2. Current Project State & Phase Progress

The project follows a strict 19-phase development roadmap (defined in `classvision-ai/docs/phases.md`). **No phase may begin until the previous phase's gate condition is 100% satisfied.**

### Current Stage: **Phase 0.8 / 0.9 (Pre-Collection, Ingestion Engineering & UI Foundation Complete)**

| Phase | Description | Status | Verification |
|---|---|---|---|
| **Phase 0.1** | Repository Architecture & Policy Specs | ✅ **DONE** | Strict directory structure, privacy policies, dataset policies. |
| **Phase 0.2** | Environment & Dependency Audit | ✅ **DONE** | `scripts/check_env.py`, configuration verification. |
| **Phase 0.3** | Kaggle Hand Gesture Ingestion & Checksumming | ✅ **DONE** | 24,000 images verified, SHA-256 locked, read-only. |
| **Phase 0.4** | Dataset Isolation & Class Verification | ✅ **DONE** | Verified Kaggle dataset has 20 classes (0-19) with unmapped semantics. |
| **Phase 0.5** | Visual Contact Sheet & Zero-Model Check | ✅ **DONE** | Generated 240-image contact sheet; verified 0 model files exist. |
| **Phase 0.6** | Real Classroom Ingestion & Processing Scripts | ✅ **DONE** | Frame extraction, phash deduplication, YOLO validator, session splitter. |
| **Phase 0.7** | Annotation Workflow & CVAT Protocol | ✅ **DONE** | Standard operating procedure, person-level bounding box schema. |
| **Phase 0.8** | Real Classroom Preflight & Quality Reporting | ✅ **DONE** | `annotation_preflight.py`, `collection_report.py`, 60/60 unit tests pass. |
| **Phase 0.9** | Frontend Web Dashboard Foundation | ✅ **DONE** | React 19 + Vite + Tailwind dashboard with 8 pages, 26/26 tests pass. |
| **Phase 1** | FastAPI Backend Skeleton | ⏳ **PENDING** | Folder structure exists (`classvision-ai/backend/app`), routes not yet built. |
| **Phase 2–19** | Model Training, CV Inference, Whisper, OCR, RAG | 🛑 **BLOCKED** | Blocked until real classroom data is collected and annotated. |

---

## 3. Ground-Truth Data & Dataset Status

The project strictly segregates data into 4 isolated pools (`datasets/`):

### 1. Kaggle Hand Gesture Dataset (`datasets/kaggle/hand_gesture/`)
- **Quantity:** 24,000 images (50×50 grayscale JPGs).
- **Split:** 18,000 train, 6,000 test.
- **Classes:** 20 numerical classes (`0` through `19`).
- **Integrity:** SHA-256 verified against source `train.zip` and `test.zip`.
- **CRITICAL LIMITATION:** This dataset contains tightly cropped hand silhouettes on plain backgrounds. It lacks whole-body human posture, classroom context, desk occlusions, and semantic labels. **Project policy strictly prohibits using this dataset to train classroom hand-raise detection**, as doing so would cause extreme out-of-distribution failure in a real classroom.

### 2. Real Classroom Dataset (`datasets/real_classroom/`)
- **Quantity:** **0 videos, 0 frames, 0 annotations** (Currently empty).
- **Why empty?** Real recording starts after **12 October 2026** upon college reopening with student consent and institutional ethics protocols.
- **Target Collection Plan:**
  - 8 to 12 lecture sessions across at least 3 distinct classroom environments.
  - ~1,000 high-quality reviewed frames.
  - Class distribution target: $\ge 20\%$ positive hand raises via a dual-source protocol (combining unscripted lecture time with structured consented hand-raise drills).
- **Annotation Schema:** Person-level upper-body YOLO format boxes:
  - `0: hand_raised`
  - `1: hand_not_raised`
  - `2: ambiguous`

### 3. Synthetic Data (`datasets/synthetic/`)
- **Quantity:** 0 (Planned for edge cases and pose augmentation). Synthetic data is strictly restricted to training sets and never permitted in evaluation splits.

### 4. Evaluation Benchmark (`datasets/evaluation/`)
- **Quantity:** 0 (To be frozen once real classroom test sessions are collected).

---

## 4. Models & AI Pipelines: Plan vs. Reality

| Module | Planned Model / Technology | Implementation Status | Active Checkpoints / Weights | Evaluation Metrics |
|---|---|---|---|---|
| **Person Detection** | YOLOv8n (nano) | Not implemented | `None` (0 checkpoints) | Not connected |
| **Hand-Raise Detection** | YOLOv8n / Keypoint Classifier on person box | Not implemented | `None` (0 checkpoints) | Precision/Recall: Unavailable |
| **Activity & Pose** | MediaPipe Pose (CPU $\ge 10$ fps) | Not implemented | `None` | F1-Score: Unavailable |
| **Speech-to-Text (ASR)**| `faster-whisper` (tiny/base) | Not implemented | `None` | WER: Unavailable |
| **Whiteboard OCR** | `EasyOCR` (fallback for PaddleOCR) | Not implemented | `None` | CER: Unavailable |
| **Topic & Sentiment** | `sentence-transformers` + lightweight classifier | Not implemented | `None` | Macro F1: Unavailable |
| **RAG Assistant** | `ChromaDB` local vector store + LLM | Not implemented | `None` | Retrieval Latency: Unavailable |

> **Key takeaway:** There are currently **ZERO trained weights, ZERO `.pt` / `.onnx` model files**, and **ZERO connected inference pipelines**. Anyone claiming the model achieves 95% accuracy is hallucinating.

---

## 5. What is Actually Built and Working?

### A. Python Dataset Processing Pipeline (`scripts/` & `tests/`) — 100% WORKING
1. **`extract_classroom_frames.py`:**
   - Extracts frames from video with timestamp-based naming: `<session_id>/<video_stem>_t<ms>.jpg`.
   - Records metadata in `frame_manifest.csv`.
   - Computes blur variance (Laplacian) and brightness in `quality_report.csv`.
   - Idempotent: automatically skips already extracted frames.
2. **`deduplicate_classroom_frames.py`:**
   - Performs perceptual hashing (`imagehash.phash`) within individual sessions to eliminate identical/static frames.
   - Supports dry-run reporting and `--apply` copying to `frames/deduplicated/`.
3. **`validate_annotations.py`:**
   - Validates YOLO coordinate boundaries $[0.0, 1.0]$.
   - Enforces class IDs (`0, 1, 2`).
   - Cross-references that every `.txt` annotation has a matching `.jpg` image.
   - Enforces two-tier workflow (`raw` vs `reviewed`).
4. **`split_classroom_dataset.py`:**
   - Performs **session-level splitting** (all frames from a session stay together in train, val, or test). Never splits by frame, preventing severe cross-frame data leakage.
   - Generates `splits/train.txt`, `splits/validation.txt`, `splits/test.txt`, and `splits/split_manifest.json`.
5. **`annotation_preflight.py` & `collection_report.py`:**
   - Audits annotation sanity, detects inverted class ratios, checks multi-session requirements, and outputs Markdown summaries.
6. **Automated Test Suite:**
   - **60 out of 60 pytest unit tests pass cleanly** (`python -m pytest -v`).
   - Tests verify determinism, data immutability, edge cases, error handling, and guarantee no unapproved model files exist.

### B. Frontend Dashboard (`frontend/`) — 100% WORKING (UI + Mock Data Layer)
- **Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React icons, Vitest.
- **Test Suite:** **26 out of 26 Vitest unit tests pass cleanly** (`npm --prefix frontend test`).
- **Pages Implemented:**
  1. `LandingPage.tsx`: Product introduction, architectural flow, and feature showcase.
  2. `DashboardPage.tsx`: Live summary cards, active session telemetry, engagement trends.
  3. `MonitoringPage.tsx`: Multi-camera grid view, simulated bounding boxes (`hand_raised`, `student`), alert feed.
  4. `AnalyticsPage.tsx`: Hand-raise frequency charts, hourly attention graphs, classroom participation heatmaps.
  5. `IntelligencePage.tsx`: Aggregated lecture intelligence combining mock Whisper audio transcripts with whiteboard OCR text.
  6. `AskClassVisionPage.tsx`: Interactive RAG question-answering assistant over lecture materials.
  7. `ReportsPage.tsx`: Session reports, attendance, automated lecture summary export, and model quality cards.
  8. `ModelStatusPage.tsx`: Dedicated audit page displaying verified ground-truth repository facts vs unconnected modules.
  9. `SettingsPage.tsx`: Hardware camera configuration, storage path, privacy retention policies.
- **Service Layer (`frontend/src/services/api.ts`):**
  - Fully typed interface (`ClassVisionApi`).
  - `DemoClassVisionApi`: Serves labeled mock data and real repository snapshot metrics.
  - `RealClassVisionApi`: Pre-structured stubs ready to connect to FastAPI endpoints once built.
  - Toggled via `VITE_USE_DEMO_DATA=true|false`.

---

## 6. Known Issues, Technical Constraints & Blockers

### 1. The Real Classroom Data Blocker (Critical Path)
- **Problem:** No classroom videos have been recorded yet. College reopens after 12 October 2026.
- **Impact:** Model training cannot begin until footage is recorded, extracted, deduplicated, and hand-annotated with person-level bounding boxes.
- **Policy Enforcement:** Training on Kaggle hand silhouettes is forbidden due to negative transfer risk.

### 2. Python 3.14 Compatibility & PaddleOCR
- **Problem:** The workstation runs **Python 3.14.3**. PaddlePaddle / PaddleOCR does not currently offer pre-compiled wheels for Python 3.14 on Windows.
- **Mitigation:** The architecture documents `EasyOCR` as the primary board OCR fallback. If full PaddleOCR is required later, the team must downgrade the Python virtual environment to **Python 3.11**.

### 3. Hardware Limitations (GPU VRAM)
- **Hardware:** Target laptop GPU is an **NVIDIA GeForce GTX 1650 (4 GB VRAM)**.
- **Risk:** Concurrently running YOLOv8, Whisper, MediaPipe, and an embedding model will easily trigger CUDA Out-Of-Memory (OOM).
- **Mitigation Strategy:**
  - Sequential batch processing instead of simultaneous live inferencing.
  - Use `yolov8n` (nano) with batch size = 1.
  - Run `whisper` in CPU mode or use the `tiny.en` / `base.en` quantization.
  - Operate in `DEMO` mode with frame striding (process 1 frame every 5–15 frames instead of 30 fps).

### 4. OneDrive Synchronization & Privacy Hazard
- **Problem:** The repository lives inside a Windows OneDrive folder (`C:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection`).
- **Risk:** Storing identifiable student faces or audio inside OneDrive violates student privacy ethics and institutional clearance.
- **Mitigation:** Real data must be stored in an un-synced external folder (e.g. `D:\ClassVisionData\real_classroom`) controlled via the `CLASSVISION_REAL_DATA_ROOT` environment variable or `--root` CLI argument.

### 5. Backend Server Not Yet Implemented
- **Problem:** `classvision-ai/backend/app/` contains empty skeletons (`.gitkeep`). FastAPI routes (`/health`, `/session`, `/events`, `/analytics`) have not been implemented.
- **Impact:** Frontend currently operates solely in `DemoClassVisionApi` mode.

---

## 7. Immediate Next Steps (Work Plan)

When continuing work on this project, the priority sequence is:

1. **Step 1: Implement FastAPI Backend Skeleton (Phase 1)**
   - Set up `backend/app/main.py` with FastAPI.
   - Implement `/health`, `/api/dashboard/summary`, `/api/sessions`, and `/api/model/status`.
   - Connect frontend `RealClassVisionApi` to FastAPI via Vite proxy or CORS.
2. **Step 2: Collect & Ingest First 3 Real Classroom Sessions (Phase 0.6–0.8)**
   - Record 3 short pilot sessions (post 12 October 2026).
   - Run `python scripts/extract_classroom_frames.py`.
   - Run `python scripts/deduplicate_classroom_frames.py --apply`.
   - Annotate ~200 pilot frames in local CVAT with `hand_raised` / `hand_not_raised`.
   - Run `python scripts/validate_annotations.py` and `python scripts/split_classroom_dataset.py`.
3. **Step 3: Baseline YOLOv8 Person Detection (Phase 2)**
   - Integrate pre-trained `yolov8n.pt` for person bounding boxes.
   - Measure baseline inference latency on GTX 1650.
4. **Step 4: Train Hand-Raise Model (Phase 3)**
   - Fine-tune YOLOv8 on real classroom annotations.
   - Log real mAP, precision, and recall into `classvision-ai/models/model_registry.json`.
5. **Step 5: Offline Audio & Board Processing (Phases 5 & 6)**
   - Implement `faster-whisper` audio transcription worker.
   - Implement `EasyOCR` whiteboard text extraction pipeline.

---

## 8. Quick Fact Sheet for ChatGPT Queries

- **Language & Frameworks:** Python 3.14 (Backend/ML scripts), React 19 + TypeScript + Vite + Tailwind CSS (Frontend).
- **Test Suite Status:** 60/60 Python pytest tests passing; 26/26 Frontend vitest tests passing.
- **Total Real Classroom Videos Collected:** **0**.
- **Total Real Classroom Annotated Frames:** **0**.
- **Kaggle Gesture Images:** **24,000** (50×50, isolated, unmapped semantics, training blocked).
- **Active ML Checkpoints:** **None (0 models trained)**.
- **Backend API:** Skeletons only, FastAPI endpoints pending.
- **Frontend State:** Complete modern UI with realistic simulated telemetry and verified status badges.
- **Primary Privacy Mechanism:** Local offline execution, face blurring on ingestion, storage outside OneDrive via `CLASSVISION_REAL_DATA_ROOT`.


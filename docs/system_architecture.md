# ClassVision AI — System Architecture & Data Flow

**ClassVision AI:** Real-Time Multimodal Classroom Intelligence System  
**Hardware Profile:** HP Victus Laptop | NVIDIA GTX 1650 (4 GB VRAM) | Windows | Python 3.14.3  
**Data Policy:** 50% Kaggle Data / 50% Synthetic Data / **0% Real Classroom Footage**

---

## 1. High-Level Architecture Overview

ClassVision AI is designed as a modular, privacy-preserving multimodal system consisting of four primary layers:

```
+-----------------------------------------------------------------------------------+
|                            React 19 + Vite Frontend                               |
|   Landing | Dashboard | Live Classroom | Analytics | Lecture Intel | Ask RAG | ...|
+------------------------------------------+----------------------------------------+
                                           | HTTP (REST) / WebSocket
+------------------------------------------v----------------------------------------+
|                               FastAPI API Gateway                                 |
|  /api/dashboard | /api/sessions | /api/vision | /api/speech | /api/ocr | /api/rag |
+------------------------------------------+----------------------------------------+
                                           | Service Orchestration
+------------------------------------------v----------------------------------------+
|                                Multimodal AI Engine                               |
|   +-------------------+  +-------------------+  +-------------------------------+ |
|   |  Computer Vision  |  | Speech & Whisper  |  |    Whiteboard / Slide OCR     | |
|   | YOLOv8n / Pose    |  |  Faster-Whisper   |  |            EasyOCR            | |
|   +-------------------+  +-------------------+  +-------------------------------+ |
|   +------------------------------------------+  +-------------------------------+ |
|   |        Lecture NLP & Summarization       |  |      Curriculum RAG Engine    | |
|   |           Sentence-Transformers          |  |     ChromaDB Vector Store     | |
|   +------------------------------------------+  +-------------------------------+ |
+------------------------------------------+----------------------------------------+
                                           | Persistence & Auditing
+------------------------------------------v----------------------------------------+
|                             Local Storage Layer                                   |
|       SQLite (classvision_ai.db)  |  ChromaDB (/data/chroma)  |  ReportLab/Excel  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Multimodal AI Pipelines

### A. Computer Vision Pipeline (YOLOv8n + YOLOv8n-pose + MediaPipe)
- **Person Detection:** YOLOv8n identifies seated students and instructors, generating anonymous bounding boxes (`anon_001`, `anon_002`...).
- **Pose Estimation:** YOLOv8n-pose estimates 17 COCO keypoints (shoulders, elbows, wrists).
- **Geometric Hand-Raise Classification:**
  - Evaluates vertical relationship between wrist and shoulder:
    $$\text{wrist}_y < \text{shoulder}_y - \text{margin}$$
  - Enforces visibility confidence thresholds ($>0.40$).
  - Ambiguous poses or occluded limbs are tagged as `NEEDS_REVIEW`.
- **Privacy Enforcement:** No face recognition, biometric student IDs, or emotion inference.

### B. Speech Recognition Pipeline (Faster-Whisper)
- **Model:** `faster-whisper-tiny` running on CPU with `int8` quantization.
- **Functionality:** Accepts audio input, transcribes lecture speech, segments utterances with millisecond timestamps, and extracts key concepts.

### C. Whiteboard & Slide OCR Pipeline (EasyOCR)
- **Model:** EasyOCR reader for academic English.
- **Functionality:** Ingests whiteboard snapshots and slides, extracts mathematical formulas and notes, and returns bounding polygons and confidence scores.

### D. Retrieval-Augmented Generation (RAG)
- **Embeddings:** `all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Vector Database:** Local persistent ChromaDB (`data/chroma`).
- **Grounding:** Queries retrieve indexed lecture transcripts and OCR notes; if content is missing, an explicit unavailable response is returned without fabrication.

---

## 3. Database Schema (SQLite)

All operational results are persisted to `classvision_ai.db` via SQLAlchemy ORM:

- `sessions`: Classroom lecture sessions, duration, course code, instructor.
- `detection_events`: Frame-by-frame counts, bounding boxes, keypoints, FPS, data source.
- `transcripts`: Full text, timestamped segments, word counts, extracted keywords.
- `ocr_results`: Extracted text, confidence scores, text box coordinates.
- `nlp_results`: Curriculum topics, extractive summaries, concept tags.
- `reports`: Generated PDF / Excel files and download paths.
- `dataset_records`: Inventory of Kaggle and Synthetic datasets.
- `model_records`: Registry of loaded models and execution status.


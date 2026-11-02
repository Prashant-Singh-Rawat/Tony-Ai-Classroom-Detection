# Phase 0: Existing Reusable Components & Architecture Inspection Report

**Project**: ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Task**: Two Independent Video Processing Modes  
**Phase**: Phase 0 — Comprehensive Inspection & Architecture Mapping  
**Date**: November 2, 2026  
**Hardware Target**: NVIDIA GeForce GTX 1650 (4GB VRAM) / Intel CPU / Windows 11  

---

## 1. Executive Summary

ClassVision AI currently possesses a rich foundation of production-ready machine learning services, vector stores, ORM models, and frontend interfaces. Rather than building from scratch or using brittle workarounds, this report identifies the exact existing components that will be reused, describes how audio and visual text will be extracted from video inputs without an audio-upload option, and outlines a memory-efficient architectural design tailored to the 4GB VRAM hardware constraint.

Strict ethical boundaries are preserved:
- Zero facial recognition, zero biometric profiling, zero emotion/attention scoring.
- Purely observable body poses and curriculum lecture content.

---

## 2. Reusable Existing Components

### A. Speech Transcription (`backend/app/services/speech/service.py`)
- **Engine**: `faster-whisper` (v1.2.1) wrapping CTranslate2.
- **Model**: `tiny` model executed on **CPU with `int8` quantization**.
- **Capabilities**:
  - Extracts word and segment-level timestamps (`start`, `end`, `text`).
  - Detects spoken language and language confidence probability.
  - Generates transcript duration and word count.
  - Built-in term-frequency keyword extraction.
- **VRAM Footprint**: **0 MB VRAM** (runs entirely in RAM on CPU), preventing GPU out-of-memory conflicts with YOLO models.
- **Current Status**: Verified and active (`SpeechService.transcribe`). Tested via `test_speech_and_ocr_endpoints.py`.

### B. Internal Video Audio Extraction (FFmpeg / PyAV)
- **Library**: `av` (PyAV v19.0.2).
- **Capabilities**: Directly links to FFmpeg's `libavformat`, `libavcodec`, `libswresample`, and `libavutil`.
- **Function**: Automatically demuxes video files (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`) and extracts the audio stream into 16kHz mono PCM WAV required by Faster-Whisper.
- **User Experience**: The user provides *only* a video file. No audio upload option is exposed.

### C. Whiteboard & Slide OCR (`backend/app/services/ocr/service.py`)
- **Engine**: `easyocr` (v1.7.2).
- **Execution**: Configured with `gpu=False` (CPU mode), keeping the GTX 1650's 4GB VRAM free.
- **Capabilities**:
  - Extracts text blocks, bounding coordinates `[[x1,y1],[x2,y2],[x3,y3],[x4,y4]]`, confidence scores per block, and overall average confidence.
  - Distinguishes whiteboard handwriting and projected slides.
- **Frame Selection Strategy**:
  - To prevent processing hundreds of redundant frames, frames will be sampled at dynamic intervals (e.g., scene-change keyframes or every 4–6 seconds where mean pixel difference $> \tau$).
  - OCR results preserve the exact video frame timestamp ($t$ in seconds).

### D. NLP & Topic Extraction (`backend/app/services/nlp/service.py`)
- **Engine**: `sentence-transformers` (v6.2.0) with `all-MiniLM-L6-v2` (384-dimensional embeddings on CPU) and extractive scoring.
- **Existing Functions**:
  - `extract_keywords`: Frequency and position-weighted academic term extraction.
  - `identify_topics`: Cosine similarity matching against academic curriculum taxonomies.
  - `summarize_lecture`: Extractive sentence scoring for content summaries.
- **Enhancement Needed**: Structured topic hierarchy generator (Subject, Main Topics, Subtopics, Timestamps, Linked Transcript Segments, Linked OCR Text, Definitions, Formulas, Key Points, Q&A).

### E. Vector Store & RAG Assistant (`backend/app/services/rag/service.py`)
- **Vector Database**: `chromadb` (v1.5.9) PersistentClient stored at `data/chroma/`.
- **Embedder**: `SentenceTransformer("all-MiniLM-L6-v2", device="cpu")`.
- **Existing Functions**:
  - `ingest_lecture`: Chunks transcript segments and whiteboard OCR notes with timestamped metadata (`session_id`, `source_type`, `title`, `timestamp`).
  - `query`: Hybrid vector retrieval with educational honesty filters (refuses questions when retrieval similarity $< 0.35$).
- **API Endpoint**: `POST /api/rag/query` linked to the "Ask ClassVision" page.

### F. Document & Report Exporters (`backend/app/services/reports/generator.py`)
- **Libraries**:
  - `reportlab` (v4.4.10): High-quality PDF document layout, typography, tables, and headers.
  - `python-docx` (v1.2.0): Clean Microsoft Word document generation.
  - Plain Text (`.txt`): Lightweight markdown/text export.
- **Existing Functions**: `ReportGenerator.generate_pdf_session_report` generates publication-quality PDF documents.

### G. Database & ORM (`backend/app/database/models.py`)
- **Database**: SQLite (`backend/app/database/classroom.db`) with SQLAlchemy ORM.
- **Existing Tables**:
  - `Session`: Session metadata, instructor, course code, status, data provenance.
  - `Transcript`: Segments, full text, duration, language, word count.
  - `OcrResult`: Extracted text, bounding blocks, overall confidence.
  - `NlpResult`: Keywords, topics, summary.
  - `RagDocument`: Chunk index, content, Chroma document ID.
  - `ProcessingResult`: Async job status tracking (`pending`, `processing`, `completed`, `failed`), processing time, errors.

### H. Computer Vision Pipeline (Option 1: Classroom Activity & Gesture Detection)
- **Status**: **Fully working and preserved**.
- **Components**:
  - `backend/app/services/computer_vision/`: YOLOv8 person detection, 17-keypoint COCO pose estimation.
  - `backend/app/services/tracking/`: ByteTrack anonymous ID tracking.
  - `backend/app/services/activity_recognition/`: 6-color activity classification (Green: Facing board, Blue: Hand raised, Red: Phone visible, Yellow: Head down, Orange: Turned sideways, Gray: Needs review).
  - `frontend/src/pages/MonitoringPage.tsx`: Exact aspect-ratio sizing, overlay synchronization, telemetry bar, live webcam, and video file inference.
- **Guarantee**: This pipeline will remain completely untouched and isolated from the lecture notes pipeline.

---

## 3. Architecture for Option 2: AI Lecture Notes & Summary

```
                      +---------------------------------------+
                      |       Uploaded Lecture Video          |
                      |  (.mp4, .mov, .avi, .mkv, .webm)      |
                      +-------------------+-------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
             [ PyAV Audio Extraction ]           [ OpenCV Frame Sampler ]
             - Demuxes audio stream              - Scene-change detector
             - Converts to 16kHz WAV mono        - Keyframe extraction
                        |                                   |
                        v                                   v
             [ Faster-Whisper (CPU) ]             [ EasyOCR (CPU) ]
             - Teacher speech transcript         - Blackboard & slide text
             - Timestamps & confidence           - Bounding boxes & confidence
                        |                                   |
                        +-----------------+-----------------+
                                          |
                                          v
                              [ Multimodal NLP Fusion ]
                              - Aligns OCR with transcript timestamps
                              - Identifies subjects, topics & subtopics
                              - Extracts definitions, formulas & points
                              - Generates structured study notes & revision
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
                    v                     v                     v
            [ ChromaDB RAG ]       [ SQLite DB ]        [ Exporters ]
            - Transcript chunks    - Sessions           - PDF (ReportLab)
            - OCR text blocks      - Notes & summaries  - DOCX (python-docx)
            - Ask ClassVision Q&A  - Job status         - TXT (Markdown)
```

---

## 4. Hardware Optimization (GTX 1650 4GB VRAM)

1. **Zero VRAM Bloat for Lecture Notes**:
   - Both Faster-Whisper (`tiny` int8) and EasyOCR run on **CPU**.
   - Sentence-Transformers (`all-MiniLM-L6-v2`) runs on **CPU**.
   - ChromaDB runs in-memory / disk with CPU cosine similarity.
   - The entire 4GB GPU VRAM remains dedicated to Option 1 (YOLOv8 & OpenCV) if running concurrently.
2. **Asynchronous Background Job Execution**:
   - Lecture video processing executes via background tasks (`BackgroundTasks` or threading).
   - The FastAPI event loop remains responsive and never blocks.
   - Polling endpoint (`GET /api/lecture-notes/status/{job_id}`) provides real-time progress percentages and stage updates (`extracting_audio`, `transcribing`, `extracting_frames`, `running_ocr`, `generating_notes`, `completed`).
3. **Smart Video Frame Sampling**:
   - Rather than processing 30 frames per second (which would mean 1,800 frames per minute), the sampler samples 1 frame every 4–6 seconds or when significant structural difference occurs ($\Delta \text{frame} > \text{threshold}$). A 10-minute lecture analyzes only ~100–120 frames, completing OCR in seconds on CPU.

---

## 5. UI Architecture: Two Independent Options

In the frontend, students and instructors will see two prominent, distinct cards:

1. **Card 1: Classroom Activity & Gesture Detection**
   - *Description*: Analyze classroom videos to detect people, poses, hand raises, and observable classroom activities.
   - *Action*: Navigates to `/live` (the existing, verified monitoring workflow with YOLOv8 bounding boxes, skeletons, and telemetry).

2. **Card 2: AI Lecture Notes & Summary**
   - *Description*: Extract teacher explanations, board content, slides, and important topics from lecture videos to generate organized student notes.
   - *Action*: Navigates to dedicated `/lecture-notes` workflow accepting video uploads (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`).
   - *No Audio Upload*: Strictly video-only input.

### Lecture Notes Results Page Layout
- **Lecture Overview**: Video metadata, duration, detected language, subject, processing metrics.
- **Topics & Subtopics**: Interactive timeline navigation with start/end timestamps.
- **Searchable Transcript**: Timestamped teacher speech segments with confidence tags.
- **Visual Board Text**: OCR extractions with frame preview thumbnails and timestamps.
- **Generated Study Notes**: Complete 14-section structured notes (title, overview, topics, explanations, definitions, formulas, key takeaways, revision sheet, Q&A).
- **Summary Modes**: Tabbed selector for Full Summary, Short Summary, Topic-wise Summary, Quick Revision Sheet.
- **Export Bar**: One-click download for PDF, DOCX, and TXT.
- **Curriculum Q&A**: "Ask ClassVision" embedded drawer with evidence snippets and timestamps.


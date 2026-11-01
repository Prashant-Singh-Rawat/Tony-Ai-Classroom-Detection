# ClassVision AI — Backend Architecture & API Specification
**Phase 1.0 — FastAPI Backend Foundation**

---

## 1. Executive Summary & Purpose

The ClassVision AI backend is a modular, high-throughput asynchronous API built with **FastAPI**, **Pydantic v2**, and **Starlette**. It serves as the central nervous system connecting:
- Real-time video frame processing & Computer Vision pipelines (YOLOv8 & MediaPipe Pose)
- Audio transcription pipelines (`faster-whisper`)
- Slide & blackboard text extraction (`EasyOCR`)
- Curriculum and lecture search via Retrieval-Augmented Generation (`ChromaDB`)
- The React 19 + TypeScript + Vite + Tailwind CSS frontend dashboard

The Phase 1.0 backend is designed according to **honest data handling principles**: when models or physical hardware are not connected, the API explicitly returns calibrated status indicators (`DEMO_DATA`, `NOT_CONNECTED`, `NOT_AVAILABLE`) rather than fabricated predictions or unverified claims.

---

## 2. Architecture & Directory Layout

The backend adopts a decoupled, layered architecture:

```
backend/
├── requirements.txt            # Python dependencies for FastAPI backend
├── app/
│   ├── __init__.py             # Exports ASGI app
│   ├── main.py                 # FastAPI application factory & lifecycle management
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic BaseSettings, environment & YAML loader
│   │   └── cors.py             # Cross-Origin Resource Sharing middleware
│   ├── schemas/                # Strongly-typed Pydantic response/request models
│   │   ├── __init__.py
│   │   ├── common.py           # HandRaiseClass & DataStatus enums
│   │   ├── detections.py       # BoundingBox & WebSocket messages
│   │   ├── sessions.py         # SessionInfo schema
│   │   ├── dashboard.py        # DashboardSummary & DashboardStats
│   │   ├── analytics.py        # AnalyticsData, TimeSeries, Distribution
│   │   ├── intelligence.py     # LectureIntelligenceData, Transcripts, OCR notes
│   │   ├── rag.py              # RagQueryRequest & RagResponse
│   │   ├── reports.py          # ReportItem & ModelQualityReport
│   │   ├── models.py           # ModelStatusData, Kaggle & Real Dataset statuses
│   │   ├── settings.py         # CameraSettings, PrivacySettings, AiModulesSettings
│   │   └── system.py           # SystemStatus schema
│   ├── services/               # Domain business logic & AI subsystem wrappers
│   │   ├── __init__.py
│   │   ├── computer_vision/    # CV service interface (NOT CONNECTED in Phase 1.0)
│   │   ├── speech/             # Whisper service interface (NOT CONNECTED in Phase 1.0)
│   │   ├── ocr/                # Whiteboard OCR service interface (NOT CONNECTED in Phase 1.0)
│   │   ├── nlp/                # NLP topic & sentiment interface (NOT CONNECTED in Phase 1.0)
│   │   ├── rag/                # RAG assistant service (Demo fallback or NOT CONNECTED)
│   │   ├── analytics/          # Metric aggregation & verified repo snapshots
│   │   └── database/           # Session repository & metadata parser
│   └── api/
│       ├── __init__.py
│       ├── api_router.py       # Master router aggregating all domain sub-routers
│       └── routes/
│           ├── __init__.py
│           ├── health.py       # GET /health
│           ├── dashboard.py    # GET /api/dashboard/summary
│           ├── sessions.py     # GET /api/sessions & GET /api/sessions/{session_id}
│           ├── analytics.py    # GET /api/analytics
│           ├── intelligence.py # GET /api/intelligence/{session_id}
│           ├── rag.py          # POST /api/rag/query
│           ├── reports.py      # GET /api/reports
│           ├── models.py       # GET /api/model/status
│           ├── settings.py     # GET /api/settings
│           ├── system.py       # GET /api/system/status
│           └── websocket.py    # WebSocket /api/ws/detections
```

---

## 3. Implemented API Endpoints

All endpoints conform strictly to the TypeScript interfaces in `frontend/src/types/index.ts`.

| Method | Path | Description | Response Schema | Phase 1.0 Status |
|---|---|---|---|---|
| `GET` | `/health` | Core health check (Gate condition) | `{"status": "ok", ...}` | **REAL** |
| `GET` | `/api/dashboard/summary` | Live metric cards, active session, timeline | `DashboardSummary` | **DEMO_DATA / REAL** |
| `GET` | `/api/sessions` | List recorded or active classroom sessions | `List[SessionInfo]` | **DEMO_DATA / REAL** |
| `GET` | `/api/sessions/{session_id}` | Detailed session metadata and engagement | `SessionInfo` (or 404) | **DEMO_DATA / REAL** |
| `GET` | `/api/analytics` | Participation trends and activity distribution | `AnalyticsData` | **DEMO_DATA / REAL** |
| `GET` | `/api/intelligence/{session_id}` | Fused speech transcript and whiteboard OCR notes | `LectureIntelligenceData` | **DEMO_DATA / REAL** |
| `POST` | `/api/rag/query` | Natural language Q&A over lecture content | `RagResponse` | **DEMO_DATA / NOT_CONNECTED** |
| `GET` | `/api/reports` | Downloadable summaries and model audit | `ReportsResponse` | **DEMO_DATA / REAL** |
| `GET` | `/api/model/status` | Verified repository ground-truth audit | `ModelStatusData` | **REAL** |
| `GET` | `/api/settings` | Camera, offline privacy, retention config | `SettingsData` | **REAL** |
| `GET` | `/api/system/status` | Server runtime status and data root | `SystemStatus` | **REAL** |
| `WS` | `/api/ws/detections` | Real-time streaming bounding boxes | `WebSocketDetectionMessage`| **DEMO_DATA / REAL** |

---

## 4. Request and Response Formats

### 4.1 Health Check (`GET /health`)
**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8000
```
**Response (200 OK):**
```json
{
  "status": "ok",
  "app": "ClassVision AI",
  "version": "1.0.0",
  "phase": "Phase 1.0 - Backend Foundation",
  "pipeline_mode": "DEMO",
  "timestamp": "2026-10-30T09:16:37.020323+00:00"
}
```

### 4.2 Dashboard Summary (`GET /api/dashboard/summary`)
**Parameters:**
- `demo` (optional, boolean): If `true`, returns demonstration metrics. If `false`, returns unpopulated live hardware structure. Defaults to `settings.is_demo_mode`.

**Response (200 OK):**
```json
{
  "currentSession": {
    "sessionId": "sess_01",
    "title": "CS402: Convolutional Neural Networks & Optimization",
    "courseCode": "CS402",
    "date": "2026-10-12",
    "startTime": "09:15 AM",
    "durationMinutes": 45,
    "classroom": "Lecture Hall 302",
    "instructor": "Dr. A. Sharma",
    "status": "active",
    "totalStudents": 28,
    "activeHandRaises": 4,
    "totalHandRaiseEvents": 19,
    "averageEngagement": 86.4,
    "privacyProtected": true
  },
  "stats": {
    "totalPeopleDetected": 28,
    "activeHandRaises": 4,
    "handRaisePercentage": 14.3,
    "engagementScore": 86.0,
    "activeCameras": 1,
    "privacyModeActive": true,
    "systemMode": "demo"
  },
  "recentSessions": [...],
  "activityTimeline": [
    { "time": "09:15", "handRaises": 0, "attentiveStudents": 27, "ambiguousCount": 1 },
    { "time": "09:20", "handRaises": 1, "attentiveStudents": 26, "ambiguousCount": 1 }
  ],
  "isDemoData": true
}
```

### 4.3 RAG Assistant Query (`POST /api/rag/query`)
**Request:**
```json
{
  "query": "Did students ask questions regarding dilated convolution?",
  "session_id": "sess_01",
  "live": false
}
```
**Response when in Demonstration Mode (200 OK):**
```json
{
  "query": "Did students ask questions regarding dilated convolution?",
  "answer": "Yes, at timestamp 09:30:18, a student in the front row raised a hand to ask whether dilated convolutions preserve spatial resolution without downsampling...",
  "confidence": 0.95,
  "sources": [
    {
      "title": "Gesture Timeline & Transcript Synchrony",
      "sourceType": "transcript",
      "timestamp": "09:30:18",
      "snippet": "Student 1: \"Professor, does dilated convolution preserve spatial dimensions...?\""
    }
  ],
  "isPlaceholder": true,
  "isDemoData": true,
  "status": "DEMO_DATA"
}
```

**Response when `live: true` (Honest NOT_CONNECTED state):**
```json
{
  "query": "Did students ask questions regarding dilated convolution?",
  "answer": "RAG vector store is NOT CONNECTED. No language model or document index is available in Phase 1.0.",
  "confidence": 0.0,
  "sources": [],
  "isPlaceholder": true,
  "isDemoData": false,
  "status": "NOT_CONNECTED"
}
```

### 4.4 Model & Dataset Ground-Truth Audit (`GET /api/model/status`)
**Response (200 OK):**
```json
{
  "modelCheckpointsCount": 0,
  "activeCheckpoint": "None",
  "trainingStatus": "NOT_STARTED",
  "kaggleGestureDataset": {
    "totalImages": 24000,
    "trainImages": 18000,
    "testImages": 6000,
    "classes": 20,
    "semanticsVerified": false,
    "disclaimer": "Isolated hand gesture benchmark; does not represent classroom hand-raise detection"
  },
  "realClassroomDataset": {
    "collectedVideos": 0,
    "extractedFrames": 0,
    "annotationsCount": 0,
    "targetPlan": "Collection starts post 12 October 2026 upon college reopening"
  },
  "evaluationMetrics": {
    "precision": "Unavailable, no model trained",
    "recall": "Unavailable, no model trained",
    "f1Score": "Unavailable, no model trained",
    "map50": "Unavailable, no model trained",
    "status": "NOT CONNECTED"
  },
  "verifiedTests": {
    "passed": 60,
    "total": 60,
    "status": "ALL_PASSING"
  }
}
```

### 4.5 Real-Time Detection WebSocket (`ws://localhost:8000/api/ws/detections`)
**Frame message emitted to client:**
```json
{
  "type": "detections",
  "sessionId": "sess_01",
  "timestamp": "2026-10-30T09:16:37.020323+00:00",
  "detections": [
    {
      "id": "box_01",
      "personId": 1,
      "classId": 0,
      "className": "hand_raised",
      "confidence": 0.94,
      "x": 18.0,
      "y": 28.0,
      "w": 14.0,
      "h": 42.0
    }
  ],
  "status": "DEMO_DATA"
}
```

---

## 5. Frontend Integration Architecture

1. **Base URL Alignment**:
   The frontend service in `frontend/src/services/api.ts` targets `API_CONFIG.baseUrl = http://localhost:8000/api`.
2. **CORS Protocol**:
   The backend middleware (`backend/app/core/cors.py`) allows origins from the local Vite development servers (`http://localhost:5173`, `http://127.0.0.1:5173`) with full support for credential passing and preflight `OPTIONS` requests.
3. **CamelCase Serialization**:
   All Pydantic models inherit from `CamelModel` (`backend/app/schemas/common.py`), ensuring that JSON attributes serialize as `sessionId`, `personId`, `isDemoData`, and `averageEngagement` directly matching TypeScript expectations without client-side key translation.
4. **Transition from Demo Mode**:
   The React frontend defaults to `DemoClassVisionApi` (self-contained mock telemetry). To switch the frontend to connect directly to the running FastAPI server:
   ```bash
   # In frontend/.env or terminal:
   VITE_USE_DEMO_DATA=false
   VITE_BACKEND_URL=http://localhost:8000/api
   ```
   When set to `false`, the frontend initializes `RealClassVisionApi` to make real network requests to FastAPI.

---

## 6. Environment Variables

All settings can be configured via a `.env` file at the repository root or standard environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_HOST` | `0.0.0.0` | Host IP interface to bind Uvicorn |
| `BACKEND_PORT` | `8000` | Port for the FastAPI server |
| `PIPELINE_MODE` | `DEMO` | `DEMO` (low latency, demo fallback) or `ACCURACY` (strict evaluation) |
| `CLASSVISION_REAL_DATA_ROOT` | `datasets/real_classroom` | Un-synced storage directory for real footage and annotations |
| `BLUR_FACES_OVERRIDE` | `null` | Overrides `config/retention.yaml` face blurring setting |
| `MODEL_REGISTRY_PATH` | `classvision-ai/models/model_registry.json` | Path to the model registry JSON file |
| `LOG_LEVEL` | `INFO` | Server logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 7. How to Start the Backend

### Standard Development Server (with Auto-Reload)
From the repository root (`Tony-Ai-Classroom-Detection`):
```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or from within the `classvision-ai/` subfolder:
```powershell
cd classvision-ai
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive API Documentation
Once running, the interactive Swagger UI and ReDoc documentation are available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 8. Future AI Module Integration Plan

Each domain module in `backend/app/services/` provides a pluggable interface ready for future phases:

1. **Phase 2 — Vision: Person Detection**:
   - Install `ultralytics`.
   - Update `backend/app/services/computer_vision/service.py` to load `yolov8n.pt`.
   - Implement `cv_service.process_frame()` returning person bounding boxes.
2. **Phase 3 — Vision: Hand-Raise Detection**:
   - Fine-tune YOLOv8 on real classroom annotations (`0: hand_raised`, `1: hand_not_raised`).
   - Register checkpoint in `classvision-ai/models/model_registry.json`.
3. **Phase 4 — Vision: Pose Keypoints**:
   - Integrate `mediapipe.solutions.pose` for skeletal keypoints.
4. **Phase 5 — Audio: Speech Recognition**:
   - Integrate `faster_whisper.WhisperModel("base")`.
   - Implement `speech_service.transcribe()` on 30-second lecture audio chunks.
5. **Phase 6 — Board: Whiteboard OCR**:
   - Integrate `easyocr.Reader(['en'])`.
   - Implement `ocr_service.extract_text()` with contrast pre-processing.
6. **Phase 9 — RAG Engine**:
   - Ingest syllabi and lecture transcripts into a local `chromadb` collection.
   - Update `rag_service.query()` to perform dense vector similarity search and feed context to a quantized local LLM.


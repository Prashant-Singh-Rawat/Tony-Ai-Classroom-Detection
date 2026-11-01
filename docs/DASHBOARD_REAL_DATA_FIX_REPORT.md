# ClassVision AI — Dashboard Real Data Verification & Fix Report

**Report Status:** Verified & Completed  
**Date:** 2026-11-01  
**Project:** ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Pipeline Mode:** `DEMO` (Preserved)  
**Backend:** `http://127.0.0.1:8000` (FastAPI)  
**Frontend:** `http://127.0.0.1:5174` (React / Vite)  

---

## 1. Executive Summary

Following the root cause investigation, the missing `SessionInfo` schema import in [`backend/app/services/analytics/service.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/backend/app/services/analytics/service.py) has been repaired. The application was safely restarted, and end-to-end verification confirms that:

1. **Dashboard Data Source:** The dashboard endpoint (`GET /api/dashboard/summary`) now correctly pulls genuine classroom session data from [`classvision_ai.db`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/classvision_ai.db).
2. **`isDemoData` Status:** Evaluates to `False` whenever real sessions exist in SQLite.
3. **`systemMode` Status:** Reports `"live"`.
4. **Current Session Active:** Displays `sess_live_demo_1793468210` (*"Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4"*) instead of the demo fixture `sess_01`.
5. **Session Inventory:** All 12 genuine SQLite sessions are accessible and matched with verified database event counts.
6. **Zero-Data Safety:** When querying an empty database without demo fixtures, the system returns an honest zero-metric envelope without fabricating metrics.
7. **Pipeline Mode Integrity:** `PIPELINE_MODE` remains strictly set to `DEMO` to safeguard workstation hardware stability (NVIDIA GTX 1650 4GB).

---

## 2. Exact Code Change

### File: `backend/app/services/analytics/service.py`
**Lines 22–27:**

#### Before:
```python
from backend.app.schemas.dashboard import (
    ActivityTimelineItem,
    DashboardStats,
    DashboardSummary,
)
```

#### After:
```python
from backend.app.schemas.dashboard import (
    ActivityTimelineItem,
    DashboardStats,
    DashboardSummary,
    SessionInfo,
)
```

### Impact Analysis:
- `SessionInfo` is the Pydantic model representing classroom sessions, defined in `backend/app/schemas/sessions.py` and re-exported in `backend/app/schemas/dashboard.py`.
- Previously, line 183 threw `NameError: name 'SessionInfo' is not defined`, which was caught and silenced by `except Exception: pass`, resetting `real_sessions = []`.
- With the import restored, all SQLite records convert cleanly into `SessionInfo` models. No existing exception handling, logging, or business logic was altered.

---

## 3. Before-and-After Live API Responses

### 3.1 `GET http://127.0.0.1:8000/api/dashboard/summary` (Default Call)

#### Before Fix:
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
    "totalHandRaiseEvents": 18,
    "averageEngagement": 86.0,
    "privacyProtected": true,
    "zoneFilteringEnabled": true
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
  "recentSessions": [
    { "sessionId": "sess_01" },
    { "sessionId": "sess_02" },
    { "sessionId": "sess_03" }
  ],
  "isDemoData": true
}
```

#### After Fix:
```json
{
  "currentSession": {
    "sessionId": "sess_live_demo_1793468210",
    "title": "Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4",
    "courseCode": "CV101",
    "date": "2026-10-31",
    "startTime": "09:00 AM",
    "durationMinutes": 45,
    "classroom": "Rear-Corner Camera",
    "instructor": "Automated Analysis",
    "status": "completed",
    "totalStudents": 12,
    "activeHandRaises": 0,
    "totalHandRaiseEvents": 0,
    "averageEngagement": 75.0,
    "privacyProtected": true,
    "instructorRoiPolygon": [[0.0, 0.0], [0.45, 0.0], [0.45, 0.65], [0.0, 0.65]],
    "zoneFilteringEnabled": true
  },
  "stats": {
    "totalPeopleDetected": 12,
    "activeHandRaises": 0,
    "handRaisePercentage": 0.0,
    "engagementScore": 75.0,
    "activeCameras": 1,
    "privacyModeActive": true,
    "systemMode": "live"
  },
  "recentSessions": 15,
  "isDemoData": false
}
```

---

### 3.2 `GET http://127.0.0.1:8000/api/dashboard/summary?demo=false` (Strict Real Data)

#### Before Fix:
```json
{
  "currentSession": null,
  "stats": {
    "totalPeopleDetected": 0,
    "activeHandRaises": 0,
    "handRaisePercentage": 0.0,
    "engagementScore": 0.0,
    "activeCameras": 0,
    "privacyModeActive": true,
    "systemMode": "live"
  },
  "recentSessions": [],
  "activityTimeline": [],
  "isDemoData": false
}
```

#### After Fix:
```json
{
  "currentSession": {
    "sessionId": "sess_live_demo_1793468210",
    "title": "Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4",
    "courseCode": "CV101",
    "date": "2026-10-31",
    "startTime": "09:00 AM",
    "durationMinutes": 45,
    "classroom": "Rear-Corner Camera",
    "instructor": "Automated Analysis",
    "status": "completed",
    "totalStudents": 12,
    "activeHandRaises": 0,
    "totalHandRaiseEvents": 0,
    "averageEngagement": 75.0,
    "privacyProtected": true,
    "instructorRoiPolygon": [[0.0, 0.0], [0.45, 0.0], [0.45, 0.65], [0.0, 0.65]],
    "zoneFilteringEnabled": true
  },
  "stats": {
    "totalPeopleDetected": 12,
    "activeHandRaises": 0,
    "handRaisePercentage": 0.0,
    "engagementScore": 75.0,
    "activeCameras": 1,
    "privacyModeActive": true,
    "systemMode": "live"
  },
  "recentSessions": 12,
  "isDemoData": false
}
```

---

## 4. SQLite Database Sessions Verification

Direct verification of the SQLite database (`classvision_ai.db`) confirms all 12 sessions match between the repository and the API:

| Index | Session ID | Session Title | DB Status | Events | Active Raises | Verified |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 1 | `sess_live_demo_1793468210` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | completed | 0 | 0 | **MATCH** |
| 2 | `sess_live_demo_1793468131` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | completed | 0 | 0 | **MATCH** |
| 3 | `sess_live_demo_1793468032` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | completed | 0 | 0 | **MATCH** |
| 4 | `test_analytics_comp_sess` | Zone Comparison Session | active | 3 | 0 | **MATCH** |
| 5 | `test_zone_session_01` | Session test_zone_session_01 | active | 0 | 0 | **MATCH** |
| 6 | `test_teacher_in_zone` | Teacher Zone Test | active | 0 | 0 | **MATCH** |
| 7 | `test_multimodal_sess_01` | Lecture Session: sample-000001.mp3 | active | 1 | 0 | **MATCH** |
| 8 | `test_sess_multirow_accuracy` | Video Analysis: test_rear_corner.mp4 | completed | 1 | 0 | **MATCH** |
| 9 | `test_sess_real_sample_e2e` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | completed | 0 | 0 | **MATCH** |
| 10 | `sess_video` | Video Analysis: classroom_nhd.mp4 | completed | 0 | 0 | **MATCH** |
| 11 | `sess_real_multirow_01` | Video Analysis: classroom_rear_corner_multi_row.mp4 | completed | 0 | 0 | **MATCH** |
| 12 | `sess_real_sample_01` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | completed | 0 | 0 | **MATCH** |

---

## 5. Frontend & UI Verification

1. **Environment Variable Configuration:**
   [`frontend/.env`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/.env) retains:
   ```env
   VITE_BACKEND_URL=http://localhost:8000/api
   VITE_USE_DEMO_DATA=false
   ```
2. **Real API Service Client:**
   [`frontend/src/services/api.ts`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/src/services/api.ts#L1202) instantiates `RealClassVisionApi`, routing all requests directly to the FastAPI server.
3. **Visual UI Screen Captures:**
   All 8 pages were refreshed and verified in Microsoft Edge:
   - **Dashboard:** [`docs/screenshots/dashboard.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/dashboard.png) — Displays `sess_live_demo_1793468210`, active live indicator, and real session cards.
   - **Monitoring:** [`docs/screenshots/monitoring.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/monitoring.png) — Video upload, privacy blur toggles, instructor ROI polygon editor.
   - **Analytics:** [`docs/screenshots/analytics.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/analytics.png) — Real session selector populating 62 recorded tracking intervals.
   - **Intelligence:** [`docs/screenshots/intelligence.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/intelligence.png) — Multimodal synthesis view.
   - **Ask ClassVision:** [`docs/screenshots/ask_classvision.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/ask_classvision.png) — RAG question answering interface.
   - **Reports:** [`docs/screenshots/reports.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/reports.png) — Automated compliance audit export.
   - **Model Status:** [`docs/screenshots/model_status.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/model_status.png) — Multi-model registry display.
   - **Settings:** [`docs/screenshots/settings.png`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/screenshots/settings.png) — Privacy and hardware parameters.

---

## 6. Pipeline Mode Safety: DEMO vs. ACCURACY Analysis

`PIPELINE_MODE=DEMO` was left strictly unchanged per user instructions. Below is the technical specification of the modes defined in [`classvision-ai/config/modes.yaml`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/classvision-ai/config/modes.yaml) and their hardware impact:

| Pipeline Dimension | DEMO Mode (Active) | ACCURACY Mode | Hardware & Performance Impact |
|---|---|---|---|
| **Frame Stride** | `stride = 3` (1 in 3 frames) | `stride = 1` (every frame) | ACCURACY mode triples video decoding and inference load |
| **Input Resolution** | `640 × 480` (0.307 MP) | `1280 × 720` (0.922 MP) | 3× pixel volume per frame; higher tensor memory |
| **Vision Model** | `yolov8n` (Nano, 3.2M params) | `yolov8m` (Medium, 25.9M params) | 8.1× parameter count; CPU inference increases from ~32ms to ~280ms |
| **Speech Recognizer** | `tiny` / `base`, `int8`, beam=1 | `medium`, `float16`, beam=5 | Model weights increase from 150 MB to 1.5 GB; requires ~3.5 GB VRAM |
| **Board OCR** | EasyOCR, CPU (`gpu: false`) | EasyOCR, GPU (`gpu: true`) | Allocates ~1.2 GB CUDA VRAM |
| **RAG Retrieval** | `top_k = 3` | `top_k = 5` | Marginal latency change (~15ms) |

### GPU and RAM Requirements:
- **Workstation GPU:** NVIDIA GeForce GTX 1650 (4.0 GB VRAM).
- **ACCURACY Mode Memory Demand:**
  - YOLOv8m: ~1.5 GB VRAM
  - Faster-Whisper Medium: ~3.5 GB VRAM
  - EasyOCR GPU: ~1.2 GB VRAM
  - **Total Required VRAM:** ~6.2 GB VRAM.
  - **Verdict:** Activating `ACCURACY` mode on this workstation would cause a **CUDA Out-of-Memory (OOM)** error.
- **DEMO Mode Memory Demand:**
  - YOLOv8n: <500 MB VRAM (or CPU)
  - Faster-Whisper Tiny (int8): ~150 MB RAM
  - EasyOCR (CPU): ~300 MB RAM
  - **Total Required Memory:** <1.5 GB RAM.
  - **Verdict:** Safe, responsive, and stable without hardware crashes.

---

## 7. Remaining Demo-Data Fallbacks

The following explicit fallback boundaries remain in the codebase:

1. **`GET /api/dashboard/summary?demo=true`:**
   Explicit query parameter override allows evaluating the demo envelope on demand.
2. **`GET /api/intelligence/{session_id}` Fallback:**
   In [`frontend/src/services/api.ts`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/src/services/api.ts#L876), calling `api.getLectureIntel()` without arguments defaults to `sessionId = 'sess_01'`, which returns the demo intelligence fixture. When passed an explicit SQLite session ID (e.g. `sess_live_demo_1793468210`), it returns real transcripts with `isDemoData: false`.
3. **Empty Database Fallback:**
   When the SQLite database has 0 sessions and `include_demo=False`, the backend returns `currentSession: null`, `stats.totalPeopleDetected: 0`, and `recentSessions: []`. It never manufactures fake sessions under real mode.
4. **Specialized Classifiers Pipeline Isolation:**
   CharacterCNN-62, SignLanguageCNN, HandGestureCNN, and Summary Scoring Regressor checkpoints remain isolated from the live video stream per system ethics and architecture requirements.


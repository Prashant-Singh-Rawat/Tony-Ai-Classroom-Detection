# ClassVision AI — Pipeline Mode Verification & Root Cause Analysis

**Document Status:** Final Verified Architecture Analysis  
**Date:** 2026-11-01  
**Project:** ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Backend URL:** `http://127.0.0.1:8000`  
**Frontend URL:** `http://127.0.0.1:5174`  

---

## 1. Executive Summary & Core Findings

During a health check of the backend server (`GET http://127.0.0.1:8000/health`), the response indicated:
```json
{
  "status": "ok",
  "app": "ClassVision AI",
  "version": "1.0.0",
  "phase": "Phase 1.0 - Backend Foundation",
  "pipeline_mode": "DEMO",
  "timestamp": "2026-11-01T03:33:47.974324+00:00"
}
```

An exhaustive investigation across backend configuration, frontend environment variables, SQLite database storage, API route handlers, and AI model checkpoints was conducted without altering runtime configurations.

### Key Findings Summary:
1. **Cause of `"pipeline_mode": "DEMO"` in Health Check:**
   - In [`backend/app/core/config.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/backend/app/core/config.py#L64), `Settings` defines `pipeline_mode: str = Field(default="DEMO", alias="PIPELINE_MODE")`.
   - The backend looks for an environment file at `REPO_ROOT / ".env"`. No `.env` file exists at the repository root, nor was `PIPELINE_MODE` set in the shell environment. Therefore, Pydantic initializes the field to its class default: `"DEMO"`.
   - [`backend/app/api/routes/health.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/backend/app/api/routes/health.py#L22) directly mirrors `settings.pipeline_mode`.
2. **Frontend `VITE_USE_DEMO_DATA` Status:**
   - [`frontend/.env`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/.env#L2) explicitly sets `VITE_USE_DEMO_DATA=false`.
   - In [`frontend/src/services/api.ts`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/src/services/api.ts#L1198), `useDemo = import.meta.env.VITE_USE_DEMO_DATA !== 'false'`. Since `VITE_USE_DEMO_DATA` is `'false'`, `useDemo` is `false`.
   - The frontend instantiates `RealClassVisionApi`, connecting directly to `http://localhost:8000/api`. The frontend UI is **not** using client-side mock fixtures.
3. **Dashboard Data Source & SQLite Record Analysis:**
   - The SQLite database [`classvision_ai.db`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/classvision_ai.db) contains **12 genuine sessions** (including end-to-end multimodal and live demonstration sessions).
   - In [`backend/app/services/analytics/service.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/backend/app/services/analytics/service.py#L183), `get_dashboard_summary()` queries SQLite via `DBSessionRepository(db).list_all()`. However, `SessionInfo` was missing from the import list on lines 22–26 of `service.py`. This threw a `NameError: name 'SessionInfo' is not defined` inside the loop, which was caught by `except Exception: pass`. As a result, `real_sessions` was left empty (`[]`), causing `get_dashboard_summary()` to fall back to `demo_sessions[0]` (`sessionId='sess_01'`) and report `isDemoData: True`.
4. **AI Model Loading Status:**
   - **YOLOv8 Person & YOLOv8-pose:** Physical checkpoints exist on disk ([`models/yolov8n.pt`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/models/yolov8n.pt) at 6.55 MB and [`models/yolov8n-pose.pt`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/models/yolov8n-pose.pt) at 6.83 MB). They are lazy-loaded on the first vision inference call.
   - **Faster-Whisper:** Model is loaded and ready (`model_size='tiny'`, CPU device).
   - **EasyOCR:** CRNN+CRAFT reader initialized and ready.
   - **RAG Engine:** ChromaDB instance loaded with status `DataStatus.READY`.
   - **Specialized Classifiers:** CharacterCNN-62, SignLanguageCNN, HandGestureCNN, and CommonLit Regressor checkpoints exist on disk and remain decoupled from the live stream per architecture guidelines.
5. **Intentionality of DEMO Mode:**
   - `DEMO` mode is **intentional by design** from Phase 0 and Phase 1 specifications ([`docs/backend_architecture.md`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/backend_architecture.md#L288) and [`classvision-ai/config/modes.yaml`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/classvision-ai/config/modes.yaml#L12)).
   - It acts as a safe, low-latency default designed for live presentations and environments with low VRAM (e.g. GTX 1650 4GB), preventing out-of-memory errors on initial startup.

---

## 2. Backend Configuration Inspection

### 2.1 Pydantic BaseSettings Definition
In [`backend/app/core/config.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/backend/app/core/config.py#L50-L106):
```python
class Settings(BaseSettings):
    """ClassVision AI backend configuration settings."""

    # Project metadata
    app_name: str = "ClassVision AI"
    app_version: str = "1.0.0"
    phase: str = "Phase 1.0 - Backend Foundation"

    # Server binding
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    secret_key: str = Field(default="dev-secret-key-classvision-ai", alias="SECRET_KEY")

    # Pipeline operational mode: DEMO or ACCURACY
    pipeline_mode: str = Field(default="DEMO", alias="PIPELINE_MODE")

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_demo_mode(self) -> bool:
        """Returns True if the backend is configured in DEMO mode."""
        return self.pipeline_mode.upper() == "DEMO"
```

### 2.2 Environment File Search Results
A filesystem scan for `.env*` files across the workspace revealed:
- `classvision-ai\.env.example`
- `frontend\.env`
- **Result:** No root `.env` file exists at `C:\Users\prash\OneDrive\Documents\Desktop\Tony-Ai-Classroom-Detection\.env`.

Because no root `.env` exists and no `PIPELINE_MODE` system environment variable was supplied during process launch, Pydantic assigned `pipeline_mode = "DEMO"`.

### 2.3 Health Route Emission
In [`backend/app/api/routes/health.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/backend/app/api/routes/health.py#L16-L25):
```python
@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        phase=settings.phase,
        pipeline_mode=settings.pipeline_mode,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
```
The health endpoint directly emits `settings.pipeline_mode`.

---

## 3. Frontend Environment & Mode Determination

### 3.1 Frontend Environment Configuration
[`frontend/.env`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/.env) contains:
```env
VITE_BACKEND_URL=http://localhost:8000/api
VITE_USE_DEMO_DATA=false
```

### 3.2 Service Factory Verification
In [`frontend/src/services/api.ts`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/src/services/api.ts#L1193-L1203):
```typescript
export function createClassVisionApi(): ClassVisionApi {
  const useDemo = import.meta.env.VITE_USE_DEMO_DATA !== 'false'
  if (useDemo) {
    return new DemoClassVisionApi()
  }
  return new RealClassVisionApi()
}
export const api = createClassVisionApi()
```
Since `VITE_USE_DEMO_DATA` is `'false'`, `useDemo` evaluates to `false`. The frontend instantiates `RealClassVisionApi()`.

### 3.3 UI Status Indicators
In [`frontend/src/components/Topbar.tsx`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/src/components/Topbar.tsx#L12) and [`frontend/src/components/Layout.tsx`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/src/components/Layout.tsx#L64):
```typescript
const isRealMode = import.meta.env.VITE_USE_DEMO_DATA === 'false'
```
The UI displays `VITE_USE_DEMO_DATA = FALSE` and routes all telemetry requests to the live backend.

---

## 4. Dashboard Data Source & SQLite Record Analysis

### 4.1 SQLite Database Inventory
Inspection of [`classvision_ai.db`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/classvision_ai.db) via SQLAlchemy shows **12 real sessions**:

| Session ID | Title / Source Video | Total Hand-Raise Events | Unique Tracks |
|---|---|:---:|:---:|
| `sess_live_demo_1793468210` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | 0 | 0 |
| `sess_live_demo_1793468131` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | 0 | 0 |
| `sess_live_demo_1793468032` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | 0 | 0 |
| `test_analytics_comp_sess` | Zone Comparison Session | 3 | 0 |
| `test_zone_session_01` | Session test_zone_session_01 | 0 | 0 |
| `test_teacher_in_zone` | Teacher Zone Test | 0 | 0 |
| `test_multimodal_sess_01` | Lecture Session: sample-000001.mp3 | 1 | 0 |
| `test_sess_multirow_accuracy` | Video Analysis: test_rear_corner.mp4 | 1 | 0 |
| `test_sess_real_sample_e2e` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | 0 | 0 |
| `sess_video` | Video Analysis: classroom_nhd.mp4 | 0 | 0 |
| `sess_real_multirow_01` | Video Analysis: classroom_rear_corner_multi_row.mp4 | 0 | 0 |
| `sess_real_sample_01` | Video Analysis: ClassVision_Sample_Classroom_Test_Compatible.mp4 | 0 | 0 |

### 4.2 Root Cause of Dashboard Falling Back to Demo Fixtures
In [`backend/app/services/analytics/service.py`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/backend/app/services/analytics/service.py#L22-L26):
```python
from backend.app.schemas.dashboard import (
    ActivityTimelineItem,
    DashboardStats,
    DashboardSummary,
)
```
Notice that `SessionInfo` was omitted from the import statement.

On line 183 of `service.py`:
```python
        real_sessions: List[SessionInfo] = []
        try:
            dbrepo = DBSessionRepository(db)
            hrepo = HandRaiseEventRepository(db)
            db_sessions = dbrepo.list_all()
            for dbs in db_sessions:
                ...
                real_sessions.append(
                    SessionInfo(
                        sessionId=dbs.id,
                        ...
                    )
                )
        except Exception:
            pass
```

When Python executed `SessionInfo(...)`, it raised:
`NameError: name 'SessionInfo' is not defined`
The broad `except Exception: pass` swallowed the error, leaving `real_sessions = []`.

Consequently, on lines 253–278:
```python
active_current = real_sessions[0] if real_sessions else (demo_sessions[0] if demo_sessions else None)
return DashboardSummary(
    currentSession=active_current, # Falls back to demo_sessions[0] ('sess_01')
    ...
    isDemoData=False if real_sessions else True, # Evaluates to True
)
```
This single missing import in `service.py` is why `/api/dashboard/summary` returned `isDemoData: True` and displayed the fixture session `sess_01` despite 12 real sessions residing in SQLite.

---

## 5. Actual AI Model Loading Status

| Model Name | Task / Modality | Checkpoint Location | File Size | Memory / Runtime State |
|---|---|---|:---:|---|
| **YOLOv8n Person** | Bounding box person detection | [`models/yolov8n.pt`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/models/yolov8n.pt) | 6.55 MB | Lazy-loaded on demand via `_get_yolo()` |
| **YOLOv8n-pose** | 17 COCO keypoints + hand raise geometry | [`models/yolov8n-pose.pt`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/models/yolov8n-pose.pt) | 6.83 MB | Lazy-loaded on demand via `_get_pose()` |
| **Faster-Whisper** | Audio transcription & keyword extraction | `Systran/faster-whisper-tiny` | HuggingFace cache | Pre-loaded in memory (`tiny`, CPU device) |
| **EasyOCR** | Whiteboard and slide text OCR | EasyOCR CRAFT + CRNN | Torch cache | Pre-loaded in memory (`reader` initialized) |
| **ChromaDB RAG** | Curriculum document retrieval | Local vector store | Persisted | Initialized (`status: DataStatus.READY`) |
| **CharacterCNN-62** | 62-class alphanumeric recognition | `models/checkpoints/character_recognition/best_character_cnn.pth` | 7.64 MB | Trained; isolated from live stream |
| **SignLanguageCNN** | 24-class ASL alphabet | `models/checkpoints/sign_language/best_sign_language_cnn.pth` | 1.71 MB | Trained; isolated from live stream |
| **HandGestureCNN** | 20-class numerical gesture | `models/checkpoints/hand_gesture/best_gesture_cnn.pth` | 4.82 MB | Trained; isolated from live stream |
| **Summary Regressor** | Content & wording rubric scoring | `models/checkpoints/summary_scoring/summary_regressor.joblib` | 0.28 MB | Trained; isolated from live stream |

All 8 models are accounted for in [`models/model_registry.json`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/models/model_registry.json) and verifiable via `GET /api/model/registry`.

---

## 6. Live API Responses Inspection

Verification was executed via live HTTP calls against the running backend server:

### 6.1 `GET /health`
```json
{
  "status": "ok",
  "app": "ClassVision AI",
  "version": "1.0.0",
  "phase": "Phase 1.0 - Backend Foundation",
  "pipeline_mode": "DEMO",
  "timestamp": "2026-11-01T03:33:47.974324+00:00"
}
```

### 6.2 `GET /api/dashboard/summary`
```json
{
  "currentSession": {
    "sessionId": "sess_01",
    "title": "CS402: Convolutional Neural Networks & Optimization",
    "status": "active",
    "totalStudents": 28,
    "activeHandRaises": 4
  },
  "stats": {
    "totalPeopleDetected": 28,
    "activeHandRaises": 4,
    "systemMode": "demo"
  },
  "recentSessions": 3,
  "isDemoData": true
}
```

### 6.3 `GET /api/sessions/`
- Returns **15 total sessions** (12 genuine SQLite sessions + 3 baseline demo sessions when `include_demo=True`).
- When called with `?include_demo=false`, it returns strictly the 12 SQLite sessions.

### 6.4 `GET /api/intelligence/{session_id}`
- For demo session `sess_01`: Returns `isDemoData: true`.
- For real SQLite session `sess_live_demo_1793468210`: Returns `isDemoData: false` with genuine transcripts and OCR logs.

### 6.5 `GET /api/model/registry`
- Returns the complete 8-model registry with latency, mAP50, PCK, WER, and F1 scores.

---

## 7. Intentionality Analysis: DEMO Mode vs ACCURACY Mode

Is `PIPELINE_MODE=DEMO` intentional or an unintended bug?

**Conclusion:** It is **intentional by design** from Phase 0 and Phase 1 specifications.

### Evidence from Project Documentation:
1. **[`classvision-ai/config/modes.yaml`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/classvision-ai/config/modes.yaml#L7-L28):**
   ```yaml
   # Two modes are provided:
   #   DEMO     — prioritises low latency; suitable for live demonstrations.
   #   ACCURACY — prioritises quality; suitable for research evaluation.
   modes:
     DEMO:
       description: "Low-latency mode for live demonstrations. Trades accuracy for speed."
       video:
         frame_stride: 3
         input_resolution: [640, 480]
       detection:
         model_size: "yolov8n"
   ```
2. **[`docs/backend_architecture.md`](file:///C:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/docs/backend_architecture.md#L288):**
   | Variable | Default | Purpose |
   |---|---|---|
   | `PIPELINE_MODE` | `DEMO` | `DEMO` (low latency, demo fallback) or `ACCURACY` (strict evaluation) |

The default setting ensures that upon fresh installation or evaluation on constrained hardware (like the developer's GTX 1650 with 4 GB VRAM), the backend does not fail with an unhandled exception or GPU out-of-memory error.

---

## 8. Safest Protocol to Enable Real Mode

Real mode is fully supported by the codebase. To transition cleanly and safely without modifying core models or breaking regression tests:

### Step 1: Fix the Missing Import in `backend/app/services/analytics/service.py`
Add `SessionInfo` to the import list from `backend.app.schemas.dashboard`:
```python
from backend.app.schemas.dashboard import (
    ActivityTimelineItem,
    DashboardStats,
    DashboardSummary,
    SessionInfo,
)
```
This enables `real_sessions` to load cleanly from SQLite without raising `NameError`.

### Step 2: Configure `PIPELINE_MODE` in the Root `.env`
Create or update `Tony-Ai-Classroom-Detection/.env` with:
```env
PIPELINE_MODE=ACCURACY
```
Or set the environment variable prior to starting Uvicorn:
```powershell
$env:PIPELINE_MODE="ACCURACY"
```

### Step 3: Restart FastAPI Backend
Restart the backend server. `GET /health` will now report:
```json
"pipeline_mode": "ACCURACY"
```
And `GET /api/dashboard/summary` will directly render genuine SQLite sessions with `isDemoData: false` and `systemMode: "live"`.

---

## 9. Current Verification Status

- [x] Backend configuration inspected (`config.py`, environment defaults).
- [x] Cause of `pipeline_mode: "DEMO"` identified and documented.
- [x] Frontend `VITE_USE_DEMO_DATA` verified (`false`, using `RealClassVisionApi`).
- [x] SQLite database inspected (12 sessions present).
- [x] Dashboard fallback root cause diagnosed (`SessionInfo` NameError).
- [x] AI model checkpoints and in-memory status verified (all 8 models accounted for).
- [x] Dashboard, Sessions, Intelligence, and Model APIs verified live.
- [x] Intentionality established from `modes.yaml` and `backend_architecture.md`.
- [x] Safe activation protocol documented.
- [x] Running servers preserved at `http://127.0.0.1:8000` and `http://127.0.0.1:5174`.


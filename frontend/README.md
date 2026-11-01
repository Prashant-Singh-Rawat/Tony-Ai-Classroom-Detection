# ClassVision AI — Web Dashboard (Phase 0.9)

Multimodal Classroom Intelligence System — Web Dashboard Foundation.

> **Status (Phase 0.9 UI Baseline):**
> This dashboard is a complete frontend application foundation. It operates strictly with **multi-modal truth labeling**:
> - **`REAL`**: Verified repository ground truth read from `frontend/src/data/repoSnapshot.ts` (Kaggle dataset 24,000 images, 20 classes, 60/60 tests pass, 0 model checkpoints).
> - **`DEMO DATA`**: Illustrative mock telemetry and sample outputs from `frontend/src/data/demo/`.
> - **`NOT CONNECTED`**: Explicit indicator for features not yet built/connected (live inference, Whisper speech, EasyOCR, RAG assistant).
> - **Zero ML models or checkpoints** are trained or active.
> - **Zero real classroom footage** exists yet (collection begins after 12 October 2026).
> - **Zero external network requests** or CDN assets are used.
> - **No webcam / hardware camera** access is initiated.

---

## OneDrive Synchronization Notice

> ⚠️ **IMPORTANT — ONEDRIVE SYNC PERFORMANCE & DATA PRIVACY**
>
> 1. **`node_modules/` Sync Overhead:**
>    Because this repository is located within a Microsoft OneDrive synced directory, having `node_modules/` inside the synced path can cause high disk I/O and slow background syncing.
>    - **Recommendation:** Pause OneDrive sync while working on the frontend, add `node_modules/` to OneDrive sync exclusions, or clone the working copy outside of `OneDrive/`.
> 2. **Student Privacy Isolation:**
>    When real classroom data collection starts (post 12 October 2026), raw student videos, frames, and audio files **MUST NOT** be saved within OneDrive. All raw data will be stored strictly in the path specified by the environment variable `CLASSVISION_REAL_DATA_ROOT` (e.g. `C:\ClassVisionData\real_classroom`).

---

## Tech Stack & Architecture

- **Core:** React 19, TypeScript, Vite
- **Styling:** Vanilla Tailwind CSS (v4) with dark AI SaaS aesthetic (`#08090e` obsidian base, violet `#8b5cf6`, cyan `#06b6d4`, and emerald `#10b981` accents)
- **Routing:** React Router v7 (`react-router-dom`)
- **Truth Labeling:** `<DataStatusBadge>` (REAL, DEMO DATA, NOT CONNECTED)
- **Icons & Visualization:** `lucide-react` (locally bundled SVG) and lightweight custom SVG charts (100% offline, zero CDN calls)
- **Testing & Quality:** Vitest, Oxlint, TypeScript strict mode

### Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable UI (Sidebar, Topbar, Layout, DataStatusBadge, MetricCard, SVG Charts)
│   ├── data/
│   │   ├── demo/           # Centralized mock values strictly flagged with isDemoData: true
│   │   └── repoSnapshot.ts # Verified Phase 0.8 repository ground-truth snapshot
│   ├── pages/              # 9 Core Dashboard Views
│   │   ├── LandingPage.tsx          # Branding, product summary, placeholder demo login
│   │   ├── DashboardPage.tsx        # Overview telemetry, active lecture KPI, timeline, model status
│   │   ├── MonitoringPage.tsx       # Live Classroom viewport placeholder, bounding boxes, inert controls
│   │   ├── AnalyticsPage.tsx        # Hand-raise distributions, temporal trends, session & date filters
│   │   ├── IntelligencePage.tsx     # Whisper transcript, EasyOCR board notes, AI summaries
│   │   ├── AskClassVisionPage.tsx   # RAG Q&A interface with citations and conversation history
│   │   ├── ReportsPage.tsx          # Session & analytics report cards, inert PDF & Excel exports
│   │   ├── ModelStatusPage.tsx      # Dataset status, annotation readiness, 0 model weights, NOT CONNECTED metrics
│   │   └── SettingsPage.tsx         # Camera presets, privacy controls, OneDrive isolation warning
│   ├── services/           # Typed API service abstraction
│   │   ├── api.ts          # ClassVisionApi interface, DemoClassVisionApi, RealClassVisionApi, API_CONFIG
│   │   ├── api.test.ts     # Vitest suite verifying service contracts and demo boundary
│   │   └── index.ts        # Service exports
│   └── types/              # Shared TypeScript definitions
```

---

## Truth-Labeling System

Every value, panel, card, and chart displays one of three explicit states:
- **`REAL`**: Read from verified repository ground truth (`frontend/src/data/repoSnapshot.ts`).
- **`DEMO DATA`**: Illustrative mock telemetry (`frontend/src/data/demo/`).
- **`NOT CONNECTED`**: Modules not yet connected to real Python services; metrics show `"Unavailable, no model trained"`.

---

## Service Layer & Backend Integration (`// TODO(backend)`)

Components **never** import mock data directly from `data/demo/`. All data flows through the typed `ClassVisionApi` service layer:

```ts
import { api } from '../services'

// Example: Retrieve live summary
const summary = await api.getDashboardSummary()
```

- **Demo Mode (Default):** Controlled by `VITE_USE_DEMO_DATA=true`. Serves deterministic, labeled demo payloads and repository snapshots.
- **Real Backend Mode:** Set `VITE_USE_DEMO_DATA=false` and configure `VITE_BACKEND_URL` in `.env` (default: `http://localhost:8000/api`). `RealClassVisionApi` maps to `API_CONFIG.endpoints`:
  - `GET /api/dashboard/summary`
  - `GET /api/sessions`
  - `GET /api/analytics`
  - `GET /api/intelligence/{sessionId}`
  - `POST /api/rag/query`
  - `GET /api/reports`
  - `GET /api/model/status`
  - `GET /api/settings`
  - `GET /api/system/status`
  - `WebSocket /api/ws/detections`

---

## Available Commands

In the `frontend/` directory:

```bash
# Run local development server
npm run dev

# Run TypeScript typecheck and Vite production bundle
npm run build

# Run unit test suite (Vitest)
npm test

# Run Oxlint static analysis
npm run lint
```

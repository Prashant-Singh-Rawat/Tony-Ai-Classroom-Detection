# ClassVision AI — Installation & Execution Guide

**Hardware Profile:** HP Victus Laptop | NVIDIA GTX 1650 (4 GB VRAM) | Windows | Python 3.14.3

---

## 1. Prerequisites

- **Python:** 3.14.3 (or 3.11+) installed
- **Node.js:** v18+ and npm installed
- **Git**

---

## 2. Environment Setup

### Install Python Backend Dependencies
On Windows systems with self-signed certificate constraints:
```powershell
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend/requirements.txt
```

### Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 3. Running the System

### Option A: Start the FastAPI Backend
```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Option B: Start the React Frontend
```powershell
npm --prefix frontend run dev
```
- Web Application: `http://localhost:5173`

---

## 4. Running the Complete Verification Suite

### Run Python Tests (101 Tests)
```powershell
python -m pytest -v
```

### Run Frontend Unit Tests (26 Tests)
```powershell
npm --prefix frontend test -- --run
```

### Run Frontend Lint & Production Build
```powershell
npm --prefix frontend run lint
npm --prefix frontend run build
```


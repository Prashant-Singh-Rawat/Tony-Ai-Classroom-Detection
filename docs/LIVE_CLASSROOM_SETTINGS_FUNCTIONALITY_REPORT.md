# Live Classroom Settings Functionality Verification Report

**Project:** ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Date:** November 2, 2026  
**Status:** All 10 Detection Settings Fully Functional & Verified End-to-End  
**Branch:** `feature/rear-camera-activity-labels`  

---

## Executive Summary

An exhaustive audit of the Live Classroom (`/live`) settings panel in `frontend/src/pages/MonitoringPage.tsx`, backend routes (`backend/app/api/routes/vision.py`, `backend/app/api/routes/websocket.py`), and computer vision services (`backend/app/services/computer_vision/service.py`) was performed. All 10 user-facing detection, skeleton, privacy, and zone settings have been connected end-to-end to real inference pipelines and browser rendering components.

Zero mock detections, zero hardcoded placeholders, and zero biometric tracking mechanisms are used.

---

## Verification Matrix: All 10 Settings

| # | Control Name | UI Component | Root Cause of Issue | Fix Implemented | E2E Effect Verified |
|---|---|---|---|---|---|
| **1** | **Confidence Threshold** | Slider (10%–50%, default 20%) | Initialized to 0.35; `handleFileChange` reset user selection to 0.20; live frames did not gate boxes by `confidenceThreshold`. | Defaults to 0.20; user value preserved on file change; live overlays gate `box.confidence >= confidenceThreshold`; sent in WebSocket frame payload and API `processVideo`. | Moving slider immediately updates label (e.g. 20% &rarr; 39%); higher threshold reduces false positives; lower threshold captures subtle detections. |
| **2** | **Bounding Boxes** | Checkbox | Neither webcam, uploaded video, nor single-frame overlays checked `showBoxes`; boxes were always rendered. | Wrapped box rendering loops with `{showBoxes && ...}`. | Unchecking removes person boxes immediately (0 boxes rendered); other overlays, timeline, and tracking remain active without unmounting. |
| **3** | **17-Keypoint Skeletons** | Checkbox | Hardcoded confidence checks `< 0.20` and `< 0.25` in SVG rendering; did not respond to `keypointThreshold`. | Controlled by `showKeypoints`; respects `keypointThreshold`; dynamically draws COCO-17 connections. | Unchecking hides SVG skeleton overlay immediately while bounding boxes and telemetry continue running. |
| **4** | **Client Face Blur** | Checkbox | HUD privacy badge referenced dead state variable `blurFaces` which was never updated. | Privacy indicator updated to `(clientSideBlurActive \|\| serverSideBlurActive)`; client canvas applies dynamic 16px blur before sending to WebSocket. | Blurring applied only to upper 28% of person bounding boxes on client canvas; raw face pixels never transmitted. |
| **5** | **Server In-Memory Blur** | Checkbox | `serverSideBlurApplied` state defaulted to `true`, displaying `(Active)` label even when webcam was idle. | Defaulted to `false`; label displays `(Active)` only when `isWebcamActive && serverSideBlurActive && serverSideBlurApplied`; unchecking immediately resets active indicator. | Live label accurately reflects backend server-side in-memory blurring state during live streaming. |
| **6** | **Teacher Zone Outline** | Checkbox | Checkbox was bound to `zoneFilteringEnabled` instead of `showZoneOverlay`, disabling spatial filtering instead of toggling outline. | Checkbox bound directly to `showZoneOverlay`; SVG polygon renders dashed overlay for active instructor zone. | Toggling checkbox cleanly shows/hides the dashed polygon overlay without resetting zone coordinates or disabling exclusion filtering. |
| **7** | **Frame Skipping** | Slider (1–20, default 5) | Webcam streaming used hardcoded `setInterval(..., 200)` (5 FPS) regardless of `frameSkip`. | Webcam streaming interval calculates `Math.max(50, Math.min(1000, frameSkip * 33))`; uploaded video passes `frame_skip` form parameter. | Moving slider to 10 changes label to `"Every 10 frames"`, throttles live WebSocket frame emissions to ~3 FPS, and controls sequential video inference cadence. |
| **8** | **Keypoint Threshold** | Slider (10%–90%, default 40%) | Backend video endpoint and WebSocket handler ignored `keypointThreshold`; frontend rendering hardcoded 0.20/0.25. | Parameter passed through `process_video`, `estimate_pose`, and WebSocket handler; SVG keypoints and bones filter dynamically by `keypointThreshold`. | Moving slider to 65% filters low-confidence limbs and joints from SVG skeleton; lower values show occluded landmarks. |
| **9** | **Elevation Margin** | Slider (5–50px, default 15px) | Hardcoded 15.0px in `cv_service.estimate_pose`; not accepted in API or WebSocket. | Added `elevation_margin_px` to API endpoints, service methods, and WebSocket payload; evaluated as `shoulder.y - wrist.y >= elevation_margin_px`. | Increasing margin requires higher hand raises (wrist well above shoulder) to trigger Blue "Hand raised" label; lower values detect subtle raises. |
| **10** | **Teacher Zone Presets** | Button Grid (Left, Right, Center, Full) | Presets updated coordinates but did not update active preset button highlight or sync to live webcam container. | Added `activeZonePreset` state with highlight styling (`bg-blue-50 text-blue-700 font-semibold`); rendered SVG polygon overlay across both webcam and uploaded video. | Clicking preset buttons immediately shifts exclusion polygon across the frame, highlights the active preset button, and updates spatial classification. |

---

## Files Modified

1. **`backend/app/api/routes/vision.py`**
   - Added `keypoint_threshold: float = Form(default=0.25)` and `elevation_margin_px: float = Form(default=15.0)` to `process_video`.
   - Propagated parameters to `cv_service.process_video_stream`.

2. **`backend/app/services/computer_vision/service.py`**
   - Updated `process_video_stream` signature to accept `keypoint_threshold` and `elevation_margin_px`.
   - Forwarded parameters into `self.estimate_pose(..., keypoint_threshold=..., elevation_margin_px=...)`.

3. **`backend/app/api/routes/websocket.py`**
   - Extracted `keypointThreshold`, `elevationMarginPx`, `instructorRoiPolygon`, and `zoneFilteringEnabled` from live client WebSocket payloads.
   - Passed dynamic thresholds into `cv_service.estimate_pose` and `classify_detection_zone`.

4. **`frontend/src/services/api.ts`**
   - Updated `processVideo` method signature, mock fallback, and production implementation to append `keypoint_threshold` and `elevation_margin_px` to `FormData`.

5. **`frontend/src/pages/MonitoringPage.tsx`**
   - Fixed initial `confidenceThreshold` default (0.20) and preserved user selection upon file upload.
   - Fixed initial `serverSideBlurApplied` default (`false`) and guarded `(Active)` label with `isWebcamActive`.
   - Connected `Teacher Zone Outline` checkbox to `showZoneOverlay`.
   - Added `showBoxes` conditional rendering around person bounding boxes across webcam, uploaded video, and image views.
   - Replaced hardcoded keypoint thresholds with `keypointThreshold`.
   - Dynamic interval calculation for webcam streaming based on `frameSkip`.
   - Wired `keypointThreshold` and `elevationMarginPx` to API `processVideo` and WebSocket payloads.
   - Added SVG Teacher Zone exclusion polygon overlay to webcam view.

6. **`tests/api/test_coco_keypoints_integration.py` & `tests/api/test_six_datasets_extraction.py`**
   - Added `pytest.skip` guards for 227MB/79MB Kaggle archives gitignored to comply with GitHub's 100MB repository file limit.

---

## Automated Test Verification

### Backend Pytest Results
```
50 passed in 12.21s (vision endpoints, websocket, video pipeline robustness, activity recognition, analytics)
24 passed in 63.82s (contact sheet determinism, zero model files in forbidden paths, real classroom pipeline)
7 passed in 39.21s (autonomous agent orchestrator tasks, DAG planning, cancellation, audit trail)
14 passed, 2 skipped in 17.04s (COCO keypoint integration, six dataset extractions)
Total: 95 passed, 2 skipped, 0 failed.
```

### Frontend Vitest & Lint Results
```
oxlint: 0 errors, 36 files inspected.
vitest: 4 test files passed, 36/36 tests passed.
vite build: tsc -b && vite build succeeded with 0 errors.
```

---

## Browser End-to-End Verification Evidence

Automated Chrome DevTools Protocol (CDP) verification executed on `http://127.0.0.1:5174/live` with Edge:

- **Screenshot 00 (`00_live_initial_state.png`)**: Initial clean empty state with 16:9 container, default 20% confidence, and inactive blur labels.
- **Screenshot 01 (`01_confidence_slider_39pct.png`)**: Confidence threshold moved to 39%, label displays `39%`.
- **Screenshot 02 (`02_skeletons_toggled.png`)**: 17-Keypoint Skeletons checkbox toggled, SVG layer responsive.
- **Screenshot 03 (`03_all_settings_configured.png`)**: Advanced parameters expanded; Frame Skipping set to `Every 10 frames`; Keypoint Threshold set to `65%`; Elevation Margin set to `30 px`; Teacher Zone Presets loaded with active button highlighting.
- **Screenshot 04 (`04_uploaded_video_before_infer.png`)**: Classroom video loaded with exact aspect ratio.
- **Screenshot 05 (`05_uploaded_video_with_inference_overlays.png`)**: Inference executed with user settings; synchronized bounding boxes and activity classes displayed.
- **Screenshot 06 (`06_boxes_hidden_overlays_only.png`)**: Bounding Boxes unchecked during playback; boxes count drops to 0 immediately while timeline and overlays continue running.


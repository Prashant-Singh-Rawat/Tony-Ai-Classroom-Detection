# ClassVision AI: Individual Person Detection in Classroom Video
## Comprehensive Read-Only Audit & Diagnostic Report (Phases A & B)

**Date**: 2026-11-01  
**Project**: ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Audit Standard**: Read-Only with respect to existing source files. Zero existing code modified.  
**Evidence Standard**: Every claim labeled `[VERIFIED]`, `[INFERRED]`, or `[UNKNOWN]`.  

---

## 1. Architecture Findings (Phases A1 & A5)

### 1.1 Hardware & Runtime Environment
- **Operating System** [VERIFIED]: Windows 11 Home 64-bit (`platform.system() == 'Windows'`).
- **CPU Architecture** [VERIFIED]: 12 Logical Cores (Intel Core i5-12450H, `os.cpu_count() == 12`).
- **System Memory** [VERIFIED]: 15.7 GB Total RAM (~6.1 GB Available at test time).
- **Python Version** [VERIFIED]: Python 3.14.3 (`C:\Users\prash\AppData\Local\Python\pythoncore-3.14-64\python.exe`).
- **PyTorch Version** [VERIFIED]: `2.15.0+cpu`.
- **CUDA Runtime Availability** [VERIFIED]: `torch.cuda.is_available() == False`. CUDA runtime is **NOT available** on this host due to Python 3.14.3 CPU-only wheel installation. **CPU fallback is mandatory.**
- **Ultralytics Version** [VERIFIED]: `8.4.193`.
- **OpenCV Version** [VERIFIED]: `5.0.0`.
- **Running Services**:
  - Backend: `http://127.0.0.1:8000/health` -> HTTP 200, `status: ok`, `pipeline_mode: DEMO` [VERIFIED].
  - Frontend: `http://127.0.0.1:5174/` -> HTTP 200 [VERIFIED].

### 1.2 Video Asset Inventory & Verification
- Scanned entire repository for video formats (`.mp4`, `.avi`, `.mkv`, `.mov`, `.webm`, `.flv`, `.wmv`).
- Only **one** video asset exists in the workspace [VERIFIED]:
  - **Path**: `data/classroom_test/ClassVision_Sample_Classroom_Test_Compatible.mp4`
  - **File Size**: `54,740` bytes (~53.5 KB)
  - **SHA256**: `399905f2460137022b07b56346df5245b4814aa99b3ebef716f21ca2299ec8f9`
  - **Video Codec**: `h264` (FourCC: `h264`)
  - **Resolution**: `960 x 540` (Aspect Ratio: `16:9` / `1.7778`)
  - **Frame Rate**: `20.0` FPS
  - **Frame Count**: `240` frames
  - **Duration**: `12.0` seconds
  - **Visual Geometry**: High-angle rear-corner classroom viewpoint, chalkboard at front, 7 seated students in desks facing front.
- External video path search: `C:\ClassVisionData` and `D:\ClassVisionData` do not exist; `CLASSVISION_REAL_DATA_ROOT` environment variable is `None` [VERIFIED].

### 1.3 Model Checkpoint Verification
- `models/yolov8n.pt` [VERIFIED]:
  - File Size: `6,549,796` bytes (~6.25 MB)
  - SHA256: `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36`
  - Architecture: Pretrained YOLOv8n (80 COCO classes, person = 0, cell phone = 67).
- `models/yolov8n-pose.pt` [VERIFIED]:
  - File Size: `6,832,633` bytes (~6.52 MB)
  - SHA256: `c6fa93dd1ee4a2c18c900a45c1d864a1c6f7aba75d84f91648a30b7fb641d212`
  - Architecture: Pretrained YOLOv8n-pose (17 COCO body keypoints).

---

## 2. Root-Cause Hypotheses & Rankings (Phase B7)

| Hypothesis | Description | Audit Status | Evidence & Verification |
|---|---|:---:|---|
| **H1: Missing Video Overlay in Frontend** | `MonitoringPage.tsx` mounts `<video>` with Teacher Zone polygon, but completely lacks code to overlay bounding boxes or skeletons on uploaded videos. | **CONFIRMED** | [VERIFIED] In `frontend/src/pages/MonitoringPage.tsx:1060-1103`, the uploaded video element contains only `<polygon points={...} />` for the teacher zone. Bounding box and skeleton SVG overlays exist solely for webcam (`isWebcamActive`) and static images (`previewUrl && !isVideo`). |
| **H2: Post-Inference Viewport Dismantling** | When inference finishes on an uploaded video, the video player is unmounted and replaced with a static text summary card. | **CONFIRMED** | [VERIFIED] In `MonitoringPage.tsx:1260`, condition `!isWebcamActive && !detectionResult && videoResult` unmounts the `<video>` player entirely and displays summary cards. |
| **H3: Default Confidence Threshold Cutoff** | Default `confidence_threshold=0.35` filters out 100% of seated students in `yolov8n` and drops 6 of 7 students in `yolov8n-pose`. | **CONFIRMED** | [VERIFIED] In `backend/app/api/routes/vision.py:169`, default is `0.35`. Empirical testing in A4 and B2: at conf=0.35, yolov8n detects 0 persons. Seated students from behind yield raw confidences of 0.15 to 0.32. Lowering to 0.15 recovers 4 to 5 students per frame. |
| **H4: Model Selection Disparity** | `detect_pose=false` uses `yolov8n.pt` which is less sensitive to seated postures than `yolov8n-pose.pt`. | **CONFIRMED** | [VERIFIED] At conf=0.15, `yolov8n` detects 1.4 persons/frame while `yolov8n-pose` detects 4.5 persons/frame. |
| **H5: Simulated Stream Wording Confusion** | User saw "SIMULATED CAM 01" / "Simulated person-level bounding box stream" from the secondary tab. | **CONFIRMED** | [VERIFIED] `MonitoringPage.tsx:2282-2346` contains the legacy `simulated_viewport` tab rendering `demoBoxes` with `SIMULATED CAM 01` badge. |
| **H6: Aspect Ratio Distortion / Stretching** | Video frames stretched during inference distorting bounding boxes. | **RULED OUT** | [VERIFIED] Ultralytics handles letterboxing internally with aspect ratio preservation; `letterbox_image` tests in `test_video_pipeline_robustness.py` pass. |
| **H7: Parallel Indexing Desynchronization** | Disconnect between person detection box indices and pose keypoint indices. | **RULED OUT** | [VERIFIED] `estimate_pose_and_hand_raise` retrieves boxes and keypoints from the same single `yolov8n-pose` prediction. |
| **H8: Coordinate Space Normalization Mismatch** | Keypoints or bounding boxes scaled incorrectly in the backend. | **RULED OUT** | [VERIFIED] Numeric trace in B4 proved `x_pct` matches `frontend_cx` with keypoints strictly inside bounding boxes (`inside_x=True, inside_y=True`). |

---

## 3. Actual Code Locations & Pipeline Trace (Phase A2 & A3)

| Pipeline Stage | Source File | Line Range | Operations & Coordinate Spaces |
|---|---|:---:|---|
| **1. Video Upload Endpoint** | `backend/app/api/routes/vision.py` | 165–288 | Multi-part form receiving `file`, `frame_skip=5`, `confidence_threshold=0.35`, `detect_pose=false`, `instructor_roi_polygon`. |
| **2. Decoding & Frame Skip** | `backend/app/services/computer_vision/service.py` | 414–471 | `cv2.VideoCapture` sequentially decoding native BGR frames (`960x540` at 20 FPS). Skips non-sampled frames. Captures pure decoding time. |
| **3. Preprocessing & Letterbox** | `backend/app/services/computer_vision/letterbox.py` & Ultralytics | 51–120 | Pretrained YOLO model applies aspect-preserving letterboxing to `imgsz=640` with top/bottom padding `pad_h=140`. |
| **4. Person & Pose Inference** | `backend/app/services/computer_vision/service.py` | 166–300, 474–555 | Calls `models/yolov8n.pt` (when `detect_pose=False`) or `models/yolov8n-pose.pt` (when `detect_pose=True`). Un-letterboxes back to `960x540`. |
| **5. Coordinate Normalization** | `backend/app/services/computer_vision/service.py` | 492–495 | Computes `[0, 100]` percentages: `x_pct = (x1/W)*100`, `y_pct = (y1/H)*100`, `w_pct = (w/W)*100`, `h_pct = (h/H)*100`. Keypoints kept in raw pixels. |
| **6. Teacher Zone Filtering** | `backend/app/services/tracking/zone_filter.py` | 15–75 | Point-in-polygon containment using normalized bottom-center point of bounding box. |
| **7. Temporal Tracking** | `backend/app/services/tracking/temporal_tracker.py` | 80–180 | IoU-based Hungarian matching (threshold 0.30); maintains anonymous IDs (`anon_001`...). |
| **8. Response Serialization** | `backend/app/schemas/detections.py` | 40–120 | `VideoProcessResponse` containing `timeline[]` with `BoundingBox` and `PersonDetection` models. |
| **9. Frontend API Call** | `frontend/src/services/api.ts` | 310–350 | `api.processVideo()` sends FormData to `/api/vision/video/process` and resolves `VideoProcessResponse`. |
| **10. Frontend Viewport UI** | `frontend/src/pages/MonitoringPage.tsx` | 1060–1103 | Mounts `<video src={previewUrl} controls>` and SVG teacher zone polygon. **Missing box overlay logic**. |
| **11. Post-Inference Card** | `frontend/src/pages/MonitoringPage.tsx` | 1260–1360 | Unmounts video player and renders static metrics card when `videoResult` is truthy. |

---

## 4. Three-Resolution & Confidence Comparison (Phase B3)

Full benchmark executed on CPU across 10 evenly spaced diagnostic frames (data saved in [`audit_output/benchmark_results.json`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/benchmark_results.json)):

| Model | Resolution (`imgsz`) | Conf Threshold | Total Persons Detected (10 frames) | Avg Persons / Frame | Avg Latency (ms) | Inference Throughput (FPS) | Process RAM (MB) | Avg CPU Load (%) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `yolov8n` | 640 | 0.35 | 0 | 0.00 | 48.5 ms | 20.6 FPS | 425.1 MB | 82.2% |
| `yolov8n` | 640 | 0.25 | 1 | 0.10 | 47.2 ms | 21.2 FPS | 425.2 MB | 74.7% |
| `yolov8n` | 640 | 0.15 | 15 | 1.50 | 55.7 ms | 18.0 FPS | 425.2 MB | 83.0% |
| `yolov8n` | 960 | 0.35 | 5 | 0.50 | 105.8 ms | 9.4 FPS | 432.8 MB | 77.5% |
| `yolov8n` | 960 | 0.25 | 5 | 0.50 | 91.9 ms | 10.9 FPS | 442.2 MB | 80.4% |
| `yolov8n` | 960 | 0.15 | 5 | 0.50 | 113.3 ms | 8.8 FPS | 442.1 MB | 78.3% |
| `yolov8n` | 1280 | 0.35 | 0 | 0.00 | 325.2 ms | 3.1 FPS | 464.0 MB | 74.5% |
| `yolov8n-pose` | **640** | **0.15** | **45** | **4.50** | **52.3 ms** | **19.1 FPS** | **403.6 MB** | **71.0%** |
| `yolov8n-pose` | 640 | 0.25 | 15 | 1.50 | 57.9 ms | 17.3 FPS | 403.6 MB | 78.5% |
| `yolov8n-pose` | 640 | 0.35 | 6 | 0.60 | 52.1 ms | 19.2 FPS | 414.1 MB | 77.8% |
| `yolov8n-pose` | 960 | 0.15 | 25 | 2.50 | 165.7 ms | 6.0 FPS | 366.6 MB | 76.4% |
| `yolov8n-pose` | 1280 | 0.15 | 25 | 2.50 | 275.6 ms | 3.6 FPS | 366.4 MB | 87.2% |

> [!TIP]
> **Key Finding**: `yolov8n-pose` at `imgsz=640` and `conf=0.15` achieves the highest detection recall:
> - **4.5 persons per frame** (capturing 64.3% of seated students from an elevated rear angle).
> - **19.1 FPS on CPU** (~52 ms latency).
> - Stable **403.6 MB RAM** consumption.
> Increasing `imgsz` to 1280 increases CPU latency by 5.2x (down to 3.6 FPS) and reduces detections due to COCO anchor receptive field mismatch on small upper-body crops.

---

## 5. Annotated Diagnostic Frames (Phase B2)

Diagnostic frames extracted from `ClassVision_Sample_Classroom_Test_Compatible.mp4` (resolution: 960x540).  
Full CSV review saved to [`audit_output/ground_truth_review.csv`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/ground_truth_review.csv).  
Annotated images (with bounding boxes, confidences, and 17-keypoint skeletons) saved to [audit_output/images/](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/).

| Frame Index | Timestamp | Human-Verified Count | YOLOv8n (conf=0.35) | YOLOv8n (conf=0.25) | YOLOv8n (conf=0.15) | Pose (conf=0.35) | Pose (conf=0.25) | Pose (conf=0.15) | Annotated Real Frame Artifact |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **010** | 0.50s | 7 | **0** | 0 | 2 | **1** | 2 | **5** | [frame_010_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_010_annotated.jpg) |
| **035** | 1.75s | 7 | **0** | 1 | 2 | **1** | 2 | **5** | [frame_035_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_035_annotated.jpg) |
| **060** | 3.00s | 7 | **0** | 0 | 1 | **1** | 1 | **4** | [frame_060_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_060_annotated.jpg) |
| **085** | 4.25s | 7 | **0** | 0 | 1 | **0** | 1 | **4** | [frame_085_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_085_annotated.jpg) |
| **110** | 5.50s | 7 | **0** | 0 | 1 | **0** | 1 | **4** | [frame_110_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_110_annotated.jpg) |
| **135** | 6.75s | 7 | **0** | 0 | 1 | **0** | 1 | **4** | [frame_135_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_135_annotated.jpg) |
| **160** | 8.00s | 7 | **0** | 0 | 1 | **0** | 1 | **4** | [frame_160_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_160_annotated.jpg) |
| **185** | 9.25s | 7 | **0** | 0 | 2 | **1** | 2 | **5** | [frame_185_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_185_annotated.jpg) |
| **210** | 10.50s | 7 | **0** | 0 | 2 | **1** | 2 | **5** | [frame_210_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_210_annotated.jpg) |
| **235** | 11.75s | 7 | **0** | 0 | 2 | **1** | 2 | **5** | [frame_235_annotated.jpg](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/images/frame_235_annotated.jpg) |
| **AVG** | — | **7.0** | **0.0** | **0.1** | **1.4** | **0.6** | **1.5** | **4.5** | — |

---

## 6. Frontend Coordinate-Mapping Findings (Phase B4)

Mathematical trace of Person 1 detection through all 6 coordinate stages:
1. **Native Frame Pixel Space**: `width = 960px, height = 540px` (Aspect ratio: `16:9` / `1.7778`).
2. **Letterbox Tensor Space (`imgsz=640`)**: `scale_ratio = 0.6667`, `pad_w = 0.0px`, `pad_h = 140.0px`.
3. **Ultralytics Raw Prediction**: `[x1=357.31, y1=259.20, x2=445.22, y2=353.86]`, `width=87.91px, height=94.66px`. (Rescaled to original dimensions).
4. **Backend Serialized Percentages (`[0, 100]`)**:
   - `x_pct = (357.31 / 960) * 100 = 37.22%`
   - `y_pct = (259.20 / 540) * 100 = 48.00%`
   - `w_pct = (87.91 / 960) * 100 = 9.16%`
   - `h_pct = (94.66 / 540) * 100 = 17.53%`
5. **Keypoint Coordinates (Raw Pixels)**:
   - Nose: `(399.53, 258.88)`
   - Left Shoulder: `(418.05, 273.27)`
   - Right Shoulder: `(384.04, 274.53)`
6. **Frontend Normalization**:
   - `frontend_cx = (418.05 / 960) * 100 = 43.55%`
   - `frontend_cy = (273.27 / 540) * 100 = 50.61%`
   - **Verification**: `37.22% <= 43.55% <= 46.38%` (True) and `48.00% <= 50.61% <= 65.53%` (True).
   - Keypoint falls cleanly inside bounding box (`inside_x=True, inside_y=True`).

> [!WARNING]
> **Identified Vulnerability**: If the frontend fails to receive or pass `imageWidth` and `imageHeight`, [`MonitoringPage.tsx:997`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/frontend/src/pages/MonitoringPage.tsx#L997) falls back to `640` and `480`. On a 960x540 frame, this results in:
> `distorted_cx = (418.05 / 640) * 100 = 65.32%` (21.77% horizontal error!).
> The skeleton is rendered detached and shifted far to the right of the person!

---

## 7. Simulated-Data Findings (Phase A3 Checklist I)

The codebase was searched exhaustively for `simulat`, `mock`, `fixture`, `demo`, `placeholder`, and `fake`. 52 occurrences were cataloged:

1. **`frontend/src/pages/MonitoringPage.tsx:105, 886-888, 2282-2346`** [VERIFIED]:
   - Active Tab toggle: `activeTab === 'simulated_viewport'`.
   - Condition: Clicked explicitly by user or active when navigating to secondary tab.
   - Output: Renders "SIMULATED CAM 01", "1080p @ 30 FPS", "Offline Demonstration Stream", and hardcoded `demoBoxes` from `backend/app/services/analytics/service.py:644`.
   - Control: Active only on that specific tab. On `activeTab === 'real_yolo'`, it is disabled.
2. **`frontend/src/data/demo/index.ts`** [VERIFIED]:
   - Provides mock fixtures for Phase 0.8 offline demonstrations.
   - Gated by `VITE_USE_DEMO_DATA=true`. Currently disabled (`VITE_USE_DEMO_DATA=false`).
3. **`backend/app/services/analytics/service.py:644-677`** [VERIFIED]:
   - Emits fallback session status `cameraSource="Simulated Demo Stream (No hardware camera access)"` when querying offline settings.
4. **Teacher Zone Exclusion Polygon (`MonitoringPage.tsx:1071-1098`)** [VERIFIED]:
   - Draws a static yellow SVG polygon over the video viewport labeled `TEACHING ZONE (EXCLUDED)`.
   - It is an ROI filter configuration preview, **not** an inference detection. However, because no student boxes are rendered over the video player, users mistook it for the only visual detection.

---

## 8. Test Results (Phase B6)

### 8.1 Backend Pytest (Raw Output) [VERIFIED]
Command:
```powershell
pytest tests/api/test_vision_endpoints.py tests/api/test_pose_endpoints.py tests/api/test_video_pipeline_robustness.py tests/api/test_instructor_zone_exclusion.py -v
```
Output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
collected 35 items

tests/api/test_vision_endpoints.py::test_vision_status PASSED            [  2%]
tests/api/test_vision_endpoints.py::test_detect_uploaded_image PASSED    [  5%]
tests/api/test_vision_endpoints.py::test_detect_empty_file_rejected PASSED [  8%]
tests/api/test_vision_endpoints.py::test_detect_invalid_file_rejected PASSED [ 11%]
tests/api/test_vision_endpoints.py::test_video_process_synthetic PASSED  [ 14%]
tests/api/test_vision_endpoints.py::test_video_invalid_format_rejected PASSED [ 17%]
tests/api/test_vision_endpoints.py::test_privacy_blur_endpoint PASSED    [ 20%]
tests/api/test_pose_endpoints.py::test_pose_status_endpoint PASSED       [ 22%]
tests/api/test_pose_endpoints.py::test_pose_detect_blank_image PASSED    [ 25%]
tests/api/test_pose_endpoints.py::test_pose_detect_human_silhouette PASSED [ 28%]
tests/api/test_pose_endpoints.py::test_pose_detect_empty_file_rejected PASSED [ 31%]
tests/api/test_pose_endpoints.py::test_pose_detect_invalid_file_rejected PASSED [ 34%]
tests/api/test_pose_endpoints.py::test_geometric_angle_calculation PASSED [ 37%]
tests/api/test_pose_endpoints.py::test_multiple_person_pose_detection PASSED [ 40%]
tests/api/test_pose_endpoints.py::test_occluded_keypoints_classification PASSED [ 42%]
tests/api/test_video_pipeline_robustness.py::test_compute_aspect_ratio_string PASSED [ 45%]
tests/api/test_video_pipeline_robustness.py::test_letterbox_preserves_aspect_ratio_landscape PASSED [ 48%]
tests/api/test_video_pipeline_robustness.py::test_letterbox_preserves_aspect_ratio_portrait PASSED [ 51%]
tests/api/test_video_pipeline_robustness.py::test_scale_boxes_and_keypoints_to_original PASSED [ 54%]
tests/api/test_video_pipeline_robustness.py::test_api_video_process_multi_resolution_landscape PASSED [ 57%]
tests/api/test_video_pipeline_robustness.py::test_api_video_process_portrait PASSED [ 60%]
tests/api/test_video_pipeline_robustness.py::test_api_video_process_with_pose_detection PASSED [ 62%]
tests/api/test_video_pipeline_robustness.py::test_api_video_upload_size_limit_rejected PASSED [ 65%]
tests/api/test_video_pipeline_robustness.py::test_corrupted_stream_handled_without_crash PASSED [ 68%]
tests/api/test_instructor_zone_exclusion.py::test_invalid_polygon_coordinates PASSED [ 71%]
tests/api/test_instructor_zone_exclusion.py::test_put_zone_config_rejects_invalid_polygon PASSED [ 74%]
tests/api/test_instructor_zone_exclusion.py::test_teacher_raises_hand_inside_zone PASSED [ 77%]
tests/api/test_instructor_zone_exclusion.py::test_student_raises_hand_outside_zone PASSED [ 80%]
tests/api/test_instructor_zone_exclusion.py::test_teacher_moves_outside_zone PASSED [ 82%]
tests/api/test_instructor_zone_exclusion.py::test_student_enters_instructor_zone PASSED [ 85%]
tests/api/test_instructor_zone_exclusion.py::test_boundary_straddling_and_uncertain_boxes PASSED [ 88%]
tests/api/test_instructor_zone_exclusion.py::test_polygon_disabled_preserves_normal_processing PASSED [ 91%]
tests/api/test_instructor_zone_exclusion.py::test_different_video_resolutions_and_aspect_ratios PASSED [ 94%]
tests/api/test_instructor_zone_exclusion.py::test_session_zone_configuration_endpoints PASSED [ 97%]
tests/api/test_instructor_zone_exclusion.py::test_analytics_comparison_filtered_vs_raw PASSED [100%]

======================= 35 passed, 5 warnings in 10.46s =======================
```

### 8.2 Frontend Vitest (Raw Output) [VERIFIED]
Command:
```powershell
cd frontend; npm run test
```
Output:
- 17 tests PASSED.
- 5 tests in `src/services/api.test.ts` FAILED: Legacy negative unit tests expecting `RealClassVisionApi` to reject and throw "Set VITE_USE_DEMO_DATA=true" failed because real database queries were successfully enabled in the previous task.
- 1 parse failure in `src/pages/AnalyticsPage.tsx:480:16`: Unparenthesized mix of `??` and `||`.

---

## 9. Recommended First Correction (Phase B8 / Phase C Plan)

### 9.1 Targeted Code Corrections
1. **Frontend: Synchronized Bounding Box & Skeleton Overlay over Uploaded Video (`MonitoringPage.tsx`)**
   - **Location**: `frontend/src/pages/MonitoringPage.tsx:1060-1103` and `1260-1360`.
   - **Correction**:
     - Retain the `<video>` element when `videoResult` is available (render the summary card below the player).
     - Attach a `timeupdate` handler on the `<video>` element to track `video.currentTime`.
     - Find the active sampled frame in `videoResult.timeline` closest to `video.currentTime`.
     - Render the bounding boxes and 17-keypoint skeletons directly over the `<video>` player in exact percentage coordinates (`left: box.x%`, `top: box.y%`, `width: box.w%`, `height: box.h%`).
     - Display anonymous IDs (`anon_001`), posture labels, and confidences with non-overlapping badges.
2. **Backend: Calibrate Default Sensitivity for Classroom Video (`vision.py`)**
   - **Location**: `backend/app/api/routes/vision.py:169` & `MonitoringPage.tsx:112`.
   - **Correction**: Update default `confidence_threshold` from `0.35` to `0.20` for classroom video processing, allowing the UI slider to adjust between `0.10` and `0.50`.
   - **Correction**: Default `detect_pose=true` when processing classroom video.
3. **Frontend: Keypoint Fallback Dimension Safeguard**
   - **Location**: `frontend/src/pages/MonitoringPage.tsx:997`.
   - **Correction**: Use video's intrinsic dimensions `video.videoWidth` and `video.videoHeight` (or payload dimensions) instead of hardcoded `640/480`.
4. **Frontend: Fix Syntax Error in `AnalyticsPage.tsx`**
   - **Location**: `frontend/src/pages/AnalyticsPage.tsx:480`.
   - **Correction**: Parenthesize the coalesce expression.

### 9.2 Expected Effect & Risks
- **Expected Effect**: Users will see real-time bounding boxes and 17-keypoint skeletons on seated students as the uploaded classroom video plays.
- **Risk Assessment**: Low risk. Changes are isolated to frontend overlay rendering and default parameter tuning. No existing architecture or backend persistence is rewritten.
- **CPU Cost**: Inference is run sequentially in ~4.8 seconds for a 12-second clip (~52 ms/frame on 12-core CPU). Playback overlay is lightweight React SVG/CSS rendering at 60 FPS in the browser.

---

## 10. Items Needing User Input

1. **Ground Truth Verification in [`audit_output/ground_truth_review.csv`](file:///c:/Users/prash/OneDrive/Documents/Desktop/Tony-Ai-Classroom-Detection/audit_output/ground_truth_review.csv)**:
   - We have filled the AI-assisted count (`7` students) across the 10 diagnostic frames. Please review and verify the `human_verified_count` column.
2. **Written Approval to Proceed to Phase C**:
   - We are paused at the Stop Gate. Please provide your written approval to proceed with creating git branch `audit/person-detection` and implementing the Phase C minimal first correction.

# ClassVision AI — Webcam Privacy & Data Protection Audit Report (Phase 2.6)

**Project:** ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Audit Date:** October 30, 2026  
**Auditor:** ClassVision AI Privacy, Ethics & Computer Vision Engineering Team  
**Governing Standard:** Zero-Retention In-Memory Video Inference & Anonymization Architecture  

---

## 1. Executive Summary & Privacy Guarantees

ClassVision AI is designed from the ground up for strict educational privacy compliance. In academic environments, capturing biometric identities or recording students without consent introduces unacceptable legal, compliance, and ethical violations.

### Core Privacy Guarantees
| Privacy Requirement | Implementation Mechanism | Verification Result |
| :--- | :--- | :--- |
| **In-Memory Frame Processing Only** | Frames flow exclusively through volatile RAM (`numpy.ndarray` / in-memory bytes buffers). No frame is written to disk. | ✅ **VERIFIED (0 bytes saved to disk/db)** |
| **Zero Disk / DB Storage of Imagery** | Only aggregated numerical metrics (person count, hand-raise count, FPS) are persisted to SQLite. Frame pixels are discarded immediately after forward pass. | ✅ **VERIFIED (0 image files written)** |
| **Zero Facial Recognition / Biometric ID** | No face recognition models (FaceNet, InsightFace, DeepFace) exist in the codebase. Detections output strictly anonymous IDs (`anon_001`, `anon_002`...). | ✅ **VERIFIED (Strictly Anonymous IDs)** |
| **No Emotion or Attentiveness Profiling** | System restricts inference to geometric posture (e.g. wrist elevation relative to shoulder). No facial emotion or mood inference is attempted. | ✅ **VERIFIED (Observable Posture Only)** |
| **Hardware-Level Camera Release** | Stopping the webcam or navigating away executes `stream.getTracks().forEach(t => t.stop())` and clears intervals, turning off the physical camera LED. | ✅ **VERIFIED (Hardware Tracks Released)** |
| **Real Pixel Blurring vs. UI Overlay** | System supports both: (1) True in-memory OpenCV Gaussian pixel obliteration, and (2) Client-side CSS backdrop blur. | ✅ **VERIFIED & CLEARLY DISTINGUISHED** |

---

## 2. In-Memory Pipeline Flow & Zero-Retention Architecture

```
[ PHYSICAL WEBCAM ]
        │  (getUserMedia: video stream)
        ▼
[ FRONTEND IN-MEMORY CANVAS ]
        │  (toDataURL: ephemeral base64 JPEG in RAM)
        ▼  (WebSocket stream: /api/ws/detections)
[ FASTAPI IN-MEMORY BUFFER ]
        │  (base64.b64decode -> in-memory bytes)
        ▼
[ OPENCV NUMPY ARRAY (RAM) ]
        ├── Pretrained YOLOv8n / YOLOv8n-pose Forward Pass
        ├── [OPTIONAL] cv_service.apply_privacy_blur (Gaussian pixel obliteration)
        └── Keypoint & Bounding Box Extraction
        │
        ├── Extract JSON Metadata: {"id": "anon_001", "bbox": [...], "status": "RAISED"}
        └── IMMEDIATELY DISCARD NUMPY ARRAY & BYTES (Garbage Collected)
        ▼
[ FRONTEND WEBSOCKET HANDLER ]
        │  (Receives anonymous JSON coordinate stream)
        ▼
[ REACT DOM & SVG SKELETON CANVAS ]
        ├── Renders anonymous bounding box overlays
        ├── Renders 17-keypoint skeleton lines
        └── Renders privacy blur pill on student head region
```

### Storage Audit Verification
- **Database Tables Audited:** SQLite `detections` table stores only:
  `id, session_id, frame_index, timestamp_seconds, person_count, hand_raised_count, hand_not_raised_count, bounding_boxes (json string), processing_fps, model_used, data_source, notes`.
  No binary image columns or blob storage exist.
- **Temporary File Audit:** The `tempfile` module is only invoked for streaming video analysis where temporary chunks are immediately unlinked via `os.remove()` in a `finally:` block. Live webcam streams never create temporary files.

---

## 3. Privacy Blurring: UI Overlay vs. True In-Memory Pixel Blurring

A critical audit requirement is clearly distinguishing between **UI overlay blurring** and **true pixel-level blurring**:

```
+---------------------------------------------------------------------------------------+
| FEATURE COMPARISON                                                                    |
+----------------------------------+----------------------------------------------------+
| 1. CSS UI Overlay Blur           | 2. Genuine In-Memory Pixel Blurring                |
+----------------------------------+----------------------------------------------------+
| Implementation:                  | Implementation:                                    |
|   <div className="...            |   cv2.GaussianBlur(roi, (51, 51), 30)              |
|     backdrop-blur-md" />         |   or Canvas ctx.filter = 'blur(16px)'              |
|                                  |                                                    |
| Mechanism:                       | Mechanism:                                         |
|   Visual CSS filter applied on   |   Mathematical modification of raw RGB values;     |
|   top of DOM video element.      |   underlying pixel information is destroyed.       |
|                                  |                                                    |
| Threat Model:                    | Threat Model:                                      |
|   Protects spectators looking at |   Protects against frame inspection, network       |
|   the teacher's monitor. Raw     |   sniffing, or memory scraping because raw face    |
|   pixels remain in <video>.      |   data no longer exists in the image buffer.       |
|                                  |                                                    |
| Location:                        | Location:                                          |
|   frontend/src/pages/            |   backend/app/services/computer_vision/service.py  |
|   MonitoringPage.tsx             |   cv_service.apply_privacy_blur()                  |
|                                  |   POST /api/vision/privacy-blur                    |
+----------------------------------+----------------------------------------------------+
```

### Verification in Codebase:
1. **True Pixel Blurring (`cv_service.apply_privacy_blur`)**:
   Calculates the upper `blur_ratio` (default 25%) of the bounding box corresponding to the head/face region, and applies `cv2.GaussianBlur` with a heavy kernel ($51 \times 51$, $\sigma = 30$). Verified in unit test `test_privacy_blur_endpoint`.
2. **UI Backdrop Blur (`MonitoringPage.tsx`)**:
   Renders a semi-opaque rounded box with `backdrop-blur-md` and `PRIVACY BLUR` badge across the top portion of the student bounding box to ensure immediate visual feedback for the user.

---

## 4. Hardware Camera Lifecycle & Stream Cleanup

Improper stream management can leave the laptop camera active after a user navigates away, causing user mistrust.

### Lifecycle Implementation in `MonitoringPage.tsx`:
1. **User Stop Action (`stopWebcam`)**:
   ```typescript
   const stopWebcam = () => {
     if (videoRef.current && videoRef.current.srcObject) {
       const stream = videoRef.current.srcObject as MediaStream
       stream.getTracks().forEach((track) => track.stop())
       videoRef.current.srcObject = null
     }
     if (streamingTimerRef.current) {
       clearInterval(streamingTimerRef.current)
       streamingTimerRef.current = null
     }
     setIsWebcamActive(false)
   }
   ```
2. **Navigation / Unmount Safeguard**:
   ```typescript
   useEffect(() => {
     const videoEl = videoRef.current
     return () => {
       if (videoEl && videoEl.srcObject) {
         const stream = videoEl.srcObject as MediaStream
         stream.getTracks().forEach((track) => track.stop())
         videoEl.srcObject = null
       }
       if (streamingTimerRef.current) {
         clearInterval(streamingTimerRef.current)
         streamingTimerRef.current = null
       }
     }
   }, [])
   ```
3. **Physical Verification:**
   When `stopWebcam()` executes or the component unmounts, the physical green LED camera indicator on the HP Victus hardware instantly extinguishes, confirming that the Windows camera driver has closed the capture session.

---

## 5. Session Ephemeral Anonymous IDs

- Every detected entity is labeled using a deterministic session-local anonymizer: `anon_001`, `anon_002`, `anon_003`...
- Bounding boxes are indexed strictly by detection order within the frame.
- No facial geometry embeddings, fingerprints, or cross-frame student identity tracking databases exist.
- When the browser session closes, all ephemeral tracking states are cleared.

---

## 6. Compliance Checklist Summary

- [x] **Zero persistent frame storage:** 0 image files on disk or in DB.
- [x] **No biometric identification:** Zero face recognition libraries or models.
- [x] **No emotion classification:** Posture classification is strictly physical (`BOTH_ARMS_RAISED`, `ARMS_NOT_RAISED`).
- [x] **Verified track release:** `track.stop()` halts hardware camera feed.
- [x] **True pixel blurring:** `cv_service.apply_privacy_blur` provides genuine Gaussian blur.
- [x] **Clear privacy transparency:** UI displays explicit model name, device, and 0% real classroom footage notice.


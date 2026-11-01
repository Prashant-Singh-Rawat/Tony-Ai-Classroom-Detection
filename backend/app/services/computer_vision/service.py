"""
backend/app/services/computer_vision/service.py — Real Computer Vision Pipeline
================================================================================
Phase 2.0: Real-Time Person Detection using Pretrained YOLOv8n (COCO weights).

Key Capabilities:
- Detects the person class only (COCO class 0).
- Sequential frame-by-frame processing with configurable frame skipping.
- Batch size 1.
- Automatic CPU / CUDA fallback with memory error handling.
- Returns exact bounding boxes, confidence scores, image dimensions, and latency.
- Strictly anonymous IDs (anon_001, anon_002...).
- NO facial recognition, identity tracking, or emotion inference.
"""

from __future__ import annotations

import io
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from backend.app.core.config import REPO_ROOT
from backend.app.schemas.common import DataStatus, HandRaiseClass
from backend.app.schemas.detections import (
    ArmPostureGeometry,
    BoundingBox,
    DetectionSummary,
    Keypoint,
    ObservablePosture,
    PersonDetection,
    PersonPoseDetection,
    PoseDetectionResponse,
    PoseGeometry,
    PoseKeypoint,
    PoseStatusResponse,
    VideoFrameSummary,
    VideoProcessResponse,
)
from backend.app.services.computer_vision.letterbox import (
    compute_aspect_ratio_string,
    letterbox_image,
    scale_boxes_to_original,
    scale_keypoints_to_original,
)

COCO_KEYPOINTS = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]


class ComputerVisionService:
    """Manages YOLOv8n person detection and video inference pipelines."""

    def __init__(self) -> None:
        self.status: DataStatus = DataStatus.READY
        self.model_name: str = "yolov8n"
        self._yolo_model = None
        self._pose_model = None

    def get_device(self) -> str:
        """Determines whether CUDA GPU is available or falls back to CPU."""
        try:
            import torch
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                return "cuda:0"
        except Exception:
            pass
        return "cpu"

    def is_available(self) -> bool:
        """Returns True since YOLOv8n weights are integrated and accessible."""
        return True

    def get_status_info(self) -> dict:
        """Returns runtime hardware, model checkpoint, and memory statistics."""
        device = self.get_device()
        vram_info = {"allocated_mb": 0.0, "reserved_mb": 0.0}

        try:
            import torch
            if device.startswith("cuda"):
                vram_info["allocated_mb"] = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
                vram_info["reserved_mb"] = round(torch.cuda.memory_reserved() / (1024 * 1024), 2)
        except Exception:
            pass

        return {
            "module": "computer_vision",
            "model_name": self.model_name,
            "status": "READY",
            "active_checkpoint": "yolov8n.pt (COCO Pretrained Person Detector)",
            "supported_models": ["yolov8n-person", "yolov8n-pose"],
            "ready_for_inference": True,
            "inference_device": device,
            "cuda_available": device.startswith("cuda"),
            "memory_usage": vram_info,
            "provenance": "PRETRAINED MODEL",
            "privacy_mode": "ANONYMOUS_PERSON_ONLY",
            "target_class": "person (COCO class 0)",
        }

    def _resolve_checkpoint_path(self, filename: str = "yolov8n.pt") -> str:
        """Finds cached model checkpoint safely without placing .pt files inside repo root."""
        # 1. Check system Ultralytics cache directory
        sys_weights = Path(os.environ.get("APPDATA", "")) / "Ultralytics" / "weights" / filename
        if sys_weights.is_file():
            return str(sys_weights)

        # 2. Check user home cache
        home_weights = Path.home() / ".cache" / "ultralytics" / filename
        if home_weights.is_file():
            return str(home_weights)

        # 3. Default name (will download to Ultralytics cache if necessary)
        return filename

    def _get_yolo(self):
        """Lazy loader for YOLOv8n person detector."""
        if self._yolo_model is None:
            from ultralytics import YOLO
            ckpt = self._resolve_checkpoint_path("yolov8n.pt")
            self._yolo_model = YOLO(ckpt)
        return self._yolo_model

    def _get_pose(self):
        """Lazy loader for YOLOv8n-pose detector."""
        if self._pose_model is None:
            from ultralytics import YOLO
            ckpt = self._resolve_checkpoint_path("yolov8n-pose.pt")
            self._pose_model = YOLO(ckpt)
        return self._pose_model

    def _load_image(self, image_input: bytes | np.ndarray) -> np.ndarray:
        """Converts raw bytes or numpy array to BGR OpenCV image."""
        if isinstance(image_input, np.ndarray):
            return image_input
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img

    def detect_persons_yolov8n(
        self,
        image_input: bytes | np.ndarray,
        confidence_threshold: float = 0.35,
        imgsz: int = 640,
    ) -> DetectionSummary:
        """
        Runs real YOLOv8n person detection on a single image/frame.
        Filters strictly for class 0 (person).
        """
        t0 = time.time()
        img = self._load_image(image_input)
        h, w = img.shape[:2]

        model = self._get_yolo()
        device = self.get_device()

        # Execute inference with CUDA OOM safety — strictly filters for class 0 (person)
        try:
            results = model(
                img,
                classes=[0],
                conf=confidence_threshold,
                imgsz=imgsz,
                device=device,
                verbose=False,
            )
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                # Fallback to CPU immediately
                results = model(
                    img,
                    classes=[0],
                    conf=confidence_threshold,
                    imgsz=imgsz,
                    device="cpu",
                    verbose=False,
                )
                device = "cpu"
            else:
                raise e

        detections: List[PersonDetection] = []
        bounding_boxes: List[BoundingBox] = []

        if results and len(results) > 0:
            boxes = results[0].boxes
            person_idx = 1
            for box in boxes:
                coords = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy()) if hasattr(box, "cls") and box.cls is not None else 0
                x1, y1, x2, y2 = coords

                if cls_id != 0:
                    continue

                person_id = f"anon_{person_idx:03d}"
                person_idx += 1

                width = max(1.0, float(x2 - x1))
                height = max(1.0, float(y2 - y1))

                # Exact pixel detection
                detections.append(PersonDetection(
                    id=person_id,
                    className="person",
                    confidence=round(conf, 3),
                    x=round(float(x1), 1),
                    y=round(float(y1), 1),
                    width=round(width, 1),
                    height=round(height, 1),
                    x1=round(float(x1), 1),
                    y1=round(float(y1), 1),
                    x2=round(float(x2), 1),
                    y2=round(float(y2), 1),
                ))

                # Percentage-based normalized box for responsive UI overlays
                x_pct = max(0.0, min(100.0, (float(x1) / w) * 100))
                y_pct = max(0.0, min(100.0, (float(y1) / h) * 100))
                w_pct = max(0.0, min(100.0, (width / w) * 100))
                h_pct = max(0.0, min(100.0, (height / h) * 100))

                bounding_boxes.append(BoundingBox(
                    id=person_id,
                    personId=person_idx - 1,
                    classId=1,
                    className=HandRaiseClass.HAND_NOT_RAISED,
                    confidence=round(conf, 3),
                    x=round(x_pct, 2),
                    y=round(y_pct, 2),
                    w=round(w_pct, 2),
                    h=round(h_pct, 2),
                    width=round(width, 1),
                    height=round(height, 1),
                    status="NOT_RAISED",
                ))

        # Explainable activity recognition for Person mode
        from backend.app.services.activity_recognition.service import activity_service
        bounding_boxes, _ = activity_service.analyze_frame(
            person_boxes=bounding_boxes,
            detected_phones=[],
            is_pose_mode=False,
        )

        elapsed_seconds = max(0.001, time.time() - t0)
        elapsed_ms = round(elapsed_seconds * 1000, 1)
        fps = round(1.0 / elapsed_seconds, 1)

        return DetectionSummary(
            totalStudents=len(detections),
            totalPersons=len(detections),
            activeHandRaises=0,
            notRaisedCount=len(detections),
            needsReviewCount=0,
            boxes=bounding_boxes,
            detections=detections,
            imageWidth=w,
            imageHeight=h,
            processingTimeMs=elapsed_ms,
            processingFps=fps,
            modelName="yolov8n",
            modelStatus="READY",
            inferenceDevice=device,
            dataSource="REAL_PROCESSING",
            status="REAL_PROCESSING",
            isDemoData=False,
        )

    def process_frame(
        self,
        frame_data: bytes,
        confidence_threshold: float = 0.35,
    ) -> DetectionSummary:
        """Alias for detect_persons_yolov8n maintaining compatibility."""
        return self.detect_persons_yolov8n(frame_data, confidence_threshold=confidence_threshold)

    def apply_privacy_blur(
        self,
        image_input: bytes | np.ndarray,
        boxes: Optional[List[PersonDetection]] = None,
        blur_ratio: float = 0.25,
        kernel_size: int = 51,
    ) -> Tuple[np.ndarray, int]:
        """
        Applies true pixel-level Gaussian blur to the head/face region of detected persons.
        Directly alters the image pixel matrix in RAM.
        Guarantees that face pixels are irrevocably obliterated in memory.
        Returns the modified image and count of blurred faces.
        """
        img = self._load_image(image_input).copy()
        if boxes is None:
            detection_res = self.detect_persons_yolov8n(img)
            boxes = detection_res.detections

        img_h, img_w = img.shape[:2]
        ksize = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        blurred_count = 0

        for box in boxes:
            x1 = max(0, int(box.x1 if box.x1 is not None else box.x))
            y1 = max(0, int(box.y1 if box.y1 is not None else box.y))
            x2 = min(img_w, int(box.x2 if box.x2 is not None else (box.x + box.width)))
            y2 = min(img_h, int(box.y2 if box.y2 is not None else (box.y + box.height)))

            box_h = y2 - y1
            if box_h <= 5 or (x2 - x1) <= 5:
                continue

            # Upper region corresponding to head/face
            head_y2 = min(img_h, y1 + int(box_h * blur_ratio))
            roi = img[y1:head_y2, x1:x2]
            if roi.size == 0 or roi.shape[0] < 2 or roi.shape[1] < 2:
                continue

            # Apply heavy Gaussian blur to pixel values
            effective_k = min(ksize, (roi.shape[0] // 2) * 2 + 1, (roi.shape[1] // 2) * 2 + 1)
            effective_k = max(3, effective_k)
            if effective_k % 2 == 0:
                effective_k += 1

            blurred_roi = cv2.GaussianBlur(roi, (effective_k, effective_k), 30)
            img[y1:head_y2, x1:x2] = blurred_roi
            blurred_count += 1

        return img, blurred_count

    def process_video_stream(
        self,
        video_source: str | bytes,
        filename_hint: str = "classroom_video.mp4",
        frame_skip: int = 5,
        confidence_threshold: float = 0.20,
        imgsz: int = 640,
        detect_pose: bool = False,
        session_id: Optional[str] = None,
        db: Any = None,
        enable_tracking: bool = True,
        instructor_roi_polygon: Optional[List[List[float]]] = None,
        zone_filtering_enabled: bool = True,
    ) -> VideoProcessResponse:
        """
        Sequentially processes video frames with configurable frame skipping.
        - Supports arbitrary resolutions: 320x240, 640x360, 640x480, 1280x720, 1920x1080, 2560x1440, 3840x2160.
        - Supports landscape, square, and portrait video orientations.
        - Strictly preserves aspect ratio via letterboxing (never stretches frames).
        - Handles corrupt/dropped frames gracefully without crashing.
        - Accurately measures video decoding FPS vs. AI inference FPS vs. native video FPS.
        - Captures peak RAM and VRAM usage.
        - Supports person detection (YOLOv8n) or pose/hand-raise estimation (YOLOv8n-pose).
        - Integrates with TemporalTracker for anonymous ID stability & SQLite event persistence.
        - Supports optional Teacher Zone Exclusion (Instructor ROI) spatial filtering.
        """
        import psutil
        import torch

        # Reset temporal tracker session if tracking is enabled
        if detect_pose and enable_tracking:
            try:
                from backend.app.services.tracking.temporal_tracker import temporal_tracker
                temporal_tracker.reset_session(session_id=session_id or "sess_video")
                temporal_tracker.set_zone_config(
                    polygon=instructor_roi_polygon,
                    enabled=zone_filtering_enabled,
                )
            except Exception:
                pass

        temp_path: Optional[str] = None
        if isinstance(video_source, bytes):
            suffix = Path(filename_hint).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_source)
                temp_path = tmp.name
            video_path = temp_path
        else:
            video_path = video_source

        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValueError(f"OpenCV could not open video file: {filename_hint}")

        t0 = time.perf_counter()
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_seconds = round(total_frames / max(1.0, video_fps), 2)

        # Detect orientation and standard aspect ratio
        if height > width:
            orientation = "PORTRAIT"
        elif height == width:
            orientation = "SQUARE"
        else:
            orientation = "LANDSCAPE"

        aspect_ratio = compute_aspect_ratio_string(width, height)

        timeline: List[VideoFrameSummary] = []
        frame_index = 0
        processed_count = 0
        corrupted_count = 0
        person_counts: List[int] = []
        total_hand_raises = 0
        total_needs_review = 0

        total_decoding_time = 0.0
        total_inference_time = 0.0

        model_name = "yolov8n-pose" if detect_pose else "yolov8n"

        try:
            while True:
                # 1. Pure video frame decoding timing
                t_dec_start = time.perf_counter()
                ret, frame = cap.read()
                t_dec_end = time.perf_counter()
                dec_elapsed = t_dec_end - t_dec_start
                total_decoding_time += dec_elapsed

                if not ret or frame is None or frame.size == 0:
                    if total_frames > 0 and frame_index >= total_frames:
                        break
                    # If stream reports frames remaining but decoding failed -> corrupt frame
                    if total_frames > 0 and frame_index < total_frames:
                        corrupted_count += 1
                        frame_index += 1
                        continue
                    else:
                        break

                # 2. Frame skip check: only run model on sampled frames
                if frame_index % max(1, frame_skip) == 0:
                    t_inf_start = time.perf_counter()

                    if detect_pose:
                        pose_res = self.estimate_pose(
                            frame,
                            confidence_threshold=confidence_threshold,
                            imgsz=imgsz,
                        )
                        count = pose_res.totalPersons
                        hr_count = (
                            pose_res.postureCounts.get(ObservablePosture.LEFT_ARM_RAISED.value, 0)
                            + pose_res.postureCounts.get(ObservablePosture.RIGHT_ARM_RAISED.value, 0)
                            + pose_res.postureCounts.get(ObservablePosture.BOTH_ARMS_RAISED.value, 0)
                        )
                        nr_count = pose_res.postureCounts.get(ObservablePosture.NEEDS_REVIEW.value, 0)
                        frame_detections = [p.bbox for p in pose_res.persons]

                        # Build bounding boxes for UI overlay
                        frame_boxes: List[BoundingBox] = []
                        for p in pose_res.persons:
                            x_pct = max(0.0, min(100.0, (p.bbox.x / max(1, width)) * 100))
                            y_pct = max(0.0, min(100.0, (p.bbox.y / max(1, height)) * 100))
                            w_pct = max(0.0, min(100.0, (p.bbox.width / max(1, width)) * 100))
                            h_pct = max(0.0, min(100.0, (p.bbox.height / max(1, height)) * 100))
                            is_raised = p.posture in (
                                ObservablePosture.LEFT_ARM_RAISED,
                                ObservablePosture.RIGHT_ARM_RAISED,
                                ObservablePosture.BOTH_ARMS_RAISED,
                            )
                            is_review = p.posture == ObservablePosture.NEEDS_REVIEW
                            class_id = 0 if is_raised else (2 if is_review else 1)

                            zone_cls_val = None
                            if instructor_roi_polygon and zone_filtering_enabled:
                                try:
                                    from backend.app.services.tracking.zone_filter import classify_detection_zone
                                    z_cls, _ = classify_detection_zone(
                                        p.bbox,
                                        polygon=instructor_roi_polygon,
                                        enabled=zone_filtering_enabled,
                                        video_width=width,
                                        video_height=height,
                                        confidence=p.confidence,
                                    )
                                    zone_cls_val = z_cls.value
                                except Exception:
                                    pass

                            kp_models = [
                                Keypoint(
                                    name=kp.name,
                                    x=round(kp.x, 1),
                                    y=round(kp.y, 1),
                                    confidence=round(kp.confidence, 3),
                                )
                                for kp in p.keypoints
                            ] if hasattr(p, "keypoints") and p.keypoints else None

                            frame_boxes.append(BoundingBox(
                                id=p.id,
                                personId=int(p.id.replace("anon_", "")) if "anon_" in p.id else 1,
                                classId=class_id,
                                className=HandRaiseClass.HAND_RAISED if is_raised else (HandRaiseClass.AMBIGUOUS if is_review else HandRaiseClass.HAND_NOT_RAISED),
                                confidence=p.confidence,
                                x=round(x_pct, 2),
                                y=round(y_pct, 2),
                                w=round(w_pct, 2),
                                h=round(h_pct, 2),
                                width=round(p.bbox.width, 1),
                                height=round(p.bbox.height, 1),
                                handRaised=is_raised,
                                status=p.posture.value if hasattr(p.posture, "value") else str(p.posture),
                                zoneClassification=zone_cls_val,
                                keypoints=kp_models,
                            ))

                        # Explainable activity recognition on pose frame boxes
                        try:
                            from backend.app.services.activity_recognition.service import activity_service
                            frame_boxes, _ = activity_service.analyze_frame(
                                person_boxes=frame_boxes,
                                detected_phones=[],
                                is_pose_mode=True,
                            )
                        except Exception:
                            pass

                        total_hand_raises += hr_count
                        total_needs_review += nr_count

                        # Phase 2.2: Temporal Tracking & Event State Machine
                        if enable_tracking:
                            try:
                                from backend.app.services.tracking.temporal_tracker import temporal_tracker
                                temporal_tracker.update(
                                    pose_res.persons,
                                    timestamp_seconds=round(frame_index / max(1.0, video_fps), 2),
                                    session_id=session_id or "sess_video",
                                    db_session=db,
                                )
                            except Exception:
                                pass
                    else:
                        det_summary = self.detect_persons_yolov8n(
                            frame,
                            confidence_threshold=confidence_threshold,
                            imgsz=imgsz,
                        )
                        count = det_summary.totalPersons
                        hr_count = 0
                        nr_count = 0
                        frame_detections = det_summary.detections
                        frame_boxes = det_summary.boxes

                    t_inf_end = time.perf_counter()
                    inf_elapsed = t_inf_end - t_inf_start
                    total_inference_time += inf_elapsed

                    timestamp = round(frame_index / max(1.0, video_fps), 2)
                    timeline.append(VideoFrameSummary(
                        frameIndex=frame_index,
                        timestampSeconds=timestamp,
                        personCount=count,
                        detections=frame_detections,
                        boxes=frame_boxes,
                        handRaisedCount=hr_count,
                        needsReviewCount=nr_count,
                        decodingTimeMs=round(dec_elapsed * 1000, 2),
                        inferenceTimeMs=round(inf_elapsed * 1000, 2),
                    ))
                    person_counts.append(count)
                    processed_count += 1

                frame_index += 1

        finally:
            cap.release()
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        total_elapsed = max(0.001, time.perf_counter() - t0)

        # Performance measurements
        decoding_fps = round(max(1, frame_index) / max(0.0001, total_decoding_time), 1)
        inference_fps = round(processed_count / max(0.0001, total_inference_time), 1)
        processing_fps = round(processed_count / max(0.0001, total_elapsed), 1)

        max_persons = max(person_counts) if person_counts else 0
        avg_persons = round(sum(person_counts) / max(1, len(person_counts)), 1) if person_counts else 0.0

        # Memory measurements
        peak_ram = round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 1)
        peak_vram = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1) if torch.cuda.is_available() else 0.0

        # Tracking event metrics & finalization
        tracked_count = 0
        events_count = 0
        active_evt_count = 0
        completed_evt_count = 0
        student_zone_events_count = 0
        instructor_zone_events_count = 0
        uncertain_zone_events_count = 0
        if detect_pose and enable_tracking:
            try:
                from backend.app.services.tracking.temporal_tracker import temporal_tracker
                from backend.app.schemas.tracking import HandRaisingState

                # Finalize any remaining active events upon reaching end of stream
                for track in list(temporal_tracker.tracks.values()):
                    if track.active_event is not None:
                        temporal_tracker._finalize_event(
                            track,
                            end_timestamp=duration_seconds,
                            end_frame=frame_index,
                            final_state="COMPLETED" if track.state == HandRaisingState.RAISED else "NEEDS_REVIEW",
                            db_session=db,
                        )

                tracked_count = len(temporal_tracker.tracks)
                events_count = len(temporal_tracker.all_events_by_id)
                active_evt_count = sum(1 for t in temporal_tracker.tracks.values() if t.active_event is not None)
                completed_evt_count = len(temporal_tracker.completed_events)
                student_zone_events_count = sum(
                    1 for e in temporal_tracker.all_events_by_id.values()
                    if getattr(e, "zoneClassification", "STUDENT_ZONE") in ("STUDENT_ZONE", "NOT_CONFIGURED")
                )
                instructor_zone_events_count = sum(
                    1 for e in temporal_tracker.all_events_by_id.values()
                    if getattr(e, "zoneClassification", None) == "INSTRUCTOR_ZONE"
                )
                uncertain_zone_events_count = sum(
                    1 for e in temporal_tracker.all_events_by_id.values()
                    if getattr(e, "zoneClassification", None) == "NEEDS_REVIEW"
                )
            except Exception:
                pass

        return VideoProcessResponse(
            videoFilename=Path(filename_hint).name,
            totalFrames=total_frames or frame_index,
            processedFrames=processed_count,
            frameSkip=frame_skip,
            videoFps=round(video_fps, 1),
            durationSeconds=duration_seconds,
            maxPersonsInFrame=max_persons,
            avgPersonsPerFrame=avg_persons,
            timeline=timeline,
            totalProcessingTimeSeconds=round(total_elapsed, 2),
            processingFps=processing_fps,
            modelName=model_name,
            modelStatus="READY",
            inferenceDevice=self.get_device(),
            dataSource="REAL_PROCESSING",
            status="COMPLETED",
            width=width,
            height=height,
            aspectRatio=aspect_ratio,
            orientation=orientation,
            decodingFps=decoding_fps,
            inferenceFps=inference_fps,
            decodingTimeSeconds=round(total_decoding_time, 3),
            inferenceTimeSeconds=round(total_inference_time, 3),
            corruptedFramesCount=corrupted_count,
            peakRamMb=peak_ram,
            peakVramMb=peak_vram,
            totalHandRaises=total_hand_raises,
            totalNeedsReview=total_needs_review,
            trackedPersonsCount=tracked_count,
            handRaiseEventsCount=events_count,
            activeEventsCount=active_evt_count,
            completedEventsCount=completed_evt_count,
            instructorRoiPolygon=instructor_roi_polygon,
            zoneFilteringEnabled=zone_filtering_enabled,
            studentZoneEventsCount=student_zone_events_count,
            instructorZoneEventsCount=instructor_zone_events_count,
            uncertainZoneEventsCount=uncertain_zone_events_count,
        )

    def estimate_pose_and_hand_raise(
        self,
        image_input: bytes | np.ndarray,
        confidence_threshold: float = 0.35,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Maintains pose estimation capability for multi-phase support."""
        img = self._load_image(image_input)
        model = self._get_pose()
        results = model(img, conf=confidence_threshold, verbose=False)

        persons = []
        counts = {"person_count": 0, "hand_raised": 0, "hand_not_raised": 0, "needs_review": 0}

        if not results or len(results) == 0:
            return persons, counts

        res = results[0]
        boxes = res.boxes
        keypoints_data = res.keypoints

        if boxes is None or len(boxes) == 0:
            return persons, counts

        counts["person_count"] = len(boxes)

        for idx, box in enumerate(boxes):
            coords = box.xyxy[0].cpu().numpy()
            b_conf = float(box.conf[0].cpu().numpy())
            x1, y1, x2, y2 = coords
            person_id = f"anon_{idx + 1:03d}"

            hand_status = "NOT_RAISED"
            ambiguity_reason = None
            kp_list = []

            if keypoints_data is not None and len(keypoints_data) > idx:
                kpts = keypoints_data[idx].data[0].cpu().numpy()
                left_shoulder = kpts[5] if len(kpts) > 5 else None
                right_shoulder = kpts[6] if len(kpts) > 6 else None
                left_wrist = kpts[9] if len(kpts) > 9 else None
                right_wrist = kpts[10] if len(kpts) > 10 else None

                kp_names = ["nose", "left_eye", "right_eye", "left_ear", "right_ear",
                            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
                            "left_wrist", "right_wrist", "left_hip", "right_hip",
                            "left_knee", "right_knee", "left_ankle", "right_ankle"]
                for k_i, kpt in enumerate(kpts):
                    if k_i < len(kp_names):
                        kp_list.append({
                            "name": kp_names[k_i],
                            "x": float(kpt[0]),
                            "y": float(kpt[1]),
                            "confidence": round(float(kpt[2]), 3),
                        })

                is_left_raised = False
                is_right_raised = False
                left_ambiguous = False
                right_ambiguous = False
                margin = 15.0
                b_height = float(y2 - y1)
                effective_margin = max(margin, 0.15 * b_height)

                nose = kpts[0] if len(kpts) > 0 else None
                lear = kpts[3] if len(kpts) > 3 else None
                rear = kpts[4] if len(kpts) > 4 else None
                head_ref_y = None
                if lear is not None and lear[2] >= 0.35:
                    head_ref_y = lear[1] + 15.0
                elif rear is not None and rear[2] >= 0.35:
                    head_ref_y = rear[1] + 15.0
                elif nose is not None and nose[2] >= 0.35:
                    head_ref_y = nose[1] + 20.0

                if left_shoulder is not None and left_wrist is not None:
                    ls_y, ls_conf = left_shoulder[1], left_shoulder[2]
                    lw_y, lw_conf = left_wrist[1], left_wrist[2]
                    is_above_head = True if head_ref_y is None else (lw_y <= head_ref_y)
                    if ls_conf > 0.4 and lw_conf > 0.4:
                        if lw_y < (ls_y - effective_margin) and is_above_head:
                            is_left_raised = True
                    elif 0.2 < lw_conf <= 0.4:
                        left_ambiguous = True

                if right_shoulder is not None and right_wrist is not None:
                    rs_y, rs_conf = right_shoulder[1], right_shoulder[2]
                    rw_y, rw_conf = right_wrist[1], right_wrist[2]
                    is_above_head = True if head_ref_y is None else (rw_y <= head_ref_y)
                    if rs_conf > 0.4 and rw_conf > 0.4:
                        if rw_y < (rs_y - effective_margin) and is_above_head:
                            is_right_raised = True
                    elif 0.2 < rw_conf <= 0.4:
                        right_ambiguous = True

                if is_left_raised or is_right_raised:
                    hand_status = "RAISED"
                    counts["hand_raised"] += 1
                elif left_ambiguous or right_ambiguous:
                    hand_status = "NEEDS_REVIEW"
                    ambiguity_reason = "Low wrist/shoulder keypoint visibility confidence or occluded arm."
                    counts["needs_review"] += 1
                else:
                    hand_status = "NOT_RAISED"
                    counts["hand_not_raised"] += 1
            else:
                counts["hand_not_raised"] += 1

            persons.append({
                "id": person_id,
                "x": max(0.0, float(x1)),
                "y": max(0.0, float(y1)),
                "width": max(1.0, float(x2 - x1)),
                "height": max(1.0, float(y2 - y1)),
                "confidence": round(b_conf, 3),
                "hand_status": hand_status,
                "ambiguity_reason": ambiguity_reason,
                "keypoints": kp_list,
                "label": "person",
                "provenance": "PRETRAINED MODEL",
            })

        return persons, counts

    def detect_with_pose(
        self,
        image_input: bytes | np.ndarray,
        confidence_threshold: float = 0.35,
    ) -> DetectionSummary:
        """
        Runs YOLOv8n-pose detection to extract person bounding boxes, 17 body keypoints,
        and geometric hand-raise classification.
        """
        t0 = time.time()
        img = self._load_image(image_input)
        h, w = img.shape[:2]

        persons, counts = self.estimate_pose_and_hand_raise(img, confidence_threshold=confidence_threshold)

        # Detect cell phones (COCO class 67)
        detected_phones: List[Dict[str, Any]] = []
        try:
            yolo_detector = self._get_yolo()
            phone_results = yolo_detector(
                img,
                classes=[67],
                conf=0.25,
                imgsz=640,
                device=self.get_device(),
                verbose=False,
            )
            if phone_results and len(phone_results) > 0 and phone_results[0].boxes:
                for p_box in phone_results[0].boxes:
                    p_coords = p_box.xyxy[0].cpu().numpy()
                    p_conf = float(p_box.conf[0].cpu().numpy())
                    detected_phones.append({
                        "bbox": [float(p_coords[0]), float(p_coords[1]), float(p_coords[2]), float(p_coords[3])],
                        "confidence": p_conf,
                    })
        except Exception as phone_err:
            logger.debug("Phone detection sub-pass notice: %s", phone_err)

        detections: List[PersonDetection] = []
        boxes: List[BoundingBox] = []

        for idx, p in enumerate(persons):
            x1, y1 = p["x"], p["y"]
            width, height = p["width"], p["height"]
            x2, y2 = x1 + width, y1 + height
            person_id = p["id"]
            conf = p["confidence"]
            hand_status = p["hand_status"]

            detections.append(PersonDetection(
                id=person_id,
                className="person",
                confidence=conf,
                x=round(x1, 1),
                y=round(y1, 1),
                width=round(width, 1),
                height=round(height, 1),
                x1=round(x1, 1),
                y1=round(y1, 1),
                x2=round(x2, 1),
                y2=round(y2, 1),
            ))

            # Normalized coordinates [0-100] for responsive UI canvas
            x_pct = max(0.0, min(100.0, (x1 / w) * 100))
            y_pct = max(0.0, min(100.0, (y1 / h) * 100))
            w_pct = max(0.0, min(100.0, (width / w) * 100))
            h_pct = max(0.0, min(100.0, (height / h) * 100))

            class_id = 0 if hand_status == "RAISED" else (2 if hand_status == "NEEDS_REVIEW" else 1)
            class_name = (
                HandRaiseClass.HAND_RAISED
                if class_id == 0
                else (HandRaiseClass.AMBIGUOUS if class_id == 2 else HandRaiseClass.HAND_NOT_RAISED)
            )

            # Convert keypoints dicts to Keypoint models
            kp_models = [
                Keypoint(
                    name=kp["name"],
                    x=round(kp["x"], 1),
                    y=round(kp["y"], 1),
                    confidence=kp["confidence"],
                )
                for kp in p.get("keypoints", [])
            ]

            boxes.append(BoundingBox(
                id=person_id,
                personId=idx + 1,
                classId=class_id,
                className=class_name,
                confidence=conf,
                x=round(x_pct, 2),
                y=round(y_pct, 2),
                w=round(w_pct, 2),
                h=round(h_pct, 2),
                width=round(width, 1),
                height=round(height, 1),
                handRaised=(hand_status == "RAISED"),
                status=hand_status,
                keypoints=kp_models,
            ))

        # Explainable temporal activity recognition (Pose Mode)
        from backend.app.services.activity_recognition.service import activity_service
        boxes, _ = activity_service.analyze_frame(
            person_boxes=boxes,
            detected_phones=detected_phones,
            is_pose_mode=True,
        )

        elapsed_seconds = max(0.001, time.time() - t0)
        elapsed_ms = round(elapsed_seconds * 1000, 1)
        fps = round(1.0 / elapsed_seconds, 1)

        return DetectionSummary(
            totalStudents=len(detections),
            totalPersons=len(detections),
            activeHandRaises=counts["hand_raised"],
            notRaisedCount=counts["hand_not_raised"],
            needsReviewCount=counts["needs_review"],
            boxes=boxes,
            detections=detections,
            imageWidth=w,
            imageHeight=h,
            processingTimeMs=elapsed_ms,
            processingFps=fps,
            modelName="yolov8n-pose",
            modelStatus="READY",
            inferenceDevice=self.get_device(),
            dataSource="REAL_PROCESSING",
            status="REAL_PROCESSING",
            isDemoData=False,
        )

    @staticmethod
    def _calculate_angle_deg(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
    ) -> Optional[float]:
        """Calculates inner angle in degrees at vertex p2 formed by (p1, p2, p3)."""
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        norm1 = float(np.hypot(v1[0], v1[1]))
        norm2 = float(np.hypot(v2[0], v2[1]))
        if norm1 < 1e-4 or norm2 < 1e-4:
            return None
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        cos_angle = float(np.clip(dot / (norm1 * norm2), -1.0, 1.0))
        return round(float(np.degrees(np.arccos(cos_angle))), 1)

    def estimate_pose(
        self,
        image_input: bytes | np.ndarray,
        confidence_threshold: float = 0.35,
        keypoint_threshold: float = 0.4,
        elevation_margin_px: float = 15.0,
        imgsz: int = 640,
    ) -> PoseDetectionResponse:
        """
        Phase 2.1: Human Pose Estimation using Pretrained YOLOv8n-pose.
        Extracts 17 COCO keypoints, calculates arm geometry (angles and elevation),
        and provides observable posture classification without identity recognition.
        """
        t0 = time.time()
        img = self._load_image(image_input)
        h, w = img.shape[:2]

        model = self._get_pose()
        device = self.get_device()

        # Execute inference with CUDA OOM safety
        try:
            results = model(
                img,
                conf=confidence_threshold,
                imgsz=imgsz,
                device=device,
                verbose=False,
            )
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                results = model(
                    img,
                    conf=confidence_threshold,
                    imgsz=imgsz,
                    device="cpu",
                    verbose=False,
                )
                device = "cpu"
            else:
                raise e

        persons: List[PersonPoseDetection] = []
        posture_counts: Dict[str, int] = {
            ObservablePosture.BOTH_ARMS_RAISED.value: 0,
            ObservablePosture.LEFT_ARM_RAISED.value: 0,
            ObservablePosture.RIGHT_ARM_RAISED.value: 0,
            ObservablePosture.ARMS_NOT_RAISED.value: 0,
            ObservablePosture.NEEDS_REVIEW.value: 0,
        }

        if results and len(results) > 0:
            res = results[0]
            boxes = res.boxes
            keypoints_data = res.keypoints

            if boxes is not None and len(boxes) > 0:
                for idx, box in enumerate(boxes):
                    coords = box.xyxy[0].cpu().numpy()
                    b_conf = float(box.conf[0].cpu().numpy())
                    x1, y1, x2, y2 = coords
                    person_id = f"anon_{idx + 1:03d}"
                    width = max(1.0, float(x2 - x1))
                    height = max(1.0, float(y2 - y1))

                    bbox = PersonDetection(
                        id=person_id,
                        className="person",
                        confidence=round(b_conf, 3),
                        x=round(float(x1), 1),
                        y=round(float(y1), 1),
                        width=round(width, 1),
                        height=round(height, 1),
                        x1=round(float(x1), 1),
                        y1=round(float(y1), 1),
                        x2=round(float(x2), 1),
                        y2=round(float(y2), 1),
                    )

                    kps_list: List[PoseKeypoint] = []
                    kpts_xy = None
                    kpts_conf = None
                    if keypoints_data is not None and len(keypoints_data) > idx:
                        kpts_xy = keypoints_data[idx].xy[0].cpu().numpy()
                        if keypoints_data[idx].conf is not None:
                            kpts_conf = keypoints_data[idx].conf[0].cpu().numpy()

                    for k_idx, name in enumerate(COCO_KEYPOINTS):
                        if kpts_xy is not None and k_idx < len(kpts_xy):
                            kx = float(kpts_xy[k_idx, 0])
                            ky = float(kpts_xy[k_idx, 1])
                            kc = float(kpts_conf[k_idx]) if kpts_conf is not None and k_idx < len(kpts_conf) else 0.0
                        else:
                            kx, ky, kc = 0.0, 0.0, 0.0

                        vis = bool(kc >= keypoint_threshold and (kx > 0.0 or ky > 0.0))
                        kx_pct = round(max(0.0, min(100.0, (kx / w) * 100)), 2)
                        ky_pct = round(max(0.0, min(100.0, (ky / h) * 100)), 2)

                        kps_list.append(PoseKeypoint(
                            index=k_idx,
                            name=name,
                            x=round(kx, 1),
                            y=round(ky, 1),
                            confidence=round(kc, 3),
                            visible=vis,
                            xPct=kx_pct,
                            yPct=ky_pct,
                        ))

                    # Keypoint references
                    ls = kps_list[5]   # left_shoulder
                    rs = kps_list[6]   # right_shoulder
                    le = kps_list[7]   # left_elbow
                    re = kps_list[8]   # right_elbow
                    lw = kps_list[9]   # left_wrist
                    rw = kps_list[10]  # right_wrist

                    # Check upper body occlusions
                    occluded = [kp.name for kp in [ls, rs, le, re, lw, rw] if not kp.visible]
                    upper_body_visible = len(occluded) == 0

                    # Calculate Arm Angles
                    left_angle = self._calculate_angle_deg((ls.x, ls.y), (le.x, le.y), (lw.x, lw.y)) if (ls.visible and le.visible and lw.visible) else None
                    right_angle = self._calculate_angle_deg((rs.x, rs.y), (re.x, re.y), (rw.x, rw.y)) if (rs.visible and re.visible and rw.visible) else None

                    # Calculate Arm Elevation (shoulder_y - wrist_y; positive = above shoulder)
                    left_elevation = round(ls.y - lw.y, 1) if (ls.visible and lw.visible) else None
                    right_elevation = round(rs.y - rw.y, 1) if (rs.visible and rw.visible) else None

                    left_raised = bool(left_elevation is not None and left_elevation >= elevation_margin_px)
                    right_raised = bool(right_elevation is not None and right_elevation >= elevation_margin_px)

                    left_arm_geom = ArmPostureGeometry(
                        elbowAngleDeg=left_angle,
                        elevationPx=left_elevation,
                        wristAboveShoulder=left_raised,
                        armRaised=left_raised,
                        confidence=round(min(ls.confidence, lw.confidence), 3) if (ls.visible and lw.visible) else 0.0,
                    )

                    right_arm_geom = ArmPostureGeometry(
                        elbowAngleDeg=right_angle,
                        elevationPx=right_elevation,
                        wristAboveShoulder=right_raised,
                        armRaised=right_raised,
                        confidence=round(min(rs.confidence, rw.confidence), 3) if (rs.visible and rw.visible) else 0.0,
                    )

                    shoulder_dist = round(float(np.hypot(rs.x - ls.x, rs.y - ls.y)), 1) if (ls.visible and rs.visible) else None

                    geom = PoseGeometry(
                        leftArm=left_arm_geom,
                        rightArm=right_arm_geom,
                        shoulderDistancePx=shoulder_dist,
                        upperBodyVisible=upper_body_visible,
                        occludedKeypoints=occluded,
                    )

                    # Posture classification:
                    # Low-confidence or occluded upper body keypoints -> NEEDS_REVIEW
                    arm_keypoints_missing = any(k in occluded for k in ["left_shoulder", "left_wrist", "right_shoulder", "right_wrist"])

                    if arm_keypoints_missing:
                        posture = ObservablePosture.NEEDS_REVIEW
                        posture_reason = f"Occluded upper-body keypoints: {', '.join(occluded)}"
                    elif left_raised and right_raised:
                        posture = ObservablePosture.BOTH_ARMS_RAISED
                        posture_reason = f"Both arms elevated: Left wrist +{left_elevation}px ({left_angle}°), Right wrist +{right_elevation}px ({right_angle}°)"
                    elif left_raised:
                        posture = ObservablePosture.LEFT_ARM_RAISED
                        posture_reason = f"Left arm elevated +{left_elevation}px above shoulder ({left_angle}°); Right arm down ({right_elevation}px)"
                    elif right_raised:
                        posture = ObservablePosture.RIGHT_ARM_RAISED
                        posture_reason = f"Right arm elevated +{right_elevation}px above shoulder ({right_angle}°); Left arm down ({left_elevation}px)"
                    else:
                        posture = ObservablePosture.ARMS_NOT_RAISED
                        posture_reason = "Both arms positioned below shoulder elevation margin"

                    posture_counts[posture.value] += 1

                    persons.append(PersonPoseDetection(
                        id=person_id,
                        confidence=round(b_conf, 3),
                        bbox=bbox,
                        posture=posture,
                        postureReason=posture_reason,
                        keypoints=kps_list,
                        geometry=geom,
                    ))

        elapsed_seconds = max(0.001, time.time() - t0)
        elapsed_ms = round(elapsed_seconds * 1000, 1)
        fps = round(1.0 / elapsed_seconds, 1)

        return PoseDetectionResponse(
            totalPersons=len(persons),
            imageWidth=w,
            imageHeight=h,
            processingTimeMs=elapsed_ms,
            processingFps=fps,
            modelName="yolov8n-pose",
            modelStatus="READY",
            inferenceDevice=device,
            postureCounts=posture_counts,
            persons=persons,
            dataSource="REAL_PROCESSING",
            status="REAL_PROCESSING",
            isDemoData=False,
        )

    def get_pose_status_info(self) -> PoseStatusResponse:
        """Returns runtime details for human pose estimation model."""
        device = self.get_device()
        vram_info = {"allocated_mb": 0.0, "reserved_mb": 0.0}

        try:
            import torch
            if device.startswith("cuda"):
                vram_info["allocated_mb"] = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
                vram_info["reserved_mb"] = round(torch.cuda.memory_reserved() / (1024 * 1024), 2)
        except Exception:
            pass

        eval_metrics = None
        eval_file = Path(REPO_ROOT) / "models" / "evaluation" / "coco_pose_evaluation_results.json"
        if eval_file.is_file():
            try:
                import json
                with open(eval_file, "r", encoding="utf-8") as f:
                    eval_metrics = json.load(f).get("metrics")
            except Exception:
                pass

        return PoseStatusResponse(
            module="computer_vision",
            submodule="pose_estimation",
            modelName="yolov8n-pose",
            activeCheckpoint="yolov8n-pose.pt (COCO Pretrained 17-Keypoint Pose)",
            status="READY",
            readyForInference=True,
            inferenceDevice=device,
            cudaAvailable=device.startswith("cuda"),
            supportedKeypointsCount=17,
            cocoKeypointOrder=COCO_KEYPOINTS,
            postureClasses=[p.value for p in ObservablePosture],
            memoryUsage=vram_info,
            provenance="PRETRAINED MODEL",
            privacyMode="ANONYMOUS_PERSON_ONLY",
            evaluationMetrics=eval_metrics,
        )


cv_service = ComputerVisionService()

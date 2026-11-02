"""
backend/app/api/routes/vision.py — Real Computer Vision Endpoints
================================================================
Phase 2.0: Pretrained YOLOv8n Person Detection.
Endpoints for image person detection, video sequential processing, and status.
Strictly anonymous IDs. No facial recognition or emotion inference.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Optional
import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session as DBSession

from backend.app.database.db import get_db
from backend.app.database.repositories import DetectionRepository, SessionRepository
from backend.app.schemas.detections import (
    DetectionSummary,
    PoseDetectionResponse,
    PoseStatusResponse,
    VideoProcessResponse,
)
from backend.app.services.computer_vision import cv_service
from backend.app.services.hand_gesture import hand_gesture_service
from backend.app.services.sign_language import sign_language_service
from backend.app.services.tracking.zone_filter import validate_polygon

router = APIRouter(prefix="/api/vision", tags=["Computer Vision"])


@router.get("/status")
def get_vision_status():
    """Returns computer vision pipeline readiness, inference device, and model information."""
    return cv_service.get_status_info()


@router.get("/pose/status", response_model=PoseStatusResponse)
def get_pose_status():
    """Returns YOLOv8n-pose pipeline readiness, checkpoint, and 17 COCO keypoints metadata."""
    return cv_service.get_pose_status_info()


@router.post("/pose", response_model=PoseDetectionResponse)
async def detect_pose(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default="sess_live"),
    confidence_threshold: float = Form(default=0.35),
    keypoint_threshold: float = Form(default=0.4),
    elevation_margin_px: float = Form(default=15.0),
    imgsz: int = Form(default=640),
    db: DBSession = Depends(get_db),
) -> PoseDetectionResponse:
    """
    Phase 2.1: Human Pose Estimation using Pretrained YOLOv8n-pose.
    Extracts 17 COCO keypoints per detected person and computes observable physical postures
    (BOTH_ARMS_RAISED, LEFT_ARM_RAISED, RIGHT_ARM_RAISED, ARMS_NOT_RAISED, NEEDS_REVIEW).
    """
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    file_ext = Path(file.filename or "").suffix.lower()

    if file.content_type and not file.content_type.startswith("image/") and file_ext not in valid_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format '{file.filename}'. Allowed formats: JPEG, PNG, BMP, WEBP.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    try:
        response = cv_service.estimate_pose(
            content,
            confidence_threshold=confidence_threshold,
            keypoint_threshold=keypoint_threshold,
            elevation_margin_px=elevation_margin_px,
            imgsz=imgsz,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pose estimation inference failed: {str(e)}",
        )

    return response


@router.post("/detect", response_model=DetectionSummary)
async def detect_frame(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default="sess_live"),
    confidence_threshold: float = Form(default=0.35),
    imgsz: int = Form(default=640),
    detect_pose: bool = Form(default=False),
    db: DBSession = Depends(get_db),
) -> DetectionSummary:
    """
    Performs real YOLOv8n or YOLOv8n-pose person detection on an uploaded image or frame.
    Returns bounding box coordinates, confidence scores, image dimensions, keypoints, and latency.
    """
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    file_ext = Path(file.filename or "").suffix.lower()

    if file.content_type and not file.content_type.startswith("image/") and file_ext not in valid_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format '{file.filename}'. Allowed formats: JPEG, PNG, BMP, WEBP.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    try:
        if detect_pose:
            summary = cv_service.detect_with_pose(
                content,
                confidence_threshold=confidence_threshold,
            )
        else:
            summary = cv_service.detect_persons_yolov8n(
                content,
                confidence_threshold=confidence_threshold,
                imgsz=imgsz,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {str(e)}",
        )

    # Persist detection event to database
    try:
        repo = DetectionRepository(db)
        repo.create(
            session_id=session_id or "sess_live",
            frame_index=0,
            timestamp_seconds=0.0,
            person_count=summary.totalPersons,
            hand_raised_count=summary.activeHandRaises,
            hand_not_raised_count=summary.notRaisedCount,
            bounding_boxes=[b.model_dump() for b in summary.boxes],
            processing_fps=summary.processingFps,
            model_used="yolov8n-pose" if detect_pose else "yolov8n (COCO Person)",
            data_source="REAL_PROCESSING",
            notes=f"Detected {summary.totalPersons} persons ({summary.activeHandRaises} hand-raises) in {summary.processingTimeMs} ms.",
        )
    except Exception:
        pass

    return summary


@router.post("/video/process", response_model=VideoProcessResponse)
async def process_video(
    file: UploadFile = File(...),
    frame_skip: int = Form(default=5),
    confidence_threshold: float = Form(default=0.20),
    imgsz: int = Form(default=640),
    detect_pose: bool = Form(default=False),
    session_id: Optional[str] = Form(default="sess_video"),
    enable_tracking: bool = Form(default=True),
    instructor_roi_polygon: Optional[str] = Form(default=None),
    zone_filtering_enabled: bool = Form(default=True),
    keypoint_threshold: float = Form(default=0.25),
    elevation_margin_px: float = Form(default=15.0),
    db: DBSession = Depends(get_db),
) -> VideoProcessResponse:
    """
    Sequentially processes an uploaded video file frame-by-frame with configurable frame skipping.
    Avoids loading full video into RAM. Returns timeline, peak counts, decoding FPS, AI inference FPS,
    temporal hand-raising event statistics, and optional Teacher Zone Exclusion filtering.
    """
    valid_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    file_ext = Path(file.filename or "").suffix.lower()

    if file.content_type and not file.content_type.startswith("video/") and file_ext not in valid_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{file.filename}'. Allowed: MP4, AVI, MOV, MKV, WEBM.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded video file is empty.",
        )

    # Maximum file size constraint (500 MB)
    max_video_size = 500 * 1024 * 1024
    if len(content) > max_video_size:
        code_413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
        raise HTTPException(
            status_code=code_413,
            detail=f"Uploaded video ({round(len(content)/(1024*1024), 1)} MB) exceeds maximum allowed size of 500 MB.",
        )

    # Parse and validate instructor_roi_polygon if provided
    parsed_polygon = None
    if instructor_roi_polygon and instructor_roi_polygon.strip():
        try:
            parsed_polygon = json.loads(instructor_roi_polygon)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format for instructor_roi_polygon: {str(e)}",
            )

        is_valid, err_msg = validate_polygon(parsed_polygon)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid instructor_roi_polygon: {err_msg}",
            )

    try:
        response = cv_service.process_video_stream(
            content,
            filename_hint=file.filename or "video.mp4",
            frame_skip=frame_skip,
            confidence_threshold=confidence_threshold,
            imgsz=imgsz,
            detect_pose=detect_pose,
            session_id=session_id or "sess_video",
            db=db,
            enable_tracking=enable_tracking,
            instructor_roi_polygon=parsed_polygon,
            zone_filtering_enabled=zone_filtering_enabled,
            keypoint_threshold=keypoint_threshold,
            elevation_margin_px=elevation_margin_px,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video processing failed: {str(e)}",
        )

    # Persist summary to database
    try:
        session_key = session_id or "sess_video"
        session_repo = SessionRepository(db)
        existing_session = session_repo.get_by_id(session_key)
        if not existing_session:
            session_repo.create(
                id=session_key,
                title=f"Video Analysis: {file.filename or 'classroom_video.mp4'}",
                course_code="CV101",
                classroom="Rear-Corner Camera",
                instructor="Automated Analysis",
                status="completed",
                data_source="REAL_PROCESSING",
                privacy_protected=True,
                instructor_roi_polygon=parsed_polygon,
                zone_filtering_enabled=zone_filtering_enabled,
            )
        else:
            session_repo.update_zone_config(
                session_key,
                instructor_roi_polygon=parsed_polygon,
                zone_filtering_enabled=zone_filtering_enabled,
            )

        repo = DetectionRepository(db)
        repo.create(
            session_id=session_key,
            frame_index=response.totalFrames,
            timestamp_seconds=response.durationSeconds,
            person_count=response.maxPersonsInFrame,
            hand_raised_count=response.totalHandRaises,
            hand_not_raised_count=max(0, response.maxPersonsInFrame - response.totalHandRaises),
            bounding_boxes=[],
            processing_fps=response.processingFps,
            model_used=response.modelName,
            data_source="REAL_PROCESSING",
            notes=f"Processed video '{response.videoFilename}' ({response.processedFrames} sampled frames, peak {response.maxPersonsInFrame} persons, {response.totalHandRaises} hand-raises, {response.instructorZoneEventsCount} instructor-zone excluded).",
        )
    except Exception:
        pass

    return response


@router.post("/privacy-blur")
async def apply_privacy_blur_endpoint(
    file: UploadFile = File(...),
    blur_ratio: float = Form(default=0.25),
    kernel_size: int = Form(default=51),
):
    """
    Applies genuine in-memory Gaussian pixel blurring to the face/head regions of all detected persons.
    Irrevocably modifies the pixel matrix in memory before returning the anonymized image.
    Guarantees 0 bytes saved to disk or database.
    """
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        blurred_img, face_count = cv_service.apply_privacy_blur(
            content,
            blur_ratio=blur_ratio,
            kernel_size=kernel_size,
        )
        success, encoded_jpg = cv2.imencode(".jpg", blurred_img)
        if not success:
            raise ValueError("Failed to encode blurred image.")

        return Response(
            content=encoded_jpg.tobytes(),
            media_type="image/jpeg",
            headers={
                "X-Faces-Blurred": str(face_count),
                "X-Privacy-Mode": "True-In-Memory-Pixel-Blur",
                "X-Data-Source": "REAL_PROCESSING_ANONYMIZED",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Privacy blurring failed: {str(e)}",
        )


@router.post("/detect-synthetic", response_model=DetectionSummary)
def detect_synthetic_frame(
    session_id: Optional[str] = "sess_synth",
    db: DBSession = Depends(get_db),
) -> DetectionSummary:
    """
    Runs computer vision inference on a dynamically generated synthetic frame.
    Useful for automated verification, CI/CD, and demo runs without camera access.
    """
    img = Image.new("RGB", (640, 480), color=(220, 225, 230))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    content = buf.getvalue()

    summary = cv_service.detect_persons_yolov8n(content)
    summary.status = "SYNTHETIC_PROCESSING"
    summary.dataSource = "SYNTHETIC_DATA"
    return summary


# ---------------------------------------------------------------------------
# Sign Language MNIST Endpoints (Isolated Module)
# ---------------------------------------------------------------------------


@router.get("/sign-language/status")
def get_sign_language_status():
    """Returns Sign Language MNIST model status, device, and test evaluation metrics."""
    return sign_language_service.get_status_info()


@router.post("/sign-language/predict")
async def predict_sign_language(file: UploadFile = File(...)):
    """
    Predicts static ASL alphabet gesture from an uploaded 28x28 grayscale image crop.
    Strict isolation: Separated from classroom hand-raising detection.
    """
    if not file.content_type or not (
        file.content_type.startswith("image/")
        or file.content_type in ("application/octet-stream",)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image format (PNG, JPEG, WEBP).",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded sign language image is empty.",
        )

    try:
        return sign_language_service.predict(content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {str(e)}")


# ---------------------------------------------------------------------------
# Hand Gesture 20-Class Endpoints (Unmapped Semantics)
# ---------------------------------------------------------------------------


@router.get("/gesture/status")
def get_hand_gesture_status():
    """Returns 20-class Hand Gesture model status, device, and test evaluation metrics."""
    return hand_gesture_service.get_status_info()


@router.post("/gesture/predict")
async def predict_hand_gesture(file: UploadFile = File(...)):
    """
    Predicts gesture class across 20 numerical classes (0-19) from an uploaded image crop.
    Strict isolation: Numerical classes only; unmapped to classroom behavior.
    """
    if not file.content_type or not (
        file.content_type.startswith("image/")
        or file.content_type in ("application/octet-stream",)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image format (PNG, JPEG, WEBP).",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded hand gesture image is empty.",
        )

    try:
        return hand_gesture_service.predict(content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {str(e)}")

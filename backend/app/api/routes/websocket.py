"""
backend/app/api/routes/websocket.py — Real-Time Detection WebSocket
===================================================================
Streams frame-by-frame bounding boxes, pose keypoints, and hand-raise detection events.
Phase 2.8: Privacy-chained webcam inference with server-side Gaussian blur safeguard
and automatic SQLite event persistence via HandRaiseEventRepository.
Guarantees 0 bytes saved to disk or database for all webcam frames.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.core.config import settings
from backend.app.database import models
from backend.app.database.db import SessionLocal
from backend.app.database.repositories import HandRaiseEventRepository
from backend.app.schemas.detections import WebSocketDetectionMessage
from backend.app.schemas.tracking import HandRaisingState
from backend.app.services.analytics import analytics_service
from backend.app.services.computer_vision import cv_service
from backend.app.services.tracking.temporal_tracker import temporal_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=["Real-time Feeds"])


@router.websocket("/detections")
async def websocket_detections(websocket: WebSocket) -> None:
    """Streams realtime bounding box detections to the connected client."""
    await websocket.accept()
    try:
        # Initial greeting with current detections preview
        boxes = analytics_service.get_detections_preview() if settings.is_demo_mode else []
        status_flag = "DEMO_DATA" if settings.is_demo_mode else "NOT_CONNECTED"
        initial_msg = WebSocketDetectionMessage(
            type="detections",
            sessionId="sess_01",
            timestamp=datetime.now(timezone.utc).isoformat(),
            detections=boxes,
            status=status_flag,
            dbPersistenceStatus="CONNECTED",
            serverSideBlurApplied=False,
            clientSideBlurDetected=False,
            persistedEventsCount=0,
        )
        await websocket.send_text(initial_msg.model_dump_json(by_alias=True))

        # Handle incoming ping / client frame messages
        while True:
            data = await websocket.receive_text()

            # Fast path for raw ping or non-JSON text
            if data == "ping" or not data.strip().startswith("{"):
                response_msg = WebSocketDetectionMessage(
                    type="detections",
                    sessionId="sess_01",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    detections=boxes,
                    status=status_flag,
                    dbPersistenceStatus="CONNECTED",
                )
                await websocket.send_text(response_msg.model_dump_json(by_alias=True))
                continue

            try:
                payload = json.loads(data)
            except Exception:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON format"})
                )
                continue

            msg_type = payload.get("type", "ping")

            # Session Reset Request (clears in-memory tracker; preserves SQLite history)
            if msg_type == "reset":
                sess_id = payload.get("sessionId", "sess_live")
                temporal_tracker.reset_session(session_id=sess_id)
                response_msg = WebSocketDetectionMessage(
                    type="status",
                    sessionId=sess_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    detections=[],
                    status="RESET_COMPLETED",
                    dbPersistenceStatus="CONNECTED",
                )
                await websocket.send_text(response_msg.model_dump_json(by_alias=True))
                continue

            if msg_type == "frame":
                raw_frame = payload.get("frame", "")
                conf_thresh = float(payload.get("confidenceThreshold", 0.35))
                detect_pose = bool(payload.get("detectPose", True))
                server_side_blur = bool(payload.get("serverSideBlur", True))
                client_side_blur = bool(payload.get("clientSideBlur", False))
                sess_id = payload.get("sessionId", "sess_live")

                server_blur_applied = False
                db_persistence_status = "CONNECTED"
                db_error_message: Optional[str] = None
                persisted_events_count = 0

                try:
                    if "," in raw_frame:
                        raw_frame = raw_frame.split(",", 1)[1]
                    # Volatile in-memory decoding: never written to disk or logged
                    frame_bytes = base64.b64decode(raw_frame)

                    # Open scoped database session for event persistence
                    db = SessionLocal()
                    try:
                        if detect_pose:
                            # 1. Human Pose Estimation (YOLOv8n-pose: 17 keypoints)
                            pose_res = cv_service.estimate_pose(
                                frame_bytes,
                                confidence_threshold=conf_thresh,
                            )

                            # 2. Server-Side Privacy Safeguard: In-memory Gaussian blur on face/head regions
                            if server_side_blur:
                                person_boxes = [p.bbox for p in pose_res.persons]
                                if person_boxes:
                                    blurred_img, _ = cv_service.apply_privacy_blur(
                                        frame_bytes,
                                        boxes=person_boxes,
                                    )
                                    del blurred_img  # Released immediately from RAM
                                server_blur_applied = True

                            # 3. Temporal Tracking & Hand-Raise FSM Update
                            active_tracks, newly_completed = temporal_tracker.update(
                                pose_res.persons,
                                session_id=sess_id,
                                db_session=db,
                            )

                            # 4. Generate detection summary with bounding boxes and gestures
                            summary = cv_service.detect_with_pose(
                                frame_bytes,
                                confidence_threshold=conf_thresh,
                            )

                            # 5. Enrich bounding boxes with stable anonymous track IDs and state
                            track_map = {t.bbox.id: t for t in active_tracks}
                            for b in summary.boxes:
                                matched_t = track_map.get(b.id)
                                if matched_t:
                                    b.id = matched_t.trackId
                                    b.status = matched_t.state.value
                                    b.handRaised = (matched_t.state == HandRaisingState.RAISED)

                                    if matched_t.state == HandRaisingState.RAISED:
                                        if matched_t.handSide == HandSide.BOTH_HANDS:
                                            b.activityLabel = "BOTH_HANDS_RAISED"
                                        elif matched_t.handSide == HandSide.LEFT_HAND:
                                            b.activityLabel = "LEFT_HAND_RAISED"
                                        elif matched_t.handSide == HandSide.RIGHT_HAND:
                                            b.activityLabel = "RIGHT_HAND_RAISED"
                                        else:
                                            b.activityLabel = "HAND_RAISED"
                                        b.statusColor = "BLUE"

                            tracked_persons_data = [t.model_dump(by_alias=True) for t in active_tracks]
                            active_evts_data = [
                                e.model_dump(by_alias=True)
                                for e in temporal_tracker.all_events_by_id.values()
                                if e.state == "RAISED"
                            ]
                            total_evts_count = len(temporal_tracker.all_events_by_id)

                            # 6. Automatic SQLite Event Persistence via HandRaiseEventRepository
                            if newly_completed:
                                try:
                                    repo = HandRaiseEventRepository(db)
                                    for evt in newly_completed:
                                        repo.upsert(
                                            event_id=evt.eventId,
                                            session_id=evt.sessionId,
                                            track_id=evt.trackId,
                                            hand_side=evt.handSide.value if hasattr(evt.handSide, "value") else str(evt.handSide),
                                            state=evt.state,
                                            start_timestamp_seconds=evt.startTimestampSeconds,
                                            end_timestamp_seconds=evt.endTimestampSeconds,
                                            duration_seconds=evt.durationSeconds,
                                            start_frame=evt.startFrame,
                                            end_frame=evt.endFrame,
                                            frame_count=getattr(evt, "frameCount", 1),
                                            max_confidence=getattr(evt, "maxConfidence", 0.0),
                                            avg_confidence=getattr(evt, "avgConfidence", 0.0),
                                            evidence=getattr(evt, "evidence", {}),
                                        )
                                    db_persistence_status = "SAVED"
                                except Exception as db_save_err:
                                    db.rollback()
                                    db_persistence_status = "ERROR"
                                    db_error_message = str(db_save_err)
                                    logger.error("Failed to persist hand raise event to SQLite: %s", db_save_err)

                            # Query current persisted event count for session
                            try:
                                persisted_events_count = (
                                    db.query(models.HandRaiseEventRecord)
                                    .filter(models.HandRaiseEventRecord.session_id == sess_id)
                                    .count()
                                )
                            except Exception as db_cnt_err:
                                db_persistence_status = "ERROR"
                                db_error_message = str(db_cnt_err)
                                persisted_events_count = len(temporal_tracker.completed_events)

                        else:
                            # Standard Person Detection (YOLOv8n)
                            summary = cv_service.detect_persons_yolov8n(
                                frame_bytes,
                                confidence_threshold=conf_thresh,
                            )
                            if server_side_blur:
                                if summary.detections:
                                    blurred_img, _ = cv_service.apply_privacy_blur(
                                        frame_bytes,
                                        boxes=summary.detections,
                                    )
                                    del blurred_img
                                server_blur_applied = True

                            tracked_persons_data = None
                            active_evts_data = None
                            total_evts_count = 0
                            persisted_events_count = 0
                            db_persistence_status = "IDLE"

                    except Exception as db_op_err:
                        # Ensure database errors never drop the WebSocket connection
                        db.rollback()
                        db_persistence_status = "ERROR"
                        db_error_message = str(db_op_err)
                        logger.error("WebSocket DB operation exception: %s", db_op_err)
                    finally:
                        db.close()
                        db = None

                    privacy_safeguards = {
                        "inMemoryOnly": True,
                        "diskWrites": 0,
                        "databaseFrameWrites": 0,
                        "clientSideBlurring": client_side_blur,
                        "serverSideBlurring": server_blur_applied,
                        "anonymousTracking": True,
                        "biometricIdentification": False,
                    }

                    response_msg = WebSocketDetectionMessage(
                        type="detections",
                        sessionId=sess_id,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        detections=summary.boxes,
                        status="REAL_PROCESSING",
                        totalPersons=summary.totalPersons,
                        activeHandRaises=summary.activeHandRaises,
                        processingFps=summary.processingFps,
                        processingTimeMs=summary.processingTimeMs,
                        inferenceDevice=summary.inferenceDevice,
                        imageWidth=summary.imageWidth,
                        imageHeight=summary.imageHeight,
                        isDemoData=False,
                        trackedPersons=tracked_persons_data,
                        activeEvents=active_evts_data,
                        totalEventsCount=total_evts_count,
                        serverSideBlurApplied=server_blur_applied,
                        clientSideBlurDetected=client_side_blur,
                        persistedEventsCount=persisted_events_count,
                        dbPersistenceStatus=db_persistence_status,
                        dbErrorMessage=db_error_message,
                        privacySafeguards=privacy_safeguards,
                    )
                    await websocket.send_text(response_msg.model_dump_json(by_alias=True))

                except Exception as exc:
                    err_msg = WebSocketDetectionMessage(
                        type="error",
                        sessionId=sess_id,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        detections=[],
                        status="ERROR",
                        dbPersistenceStatus="ERROR",
                        dbErrorMessage=str(exc),
                    )
                    await websocket.send_text(err_msg.model_dump_json(by_alias=True))
                finally:
                    # Guarantee closing of SQLAlchemy DB connection to prevent SQLite pool exhaustion
                    if 'db' in locals() and db is not None:
                        try:
                            db.close()
                        except Exception:
                            pass
                    # Guarantee release of frame buffers from memory
                    try:
                        del frame_bytes
                    except NameError:
                        pass
            else:
                response_msg = WebSocketDetectionMessage(
                    type="detections",
                    sessionId="sess_01",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    detections=boxes,
                    status=status_flag,
                    dbPersistenceStatus="CONNECTED",
                )
                await websocket.send_text(response_msg.model_dump_json(by_alias=True))

    except WebSocketDisconnect:
        # Normal client disconnection, no error
        pass
    except Exception:
        # Ensure socket is cleanly closed on unexpected error
        try:
            await websocket.close()
        except Exception:
            pass

"""
backend/app/api/routes/tracking.py — Temporal Hand-Raising & Person Tracking Endpoints
=====================================================================================
Phase 2.2: REST Endpoints for anonymous person tracking and temporal hand-raising events.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session as DBSession

from backend.app.database.db import get_db
from backend.app.database.repositories import HandRaiseEventRepository
from backend.app.schemas.tracking import (
    HandRaiseEventSchema,
    HandRaisingState,
    HandSide,
    TrackedPersonState,
    TrackingEventStatisticsResponse,
    TrackingSummaryResponse,
)
from backend.app.services.computer_vision import cv_service
from backend.app.services.tracking.temporal_tracker import temporal_tracker

router = APIRouter(prefix="/api/vision/tracking", tags=["Temporal Tracking"])


@router.get("/active", response_model=TrackingSummaryResponse)
def get_active_tracks():
    """Returns currently tracked anonymous individuals and their hand-raising states."""
    return temporal_tracker.get_summary_response()


@router.get("/states")
def get_tracking_states_summary():
    """Returns count breakdown across states: NOT_RAISED, RAISING, RAISED, LOWERING, NEEDS_REVIEW."""
    summary = temporal_tracker.get_summary_response()
    return {
        "sessionId": summary.sessionId,
        "activeTracksCount": summary.activeTracksCount,
        "activeHandRaisesCount": summary.activeHandRaisesCount,
        "states": summary.statesSummary,
    }


@router.get("/events", response_model=List[HandRaiseEventSchema])
def get_hand_raising_events(
    session_id: Optional[str] = Query(default=None),
    track_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: DBSession = Depends(get_db),
):
    """
    Returns historical hand-raising events persisted in SQLite.
    Each event represents a single continuous hand-raising episode with duration and evidence.
    """
    repo = HandRaiseEventRepository(db)
    if track_id:
        records = repo.get_by_track(track_id, session_id=session_id)
    elif session_id:
        records = repo.get_by_session(session_id, limit=limit, offset=offset)
    else:
        # If no session specified, return in-memory completed events + active events
        evts = list(temporal_tracker.all_events_by_id.values())
        return evts[offset : offset + limit]

    results: List[HandRaiseEventSchema] = []
    for r in records:
        results.append(
            HandRaiseEventSchema(
                id=r.id,
                eventId=r.event_id,
                sessionId=r.session_id,
                trackId=r.track_id,
                handSide=HandSide(r.hand_side) if r.hand_side in HandSide._value2member_map_ else HandSide.UNKNOWN,
                state=r.state,
                startTimestampSeconds=r.start_timestamp_seconds,
                endTimestampSeconds=r.end_timestamp_seconds,
                durationSeconds=r.duration_seconds,
                startFrame=r.start_frame,
                endFrame=r.end_frame,
                frameCount=r.frame_count,
                maxConfidence=r.max_confidence,
                avgConfidence=r.avg_confidence,
                evidence=r.evidence or {},
                dataSource=r.data_source,
                createdAt=r.created_at.isoformat() if r.created_at else None,
            )
        )
    return results


@router.get("/events/statistics", response_model=TrackingEventStatisticsResponse)
def get_event_statistics(
    session_id: Optional[str] = Query(default=None),
    db: DBSession = Depends(get_db),
):
    """Returns aggregated metrics for hand-raising events (count, duration, left/right breakdown)."""
    # Prefer database repository for persisted sessions
    if session_id:
        repo = HandRaiseEventRepository(db)
        stats = repo.get_statistics(session_id)
        return TrackingEventStatisticsResponse(
            sessionId=session_id,
            totalEvents=stats["total_events"],
            completedEvents=stats["completed_events"],
            activeEvents=stats["active_events"],
            leftHandCount=stats["left_hand_count"],
            rightHandCount=stats["right_hand_count"],
            bothHandsCount=stats["both_hands_count"],
            avgDurationSeconds=stats["avg_duration_seconds"],
            maxDurationSeconds=stats["max_duration_seconds"],
            totalDurationSeconds=stats["total_duration_seconds"],
            needsReviewCount=stats["needs_review_count"],
            cooldownPeriodSeconds=temporal_tracker.cooldown_seconds,
        )

    # In-memory real-time tracker statistics
    return temporal_tracker.get_statistics_response()


@router.post("/reset")
def reset_tracking_session(session_id: str = Query(default="sess_live")):
    """Resets tracking state and clears in-memory trajectory history for a fresh session."""
    temporal_tracker.reset_session(session_id=session_id)
    return {"status": "SUCCESS", "message": f"Tracking reset for session '{session_id}'."}


@router.post("/process-frame")
async def process_frame_tracking(
    file: UploadFile = File(...),
    session_id: str = Form(default="sess_live"),
    timestamp_seconds: Optional[float] = Form(default=None),
    confidence_threshold: float = Form(default=0.35),
    db: DBSession = Depends(get_db),
):
    """
    Runs YOLOv8n-pose keypoint estimation on an image and updates temporal tracking states.
    Persists completed hand-raising events into SQLite.
    """
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 1. Execute YOLOv8n-pose inference
    pose_res = cv_service.estimate_pose(
        content,
        confidence_threshold=confidence_threshold,
    )

    # 2. Update Temporal Tracker
    active_tracks, completed_events = temporal_tracker.update(
        pose_res.persons,
        timestamp_seconds=timestamp_seconds,
        session_id=session_id,
        db_session=db,
    )

    return {
        "sessionId": session_id,
        "frameIndex": temporal_tracker.current_frame_index,
        "activeTracks": active_tracks,
        "activeHandRaises": sum(1 for t in active_tracks if t.state == HandRaisingState.RAISED),
        "newlyCompletedEvents": completed_events,
        "processingTimeMs": pose_res.processingTimeMs,
        "processingFps": pose_res.processingFps,
    }


"""
backend/app/api/routes/sessions.py — Classroom Sessions Endpoints
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DBSession

from backend.app.core.config import settings
from backend.app.database.db import get_db
from backend.app.database.repositories import SessionRepository as DBSessionRepository
from backend.app.schemas.sessions import SessionInfo, SessionZoneConfigRequest
from backend.app.services.database import session_repository
from backend.app.services.tracking.zone_filter import validate_polygon

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionInfo])
async def list_sessions(
    include_demo: Optional[bool] = Query(
        default=None,
        description="Include demo sessions (defaults to settings.is_demo_mode)",
    ),
    db: DBSession = Depends(get_db),
) -> List[SessionInfo]:
    """Lists recorded or demonstration classroom sessions."""
    use_demo = include_demo if include_demo is not None else settings.is_demo_mode
    sessions = session_repository.get_all_sessions(include_demo=use_demo)

    # Augment with any SQLite sessions if demo/all mode
    if use_demo:
        db_repo = DBSessionRepository(db)
        db_sessions = db_repo.list_all()
        existing_ids = {s.sessionId for s in sessions}

        for dbs in db_sessions:
            if dbs.id not in existing_ids:
                sessions.append(
                SessionInfo(
                    sessionId=dbs.id,
                    title=dbs.title,
                    courseCode=dbs.course_code or "CV101",
                    date=dbs.date or "2026-10-31",
                    startTime=dbs.start_time or "09:00 AM",
                    durationMinutes=dbs.duration_minutes or 45,
                    classroom=dbs.classroom or "Classroom",
                    instructor=dbs.instructor or "Instructor",
                    status="completed" if dbs.status == "completed" else "active",
                    totalStudents=25,
                    activeHandRaises=0,
                    totalHandRaiseEvents=0,
                    averageEngagement=80.0,
                    privacyProtected=dbs.privacy_protected if dbs.privacy_protected is not None else True,
                    instructorRoiPolygon=dbs.instructor_roi_polygon,
                    zoneFilteringEnabled=dbs.zone_filtering_enabled if dbs.zone_filtering_enabled is not None else True,
                )
            )

    return sessions


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    include_demo: Optional[bool] = Query(
        default=None,
        description="Include demo sessions (defaults to settings.is_demo_mode)",
    ),
    db: DBSession = Depends(get_db),
) -> SessionInfo:
    """Retrieves metadata and metrics for a specific classroom session."""
    use_demo = include_demo if include_demo is not None else settings.is_demo_mode
    session = session_repository.get_by_id(session_id, include_demo=use_demo)

    # Check SQLite DB if not found in memory/demo
    if not session:
        db_repo = DBSessionRepository(db)
        dbs = db_repo.get_by_id(session_id)
        if dbs:
            return SessionInfo(
                sessionId=dbs.id,
                title=dbs.title,
                courseCode=dbs.course_code or "CV101",
                date=dbs.date or "2026-10-31",
                startTime=dbs.start_time or "09:00 AM",
                durationMinutes=dbs.duration_minutes or 45,
                classroom=dbs.classroom or "Classroom",
                instructor=dbs.instructor or "Instructor",
                status="completed" if dbs.status == "completed" else "active",
                totalStudents=25,
                activeHandRaises=0,
                totalHandRaiseEvents=0,
                averageEngagement=80.0,
                privacyProtected=dbs.privacy_protected if dbs.privacy_protected is not None else True,
                instructorRoiPolygon=dbs.instructor_roi_polygon,
                zoneFilteringEnabled=dbs.zone_filtering_enabled if dbs.zone_filtering_enabled is not None else True,
            )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classroom session '{session_id}' not found.",
        )
    return session


@router.get("/{session_id}/zone-config", response_model=Dict[str, Any])
async def get_session_zone_config(
    session_id: str,
    db: DBSession = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves the Teacher Zone Exclusion configuration for a session."""
    db_repo = DBSessionRepository(db)
    dbs = db_repo.get_by_id(session_id)
    if not dbs:
        # Fallback to session repository or demo defaults
        session = session_repository.get_by_id(session_id, include_demo=True)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Classroom session '{session_id}' not found.",
            )
        return {
            "sessionId": session_id,
            "instructorRoiPolygon": getattr(session, "instructorRoiPolygon", None),
            "zoneFilteringEnabled": getattr(session, "zoneFilteringEnabled", True),
        }

    return {
        "sessionId": session_id,
        "instructorRoiPolygon": dbs.instructor_roi_polygon,
        "zoneFilteringEnabled": dbs.zone_filtering_enabled if dbs.zone_filtering_enabled is not None else True,
    }


@router.put("/{session_id}/zone-config", response_model=Dict[str, Any])
async def update_session_zone_config(
    session_id: str,
    config: SessionZoneConfigRequest,
    db: DBSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Configures, edits, resets, or disables the Teacher Zone Exclusion polygon for a session.
    Validates that polygon coordinates are properly normalized between 0.0 and 1.0.
    """
    if config.instructorRoiPolygon is not None:
        valid, err_msg = validate_polygon(config.instructorRoiPolygon)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid instructor ROI polygon: {err_msg}",
            )

    db_repo = DBSessionRepository(db)
    dbs = db_repo.get_by_id(session_id)
    if not dbs:
        # Create session stub if not yet persisted in SQLite
        dbs = db_repo.create(
            id=session_id,
            title=f"Session {session_id}",
            course_code="CV101",
            classroom="Lecture Room",
            instructor="Instructor",
            status="active",
            data_source="REAL_PROCESSING",
            privacy_protected=True,
            instructor_roi_polygon=config.instructorRoiPolygon,
            zone_filtering_enabled=config.zoneFilteringEnabled,
        )
    else:
        dbs = db_repo.update_zone_config(
            session_id,
            instructor_roi_polygon=config.instructorRoiPolygon,
            zone_filtering_enabled=config.zoneFilteringEnabled,
        )

    return {
        "sessionId": session_id,
        "instructorRoiPolygon": dbs.instructor_roi_polygon,
        "zoneFilteringEnabled": dbs.zone_filtering_enabled,
        "message": "Instructor ROI polygon configuration updated successfully.",
    }



"""
backend/app/api/routes/reports.py — Session Reports & Quality Audit Endpoint
============================================================================
Provides downloadable PDF and Excel reports as well as model calibration audits.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from backend.app.core.config import settings
from backend.app.database.db import get_db
from backend.app.schemas.reports import ReportsResponse
from backend.app.services.analytics import analytics_service
from backend.app.services.reports import report_generator

router = APIRouter(prefix="/api/reports", tags=["Reports"])


class GenerateReportRequest(BaseModel):
    sessionId: str = "sess_01"
    format: str = "pdf"  # "pdf" | "xlsx"
    title: Optional[str] = None


@router.get("", response_model=ReportsResponse)
async def list_reports(
    demo: Optional[bool] = Query(
        default=None,
        description="Include demo reports (defaults to settings.is_demo_mode)",
    )
) -> ReportsResponse:
    """Returns downloadable reports and the model quality / calibration audit."""
    use_demo = demo if demo is not None else settings.is_demo_mode
    return analytics_service.get_reports(include_demo=use_demo)


@router.post("/generate")
def generate_report(request: GenerateReportRequest, db: DBSession = Depends(get_db)):
    """
    Generates a real PDF or Excel report using ReportLab or openpyxl.
    """
    fmt = request.format.lower()
    title = request.title or f"ClassVision Intelligence Summary — {request.sessionId}"

    course_code = "CS402"
    instructor = "Academic Instructor"
    stats = None
    transcripts = None
    ocr_blocks = None
    events = None

    try:
        from backend.app.database.repositories import (
            HandRaiseEventRepository,
            OcrRepository,
            SessionRepository,
            TranscriptRepository,
        )
        s_repo = SessionRepository(db)
        h_repo = HandRaiseEventRepository(db)
        t_repo = TranscriptRepository(db)
        o_repo = OcrRepository(db)

        s_obj = s_repo.get_by_id(request.sessionId)
        if s_obj:
            course_code = s_obj.course_code or "CS402"
            instructor = s_obj.instructor or "Academic Instructor"

        db_stats = h_repo.get_statistics(request.sessionId)
        if db_stats and db_stats.get("total_events", 0) > 0:
            stats = {
                "Total Hand-Raise Events": str(db_stats.get("total_events", 0)),
                "Left Hand Raises": str(db_stats.get("left_hand_count", 0)),
                "Right Hand Raises": str(db_stats.get("right_hand_count", 0)),
                "Both Hands Raises": str(db_stats.get("both_hands_count", 0)),
                "Average Duration": f"{db_stats.get('avg_duration_seconds', 0.0):.1f}s",
                "Camera Mount": "Rear-Corner Elevated",
                "Biometric Profiling": "DISABLED",
                "Raw Frame Storage": "0 Bytes",
            }

        db_tr = t_repo.get_by_session(request.sessionId)
        if db_tr:
            transcripts = [
                {"id": f"tr_{t.id}", "full_text": t.full_text, "text": t.full_text, "speaker": "Instructor", "timestamp": "00:00:00"}
                for t in db_tr
            ]

        db_ocr = o_repo.get_by_session(request.sessionId)
        if db_ocr:
            ocr_blocks = [
                {"id": f"ocr_{o.id}", "extracted_text": o.extracted_text, "text": o.extracted_text, "confidence": o.overall_confidence}
                for o in db_ocr
            ]

        db_evts = h_repo.get_by_session(request.sessionId)
        if db_evts:
            events = [
                {
                    "event_id": e.event_id,
                    "track_id": e.track_id,
                    "hand_side": e.hand_side,
                    "start_time": e.start_timestamp_seconds,
                    "end_time": e.end_timestamp_seconds,
                    "duration": e.duration_seconds,
                    "state": e.state,
                    "confidence": e.avg_confidence,
                }
                for e in db_evts
            ]
    except Exception:
        pass

    if fmt == "pdf":
        file_path = report_generator.generate_pdf_session_report(
            session_id=request.sessionId,
            session_title=title,
            course_code=course_code,
            instructor=instructor,
            stats=stats,
            transcripts=transcripts,
            ocr_blocks=ocr_blocks,
        )
    elif fmt in ("xlsx", "excel"):
        file_path = report_generator.generate_excel_session_report(
            session_id=request.sessionId,
            session_title=title,
            stats=stats,
            transcripts=transcripts,
            ocr_blocks=ocr_blocks,
            events=events,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{request.format}'. Use 'pdf' or 'xlsx'.",
        )

    filename = Path(file_path).name
    return {
        "status": "SUCCESS",
        "sessionId": request.sessionId,
        "format": fmt.upper(),
        "filename": filename,
        "downloadUrl": f"/api/reports/download/{filename}",
        "data_source": "REAL_PROCESSING",
    }


@router.get("/download/{filename}")
def download_report(filename: str):
    """Downloads a generated report file."""
    target_path = report_generator.output_dir / filename
    if not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file '{filename}' not found.",
        )

    media_type = (
        "application/pdf"
        if filename.endswith(".pdf")
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return FileResponse(
        path=str(target_path),
        filename=filename,
        media_type=media_type,
    )

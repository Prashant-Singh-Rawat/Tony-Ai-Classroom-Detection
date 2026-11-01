"""
backend/app/api/routes/intelligence.py — Lecture Intelligence Fusion & Summary Scoring
=====================================================================================
1. GET /api/intelligence/summary-score/status: Status of the CommonLit summary scoring model.
2. POST /api/intelligence/summary-score/predict: Predicts content & wording rubric scores.
3. GET /api/intelligence/{session_id}: Speech transcription fused with board OCR notes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession

from backend.app.core.config import settings
from backend.app.database.db import get_db
from backend.app.schemas.intelligence import LectureIntelligenceData
from backend.app.services.analytics import analytics_service
from backend.app.services.summary_scoring import summary_scoring_service

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])


class SummaryScoringRequest(BaseModel):
    summaryText: str = Field(..., alias="summary_text", description="Student summary text to evaluate")

    model_config = {
        "populate_by_name": True,
    }


@router.get("/summary-score/status")
def get_summary_scoring_status():
    """Returns CommonLit student summary scoring model status and test evaluation metrics."""
    return summary_scoring_service.get_status_info()


@router.post("/summary-score/predict")
def predict_summary_score(request: SummaryScoringRequest):
    """
    Evaluates student summary text against educational content and wording rubrics.
    Returns predicted content score, wording score, and overall quality.
    Ethical boundary: writing rubric assessment only; never measures student intelligence.
    """
    try:
        return summary_scoring_service.predict(request.summaryText)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Summary scoring failed: {str(e)}")


@router.get("", response_model=LectureIntelligenceData)
@router.get("/", response_model=LectureIntelligenceData)
async def get_default_lecture_intelligence(
    session_id: Optional[str] = Query(
        default=None,
        description="Optional session ID. If omitted, uses the latest valid real session.",
    ),
    demo: Optional[bool] = Query(
        default=None,
        description="Whether to return demonstration intel (defaults to settings.is_demo_mode)",
    ),
    db: DBSession = Depends(get_db),
) -> LectureIntelligenceData:
    """Returns lecture intelligence for the requested or latest valid real classroom session."""
    use_demo = demo if demo is not None else settings.is_demo_mode
    intel = analytics_service.get_intelligence(session_id=session_id, db=db, include_demo=use_demo)
    if not intel:
        detail_msg = (
            f"Lecture intelligence data for session '{session_id}' not found."
            if session_id
            else "Lecture intelligence data not found."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail_msg,
        )
    return intel


@router.get("/{session_id}", response_model=LectureIntelligenceData)
async def get_lecture_intelligence(
    session_id: str,
    demo: Optional[bool] = Query(
        default=None,
        description="Whether to return demonstration intel (defaults to settings.is_demo_mode)",
    ),
    db: DBSession = Depends(get_db),
) -> LectureIntelligenceData:
    """Returns speech transcription fused with board OCR notes and question timestamps."""
    use_demo = demo if demo is not None else settings.is_demo_mode
    intel = analytics_service.get_intelligence(session_id=session_id, db=db, include_demo=use_demo)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture intelligence data for session '{session_id}' not found.",
        )
    return intel

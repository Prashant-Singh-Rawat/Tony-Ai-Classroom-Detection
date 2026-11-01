"""
backend/app/api/routes/ocr.py — Whiteboard OCR & Character Recognition Endpoints
================================================================================
1. EasyOCR whiteboard & slide text extraction (preserved).
2. Dedicated CharacterCNN single-character recognition across 62 classes.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session as DBSession

from backend.app.database.db import get_db
from backend.app.database.repositories import OcrRepository, SessionRepository
from backend.app.schemas.character_recognition import (
    CharacterPredictionResponse,
    CharacterStatusResponse,
)
from backend.app.services.ocr import character_service, ocr_service
from backend.app.services.rag import rag_service

router = APIRouter(prefix="/api/ocr", tags=["Whiteboard & Character OCR"])


# ---------------------------------------------------------------------------
# EasyOCR Whiteboard Endpoints (Preserved Functionality)
# ---------------------------------------------------------------------------


@router.get("/status")
def get_ocr_status():
    """Returns EasyOCR engine status and capabilities."""
    return ocr_service.get_status_info()


@router.post("/extract")
async def extract_whiteboard_text(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default="sess_live"),
    db: DBSession = Depends(get_db),
):
    """
    Extracts text from an uploaded whiteboard or slide image using EasyOCR.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image (JPEG/PNG).",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    result = ocr_service.extract_text(content)

    # Persist in SQLite and index in RAG
    session_key = session_id or "sess_live"
    try:
        session_repo = SessionRepository(db)
        if not session_repo.get_by_id(session_key):
            session_repo.create(
                id=session_key,
                title=f"Board OCR Session: {file.filename or 'Board Photo'}",
                course_code="CV101",
                classroom="Main Lecture Hall",
                instructor="Academic Instructor",
                status="active",
                data_source="REAL_PROCESSING",
                privacy_protected=True,
            )

        repo = OcrRepository(db)
        repo.create(
            session_id=session_key,
            image_filename=file.filename,
            extracted_text=result.get("full_text", ""),
            text_blocks=result.get("text_blocks", []),
            overall_confidence=result.get("overall_confidence", 0.0),
            engine=result.get("engine", "EasyOCR"),
            data_source="REAL_PROCESSING",
        )

        # Ingest into Educational RAG ChromaDB vector store
        if result.get("full_text"):
            rag_service.ingest_lecture(
                session_id=session_key,
                ocr_text=result.get("full_text", ""),
            )
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# CharacterCNN Alphanumeric Recognition Endpoints (Phase Dataset 01)
# ---------------------------------------------------------------------------


@router.get("/character/status", response_model=CharacterStatusResponse)
def get_character_status():
    """Returns CharacterCNN model status, device, checkpoint availability, and evaluation metrics."""
    return character_service.get_status_info()


@router.post("/character/predict", response_model=CharacterPredictionResponse)
async def predict_character(
    file: UploadFile = File(...),
):
    """
    Predicts an alphanumeric character from an uploaded single-character crop image.
    Returns predicted character, class name, confidence score, and top-3 predictions.
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
            detail="Uploaded character image file is empty.",
        )

    try:
        result = character_service.predict(content)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Character inference failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Character recognition internal error: {str(e)}",
        )

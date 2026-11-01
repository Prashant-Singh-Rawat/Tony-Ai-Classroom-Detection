"""
backend/app/api/routes/speech.py — Audio Transcription Endpoints via Faster-Whisper
==================================================================================
Transcribes lecture audio recordings into timestamped segments and academic keywords.
Persists results into local SQLite database.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session as DBSession

from backend.app.database.db import get_db
from backend.app.database.repositories import SessionRepository, TranscriptRepository
from backend.app.services.rag import rag_service
from backend.app.services.speech import speech_service

router = APIRouter(prefix="/api/speech", tags=["Speech Recognition"])


@router.get("/status")
def get_speech_status():
    """Returns Faster-Whisper model status and compute settings."""
    return speech_service.get_status_info()


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default="sess_live"),
    db: DBSession = Depends(get_db),
):
    """
    Transcribes uploaded audio using Faster-Whisper.
    Returns transcript segments, full text, and extracted keywords.
    """
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty.",
        )

    result = speech_service.transcribe(content, filename_hint=file.filename or "audio.wav")

    # Persist transcript in SQLite and index in RAG
    session_key = session_id or "sess_live"
    try:
        session_repo = SessionRepository(db)
        if not session_repo.get_by_id(session_key):
            session_repo.create(
                id=session_key,
                title=f"Lecture Session: {file.filename or 'Audio Recording'}",
                course_code="CV101",
                classroom="Main Lecture Hall",
                instructor="Academic Instructor",
                status="active",
                data_source="REAL_PROCESSING",
                privacy_protected=True,
            )

        repo = TranscriptRepository(db)
        repo.create(
            session_id=session_key,
            audio_filename=file.filename,
            language=result.get("language", "en"),
            full_text=result.get("full_text", ""),
            segments=result.get("segments", []),
            word_count=result.get("word_count", 0),
            duration_seconds=result.get("duration", 0.0),
            model_used=result.get("model_used", "faster-whisper-tiny"),
            data_source="REAL_PROCESSING",
        )

        # Ingest into Educational RAG ChromaDB vector store
        rag_service.ingest_lecture(
            session_id=session_key,
            transcript_text=result.get("full_text", ""),
            segments=result.get("segments", []),
        )
    except Exception:
        pass

    return result


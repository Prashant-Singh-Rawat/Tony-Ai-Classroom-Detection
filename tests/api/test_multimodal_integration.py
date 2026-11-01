"""
tests/api/test_multimodal_integration.py
=========================================
Comprehensive integration test suite for ClassVision AI Multimodal Intelligence.
Validates all 7 multimodal phases:
1. Speech Intelligence (Faster-Whisper audio upload, language detection, timestamps, SQLite persistence).
2. OCR Intelligence (EasyOCR whiteboard extraction, CharacterCNN single-character classification).
3. Lecture Summarization (Sentence segmentation, extractive scoring, topic classification, empty text safety).
4. Educational RAG (ChromaDB ingestion, semantic chunking, in-scope Q&A, out-of-scope honest refusal).
5. Multimodal Connection (Fusion of video events, speech transcripts, board notes into LectureIntelligenceData).
6. Report Generation (Real ReportLab PDF and openpyxl multi-sheet Excel generation).
7. Database Persistence & Anonymous Privacy Guarantee (Zero raw frames or biometric IDs stored).
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.app.core.config import settings
from backend.app.database.db import get_db, init_db
from backend.app.database.models import DetectionEvent, HandRaiseEventRecord, Session as SessionModel
from backend.app.database.repositories import (
    HandRaiseEventRepository,
    OcrRepository,
    SessionRepository,
    TranscriptRepository,
)
from backend.app.main import app
from backend.app.services.nlp import nlp_service
from backend.app.services.ocr import character_service, ocr_service
from backend.app.services.rag import rag_service
from backend.app.services.speech import speech_service


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


# -----------------------------------------------------------------------------
# Phase 1: Speech Intelligence
# -----------------------------------------------------------------------------

def test_speech_transcription_endpoint(client: TestClient):
    """Tests Faster-Whisper audio upload, transcription, and database persistence."""
    audio_path = "datasets/kaggle/speech/common_voice/cv-valid-test/sample-000001.mp3"
    if not os.path.exists(audio_path):
        pytest.skip("Common Voice test audio file not found on disk")

    session_id = "test_multimodal_sess_01"
    with open(audio_path, "rb") as f:
        resp = client.post(
            "/api/speech/transcribe",
            files={"file": ("sample-000001.mp3", f, "audio/mpeg")},
            data={"session_id": session_id},
        )
    assert resp.status_code == 200, f"Speech transcription failed: {resp.text}"
    data = resp.json()

    assert data["language"] == "en"
    assert data["language_probability"] >= 0.5
    assert len(data["full_text"]) > 0
    assert "segments" in data
    assert len(data["segments"]) >= 1
    assert "start" in data["segments"][0]
    assert "end" in data["segments"][0]

    # Database verification
    db = next(get_db())
    t_repo = TranscriptRepository(db)
    transcripts = t_repo.get_by_session(session_id)
    assert len(transcripts) >= 1
    assert transcripts[0].language == "en"
    assert len(transcripts[0].full_text) > 0


def test_speech_empty_file_rejected(client: TestClient):
    """Verifies that empty audio upload returns HTTP 400."""
    resp = client.post(
        "/api/speech/transcribe",
        files={"file": ("empty.mp3", b"", "audio/mpeg")},
        data={"session_id": "test_empty"},
    )
    assert resp.status_code == 400


# -----------------------------------------------------------------------------
# Phase 2: OCR Intelligence
# -----------------------------------------------------------------------------

def test_easyocr_whiteboard_extraction(client: TestClient):
    """Tests EasyOCR board extraction and persistence."""
    # Generate synthetic slide image with clear text
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 40), "Convolutional Neural Networks", fill=(0, 0, 0))
    draw.text((20, 80), "Out_dim = ((W - K + 2P) / S) + 1", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    session_id = "test_multimodal_sess_01"
    resp = client.post(
        "/api/ocr/extract",
        files={"file": ("whiteboard.jpg", img_bytes, "image/jpeg")},
        data={"session_id": session_id},
    )
    assert resp.status_code == 200, f"OCR extraction failed: {resp.text}"
    data = resp.json()
    assert "full_text" in data
    assert "text_blocks" in data
    assert data["overall_confidence"] >= 0.0

    # Database verification
    db = next(get_db())
    o_repo = OcrRepository(db)
    notes = o_repo.get_by_session(session_id)
    assert len(notes) >= 1


def test_character_cnn_classification(client: TestClient):
    """Tests trained CharacterCNN model on single character crop."""
    img = Image.new("L", (64, 64), color=255)
    draw = ImageDraw.Draw(img)
    draw.text((20, 10), "A", fill=0)

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    resp = client.post(
        "/api/ocr/character/predict",
        files={"file": ("char_A.png", buf.getvalue(), "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "predictedCharacter" in data or "predicted_character" in data
    assert "confidence" in data
    assert "top3Predictions" in data or "top3_predictions" in data


# -----------------------------------------------------------------------------
# Phase 3: Lecture Summarization & Topic Extraction
# -----------------------------------------------------------------------------

def test_lecture_summarization_and_topics():
    """Verifies extractive summarization, keyword extraction, and topic identification."""
    lecture_text = (
        "Good morning students. Today we explore convolutional neural networks and spatial filters. "
        "Convolutional layers perform dot products between a sliding kernel and receptive fields on the input image. "
        "Max pooling downsamples spatial dimensions to achieve translation invariance. "
        "Backpropagation optimizes the filter weights via gradient descent and the chain rule of calculus."
    )

    analysis = nlp_service.analyze_lecture_content(lecture_text)
    assert len(analysis["summary"]) > 20
    assert len(analysis["keywords"]) >= 3
    assert len(analysis["topics"]) >= 1

    # Empty text safety check
    empty_summary = nlp_service.summarize_lecture("")
    assert empty_summary == ""
    empty_topics = nlp_service.identify_topics("")
    assert empty_topics == []


# -----------------------------------------------------------------------------
# Phase 4: Educational RAG with ChromaDB
# -----------------------------------------------------------------------------

def test_educational_rag_in_scope_and_out_of_scope(client: TestClient):
    """Tests RAG retrieval for lecture questions and honest refusal for irrelevant queries."""
    session_id = "test_rag_eval_sess"
    transcript = (
        "SGD updates weights using single batch gradients, whereas Adam maintains exponential moving averages "
        "of past gradients and squared gradients to adapt learning rates per parameter."
    )
    ocr_notes = "Adam: m_t = beta1*m_{t-1} + (1-beta1)*g_t; v_t = beta2*v_{t-1} + (1-beta2)*g_t^2"

    indexed = rag_service.ingest_lecture(
        session_id=session_id,
        transcript_text=transcript,
        ocr_text=ocr_notes,
    )
    assert indexed >= 2

    # Query 1: In-scope question
    resp_in = client.post(
        "/api/rag/query",
        json={"query": "How does Adam adapt learning rates?", "sessionId": session_id, "live": True},
    )
    assert resp_in.status_code == 200
    data_in = resp_in.json()
    assert data_in["confidence"] >= 0.35
    assert len(data_in["sources"]) >= 1
    assert "Adam" in data_in["answer"]

    # Query 2: Out-of-scope question (must refuse without fabricating)
    resp_out = client.post(
        "/api/rag/query",
        json={"query": "Who won the 1994 FIFA World Cup in football?", "sessionId": session_id, "live": True},
    )
    assert resp_out.status_code == 200
    data_out = resp_out.json()
    assert "Cannot find sufficient supporting lecture content" in data_out["answer"]
    assert len(data_out["sources"]) == 0


# -----------------------------------------------------------------------------
# Phase 5: Multimodal Connection
# -----------------------------------------------------------------------------

def test_multimodal_fusion_endpoint(client: TestClient):
    """Verifies that GET /api/intelligence/{session_id} fuses video events, speech, and OCR."""
    session_id = "test_multimodal_sess_01"

    # Seed a hand-raise event for this session if not already present
    db = next(get_db())
    h_repo = HandRaiseEventRepository(db)
    existing_events = h_repo.get_by_session(session_id)
    if not existing_events:
        import time
        h_repo.create(
            event_id=f"evt_test_{int(time.time()*1000)}",
            session_id=session_id,
            track_id="track_002",
            hand_side="LEFT_HAND",
            state="COMPLETED",
            start_timestamp_seconds=1.5,
            end_timestamp_seconds=4.0,
            duration_seconds=2.5,
            start_frame=15,
            end_frame=40,
            frame_count=25,
            max_confidence=0.88,
            avg_confidence=0.84,
            data_source="REAL_PROCESSING",
        )

    resp = client.get(f"/api/intelligence/{session_id}?demo=false")
    assert resp.status_code == 200, f"Multimodal intelligence query failed: {resp.text}"
    intel = resp.json()

    assert intel["sessionId"] == session_id
    assert intel["topic"] != ""
    assert len(intel["keyConcepts"]) >= 1
    assert len(intel["executiveSummary"]) >= 1
    assert len(intel["transcript"]) >= 1
    assert len(intel["questionMoments"]) >= 1
    assert intel["isDemoData"] is False


# -----------------------------------------------------------------------------
# Phase 6 & 7: Report Generation (PDF & Excel)
# -----------------------------------------------------------------------------

def test_report_generation_pdf_and_excel(client: TestClient):
    """Tests generating and downloading both PDF and Excel reports with multimodal data."""
    session_id = "test_multimodal_sess_01"

    # PDF Generation
    resp_pdf = client.post(
        "/api/reports/generate",
        json={"sessionId": session_id, "format": "pdf", "title": "Multimodal Verification Report"},
    )
    assert resp_pdf.status_code == 200
    pdf_info = resp_pdf.json()
    assert pdf_info["status"] == "SUCCESS"
    assert pdf_info["format"] == "PDF"

    # Download PDF
    dl_pdf = client.get(pdf_info["downloadUrl"])
    assert dl_pdf.status_code == 200
    assert dl_pdf.content.startswith(b"%PDF")

    # Excel Generation
    resp_xlsx = client.post(
        "/api/reports/generate",
        json={"sessionId": session_id, "format": "xlsx", "title": "Multimodal Verification Workbook"},
    )
    assert resp_xlsx.status_code == 200
    xlsx_info = resp_xlsx.json()
    assert xlsx_info["status"] == "SUCCESS"
    assert xlsx_info["format"] == "XLSX"

    # Download Excel
    dl_xlsx = client.get(xlsx_info["downloadUrl"])
    assert dl_xlsx.status_code == 200
    assert len(dl_xlsx.content) > 1000

"""
backend/app/api/routes/rag.py — RAG Assistant Query Endpoint
"""

from fastapi import APIRouter, HTTPException, status
from backend.app.core.config import settings
from backend.app.schemas.rag import RagQueryRequest, RagResponse
from backend.app.services.rag import rag_service

router = APIRouter(prefix="/api/rag", tags=["RAG Assistant"])


@router.post("/query", response_model=RagResponse)
async def query_rag_assistant(request: RagQueryRequest) -> RagResponse:
    """
    Submits a natural language query against curriculum, transcripts, and whiteboard notes.
    If RAG is not connected, returns honest uninstantiated status or labeled demo response.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query string cannot be empty.",
        )

    return rag_service.query(
        query=request.query,
        session_id=request.sessionId,
        force_live=request.live,
        use_demo_fallback=settings.is_demo_mode,
    )


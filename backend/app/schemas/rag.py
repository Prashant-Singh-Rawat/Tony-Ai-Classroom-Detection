"""
backend/app/schemas/rag.py — RAG assistant query and response schemas
"""

from typing import List, Literal, Optional
from pydantic import Field, field_validator
from backend.app.schemas.common import CamelModel


class RagQueryRequest(CamelModel):
    query: str
    sessionId: Optional[str] = Field(default=None, alias="session_id")
    live: bool = Field(default=False, description="Force real RAG lookup instead of demo fallback")

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Query cannot be empty or whitespace only")
        return clean


class RagSource(CamelModel):
    title: str
    sourceType: Literal["transcript", "slide_ocr", "syllabus"] = Field(..., alias="sourceType")
    timestamp: Optional[str] = None
    pageOrSlide: Optional[int] = Field(default=None, alias="pageOrSlide")
    snippet: str


class RagResponse(CamelModel):
    query: str
    answer: str
    confidence: float
    sources: List[RagSource] = Field(default_factory=list)
    isPlaceholder: bool = Field(default=True, alias="isPlaceholder")
    isDemoData: bool = Field(default=True, alias="isDemoData")
    status: Optional[str] = None


"""
backend/app/schemas/intelligence.py — Lecture Intelligence & Multimodal fusion schemas
"""

from typing import List, Literal, Optional
from pydantic import Field
from backend.app.schemas.common import CamelModel


class TranscriptItem(CamelModel):
    id: str
    speaker: str
    timestamp: str
    text: str
    relatedGesture: Optional[str] = Field(default=None, alias="relatedGesture")


class OcrNoteItem(CamelModel):
    id: str
    timestamp: str
    boardRegion: Literal["left_blackboard", "center_projector", "right_whiteboard"] = Field(
        ..., alias="boardRegion"
    )
    detectedText: str = Field(..., alias="detectedText")
    tags: List[str] = Field(default_factory=list)


class QuestionMomentItem(CamelModel):
    timestamp: str
    studentId: str = Field(..., alias="studentId")
    promptOrQuestion: str = Field(..., alias="promptOrQuestion")
    answered: bool


class LectureIntelligenceData(CamelModel):
    sessionId: str = Field(..., alias="sessionId")
    topic: str
    keyConcepts: List[str] = Field(default_factory=list, alias="keyConcepts")
    executiveSummary: List[str] = Field(default_factory=list, alias="executiveSummary")
    transcript: List[TranscriptItem] = Field(default_factory=list)
    boardNotes: List[OcrNoteItem] = Field(default_factory=list, alias="boardNotes")
    questionMoments: List[QuestionMomentItem] = Field(
        default_factory=list, alias="questionMoments"
    )
    isDemoData: bool = Field(default=True, alias="isDemoData")


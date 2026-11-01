"""
backend/app/schemas/character_recognition.py — Pydantic Schemas for Character Recognition
========================================================================================
Schemas for predicting alphanumeric characters (0-9, A-Z, a-z) from single-character crops.
Uses CamelModel with field aliases to accept snake_case service dicts while serializing
to camelCase JSON for API clients and tests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field
from backend.app.schemas.common import CamelModel


class CharacterTopPrediction(CamelModel):
    """A single candidate prediction from top-K classifier output."""

    character: str = Field(..., description="Human-readable character glyph (e.g. 'A', 'a', '0')")
    class_name: str = Field(..., alias="className", description="Dataset folder class name (e.g. 'A_U', 'a_L', '0')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Softmax confidence probability")


class CharacterPredictionResponse(CamelModel):
    """Response payload for POST /api/ocr/character/predict."""

    predicted_character: str = Field(..., alias="predictedCharacter")
    class_name: str = Field(..., alias="className")
    confidence: float = Field(..., ge=0.0, le=1.0)
    top3_predictions: List[CharacterTopPrediction] = Field(..., alias="top3Predictions")
    inference_time_ms: float = Field(..., alias="inferenceTimeMs")
    device: str
    model_name: str = Field(default="CharacterCNN-62", alias="modelName")
    provenance: str = "TRAINED MODEL"
    status: str = "SUCCESS"


class CharacterStatusResponse(CamelModel):
    """Response payload for GET /api/ocr/character/status."""

    module: str = "character_recognition"
    status: str = "READY"
    model_name: str = Field(default="CharacterCNN-62", alias="modelName")
    model_loaded: bool = Field(..., alias="modelLoaded")
    checkpoint_available: bool = Field(..., alias="checkpointAvailable")
    checkpoint_path: str = Field(..., alias="checkpointPath")
    num_classes: int = Field(default=62, alias="numClasses")
    device: str
    provenance: str = "TRAINED MODEL"
    training_dataset: str = Field(
        default="Kaggle English Character Recognition (62 classes)", alias="trainingDataset"
    )
    evaluation_metrics: Optional[Dict[str, Any]] = Field(default=None, alias="evaluationMetrics")

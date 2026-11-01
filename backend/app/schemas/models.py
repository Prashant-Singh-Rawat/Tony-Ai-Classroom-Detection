"""
backend/app/schemas/models.py — Model and Dataset Status schemas
"""

from typing import Any, Dict, Literal
from pydantic import Field
from backend.app.schemas.common import CamelModel


class KaggleGestureDatasetStatus(CamelModel):
    totalImages: int = Field(..., alias="totalImages")
    trainImages: int = Field(..., alias="trainImages")
    testImages: int = Field(..., alias="testImages")
    classes: int
    semanticsVerified: bool = Field(..., alias="semanticsVerified")
    disclaimer: str


class RealClassroomDatasetStatus(CamelModel):
    collectedVideos: int = Field(..., alias="collectedVideos")
    extractedFrames: int = Field(..., alias="extractedFrames")
    annotationsCount: int = Field(..., alias="annotationsCount")
    targetPlan: str = Field(..., alias="targetPlan")


class EvaluationMetricsStatus(CamelModel):
    precision: str
    recall: str
    f1Score: str = Field(..., alias="f1Score")
    map50: str
    status: Literal["NOT CONNECTED", "CALIBRATED", "EVALUATING"] = "NOT CONNECTED"


class VerifiedTestsStatus(CamelModel):
    passed: int
    total: int
    status: str


class ModelStatusData(CamelModel):
    modelCheckpointsCount: int = Field(..., alias="modelCheckpointsCount")
    activeCheckpoint: str = Field(..., alias="activeCheckpoint")
    trainingStatus: Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "NOT CONNECTED"] = Field(
        ..., alias="trainingStatus"
    )
    kaggleGestureDataset: KaggleGestureDatasetStatus = Field(..., alias="kaggleGestureDataset")
    realClassroomDataset: RealClassroomDatasetStatus = Field(..., alias="realClassroomDataset")
    evaluationMetrics: EvaluationMetricsStatus = Field(..., alias="evaluationMetrics")
    verifiedTests: VerifiedTestsStatus = Field(..., alias="verifiedTests")


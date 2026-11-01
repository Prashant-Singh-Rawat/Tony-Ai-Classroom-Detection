"""
backend/app/schemas/reports.py — Reports and Model Quality audit schemas
"""

from typing import Any, Dict, List, Literal
from pydantic import Field
from backend.app.schemas.common import CamelModel


class ReportItem(CamelModel):
    id: str
    sessionId: str = Field(..., alias="sessionId")
    title: str
    generatedDate: str = Field(..., alias="generatedDate")
    fileSize: str = Field(..., alias="fileSize")
    format: Literal["PDF", "CSV", "JSON"]
    metricsSummary: Dict[str, Any] = Field(..., alias="metricsSummary")
    isDemoData: bool = Field(default=True, alias="isDemoData")


class ModelQualityReport(CamelModel):
    status: Literal["NO_MODEL_TRAINED", "TRAINED", "EVALUATING"] = "NO_MODEL_TRAINED"
    modelCheckpoint: str = Field(
        default="None (Phase 1.0 Backend Foundation)", alias="modelCheckpoint"
    )
    evaluationDataset: str = Field(
        default="None (Collection starts post 12 October 2026)", alias="evaluationDataset"
    )
    plannedMetrics: List[str] = Field(default_factory=list, alias="plannedMetrics")
    privacyGuarantees: List[str] = Field(default_factory=list, alias="privacyGuarantees")


class ReportsResponse(CamelModel):
    reports: List[ReportItem] = Field(default_factory=list)
    modelQuality: ModelQualityReport = Field(..., alias="modelQuality")


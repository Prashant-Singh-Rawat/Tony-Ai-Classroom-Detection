"""
backend/app/schemas/system.py — Overall System Status schemas
"""

from pydantic import Field
from backend.app.schemas.common import CamelModel


class SystemStatus(CamelModel):
    backendConnected: bool = Field(default=True, alias="backendConnected")
    useDemoData: bool = Field(default=True, alias="useDemoData")
    dataRoot: str = Field(..., alias="dataRoot")
    privacyMode: str = Field(..., alias="privacyMode")
    retentionDays: int = Field(..., alias="retentionDays")
    cameraSource: str = Field(..., alias="cameraSource")
    modelStatus: str = Field(..., alias="modelStatus")
    buildVersion: str = Field(..., alias="buildVersion")


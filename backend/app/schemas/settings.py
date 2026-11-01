"""
backend/app/schemas/settings.py — Settings & Configuration schemas
"""

from pydantic import Field
from backend.app.schemas.common import CamelModel


class CameraSettings(CamelModel):
    source: str
    resolution: str
    frameRate: int = Field(..., alias="frameRate")
    hardwareConnected: bool = Field(..., alias="hardwareConnected")


class PrivacySettings(CamelModel):
    faceBlurringActive: bool = Field(..., alias="faceBlurringActive")
    storageRoot: str = Field(..., alias="storageRoot")
    retentionDays: int = Field(..., alias="retentionDays")
    storeRawVideo: bool = Field(..., alias="storeRawVideo")
    oneDriveWarningAcknowledged: bool = Field(..., alias="oneDriveWarningAcknowledged")


class AiModulesSettings(CamelModel):
    visionInference: str = Field(..., alias="visionInference")
    whisperTranscription: str = Field(..., alias="whisperTranscription")
    easyOcr: str = Field(..., alias="easyOcr")
    ragAssistant: str = Field(..., alias="ragAssistant")


class SystemMetaSettings(CamelModel):
    version: str
    demoModeActive: bool = Field(..., alias="demoModeActive")
    offlineOnly: bool = Field(..., alias="offlineOnly")


class SettingsData(CamelModel):
    camera: CameraSettings
    privacy: PrivacySettings
    aiModules: AiModulesSettings = Field(..., alias="aiModules")
    system: SystemMetaSettings


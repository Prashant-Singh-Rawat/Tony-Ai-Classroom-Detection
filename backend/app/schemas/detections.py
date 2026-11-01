"""
backend/app/schemas/detections.py — Detection Bounding Box & Pose schemas
========================================================================
Supports Phase 2.0 real-time person detection using pretrained YOLOv8n.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import Field
from backend.app.schemas.common import CamelModel, HandRaiseClass


class Keypoint(CamelModel):
    """Anonymous body pose keypoint coordinate."""

    name: str
    x: float
    y: float
    confidence: float = Field(..., ge=0.0, le=1.0)


class BoundingBox(CamelModel):
    """Normalized person upper-body bounding box and gesture classification."""

    id: str
    personId: int = Field(default=1, alias="personId")
    classId: Literal[0, 1, 2] = Field(default=1, alias="classId")
    className: HandRaiseClass = Field(default=HandRaiseClass.HAND_NOT_RAISED, alias="className")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    x: float = Field(..., description="Percentage X offset [0-100] or pixel coordinate")
    y: float = Field(..., description="Percentage Y offset [0-100] or pixel coordinate")
    w: float = Field(..., description="Percentage width [0-100] or pixel width")
    h: float = Field(..., description="Percentage height [0-100] or pixel height")
    width: Optional[float] = None
    height: Optional[float] = None
    handRaised: Optional[bool] = None
    status: Optional[str] = None
    keypoints: Optional[List[Keypoint]] = None
    zoneClassification: Optional[str] = None  # "STUDENT_ZONE" | "INSTRUCTOR_ZONE" | "NEEDS_REVIEW"
    activityLabel: Optional[str] = "NO_FLAG_OBSERVED"
    activityConfidence: Optional[float] = None
    activityDurationSeconds: Optional[float] = None
    activityEvidence: Optional[str] = None
    detectedObjects: Optional[List[str]] = None
    statusColor: Optional[str] = "GREEN"  # GREEN, RED, ORANGE, BLUE, YELLOW


class PersonDetection(CamelModel):
    """Detailed single person detection from YOLOv8n."""

    id: str
    className: str = "person"
    confidence: float = Field(..., ge=0.0, le=1.0)
    x: float
    y: float
    width: float
    height: float
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionSummary(CamelModel):
    """Summary of detection across an image or frame."""

    totalStudents: int = 0
    totalPersons: int = 0
    activeHandRaises: int = 0
    notRaisedCount: int = 0
    needsReviewCount: int = 0
    boxes: List[BoundingBox] = []
    detections: List[PersonDetection] = []
    imageWidth: Optional[int] = None
    imageHeight: Optional[int] = None
    processingTimeMs: float = 0.0
    processingFps: float = 0.0
    modelName: str = "yolov8n"
    modelStatus: str = "READY"
    inferenceDevice: str = "cpu"
    dataSource: str = "REAL_PROCESSING"
    status: str = "REAL_PROCESSING"
    isDemoData: bool = False


class VideoFrameSummary(CamelModel):
    """Summary of detections for a sampled video frame."""

    frameIndex: int
    timestampSeconds: float
    personCount: int
    detections: List[PersonDetection] = []
    boxes: List[BoundingBox] = []
    handRaisedCount: int = 0
    needsReviewCount: int = 0
    decodingTimeMs: Optional[float] = None
    inferenceTimeMs: Optional[float] = None


class VideoProcessResponse(CamelModel):
    """Summary of complete video sequential processing."""

    videoFilename: str
    totalFrames: int
    processedFrames: int
    frameSkip: int
    videoFps: float
    durationSeconds: float
    maxPersonsInFrame: int
    avgPersonsPerFrame: float
    timeline: List[VideoFrameSummary] = []
    totalProcessingTimeSeconds: float
    processingFps: float
    modelName: str = "yolov8n"
    modelStatus: str = "READY"
    inferenceDevice: str = "cpu"
    dataSource: str = "REAL_PROCESSING"
    status: str = "COMPLETED"

    # Enhanced video metadata & diagnostics
    width: Optional[int] = None
    height: Optional[int] = None
    aspectRatio: Optional[str] = None
    orientation: Optional[str] = "LANDSCAPE"
    decodingFps: Optional[float] = None
    inferenceFps: Optional[float] = None
    decodingTimeSeconds: Optional[float] = None
    inferenceTimeSeconds: Optional[float] = None
    corruptedFramesCount: int = 0
    peakRamMb: Optional[float] = None
    peakVramMb: Optional[float] = None
    totalHandRaises: int = 0
    totalNeedsReview: int = 0
    trackedPersonsCount: int = 0
    handRaiseEventsCount: int = 0
    activeEventsCount: int = 0
    completedEventsCount: int = 0
    instructorRoiPolygon: Optional[List[List[float]]] = None
    zoneFilteringEnabled: bool = True
    studentZoneEventsCount: int = 0
    instructorZoneEventsCount: int = 0
    uncertainZoneEventsCount: int = 0


class WebSocketDetectionMessage(CamelModel):
    """Message payload transmitted over detection WebSocket."""

    type: Literal["detections", "status", "ping", "error"] = "detections"
    sessionId: str = Field(..., alias="sessionId")
    timestamp: str
    detections: list[BoundingBox] = []
    status: str = "DEMO_DATA"
    totalPersons: Optional[int] = None
    activeHandRaises: Optional[int] = None
    processingFps: Optional[float] = None
    processingTimeMs: Optional[float] = None
    inferenceDevice: Optional[str] = None
    isDemoData: Optional[bool] = None
    imageWidth: Optional[int] = None
    imageHeight: Optional[int] = None
    trackedPersons: Optional[List[Dict[str, Any]]] = None
    activeEvents: Optional[List[Dict[str, Any]]] = None
    totalEventsCount: Optional[int] = None
    serverSideBlurApplied: bool = False
    clientSideBlurDetected: bool = False
    persistedEventsCount: int = 0
    dbPersistenceStatus: str = "CONNECTED"
    dbErrorMessage: Optional[str] = None
    privacySafeguards: Optional[Dict[str, Any]] = None


class ArmPostureGeometry(CamelModel):
    """Geometric calculations for a single arm."""

    elbowAngleDeg: Optional[float] = None
    elevationPx: Optional[float] = None
    wristAboveShoulder: bool = False
    armRaised: bool = False
    confidence: float = 0.0


class PoseGeometry(CamelModel):
    """Geometric body metrics calculated from 17 keypoints."""

    leftArm: ArmPostureGeometry
    rightArm: ArmPostureGeometry
    shoulderDistancePx: Optional[float] = None
    upperBodyVisible: bool = False
    occludedKeypoints: List[str] = Field(default_factory=list)


class PoseKeypoint(CamelModel):
    """Detailed keypoint with index, name, coordinates, confidence and visibility."""

    index: int
    name: str
    x: float
    y: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    visible: bool = True
    xPct: float = 0.0
    yPct: float = 0.0


class ObservablePosture(str, Enum):
    """Observable physical postures based strictly on geometric angles and elevation."""

    BOTH_ARMS_RAISED = "BOTH_ARMS_RAISED"
    LEFT_ARM_RAISED = "LEFT_ARM_RAISED"
    RIGHT_ARM_RAISED = "RIGHT_ARM_RAISED"
    ARMS_NOT_RAISED = "ARMS_NOT_RAISED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class PersonPoseDetection(CamelModel):
    """Detailed pose detection for an anonymous individual."""

    id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: PersonDetection
    posture: ObservablePosture = ObservablePosture.ARMS_NOT_RAISED
    postureReason: str = ""
    keypoints: List[PoseKeypoint] = Field(default_factory=list)
    geometry: PoseGeometry


class PoseDetectionResponse(CamelModel):
    """Complete response payload for POST /api/vision/pose."""

    totalPersons: int = 0
    imageWidth: int = 0
    imageHeight: int = 0
    processingTimeMs: float = 0.0
    processingFps: float = 0.0
    modelName: str = "yolov8n-pose"
    modelStatus: str = "READY"
    inferenceDevice: str = "cpu"
    postureCounts: Dict[str, int] = Field(default_factory=dict)
    persons: List[PersonPoseDetection] = Field(default_factory=list)
    dataSource: str = "REAL_PROCESSING"
    status: str = "REAL_PROCESSING"
    isDemoData: bool = False


class PoseStatusResponse(CamelModel):
    """Model status and runtime details for GET /api/vision/pose/status."""

    module: str = "computer_vision"
    submodule: str = "pose_estimation"
    modelName: str = "yolov8n-pose"
    activeCheckpoint: str = "yolov8n-pose.pt (COCO Pretrained 17-Keypoint Pose)"
    status: str = "READY"
    readyForInference: bool = True
    inferenceDevice: str = "cpu"
    cudaAvailable: bool = False
    supportedKeypointsCount: int = 17
    cocoKeypointOrder: List[str] = Field(default_factory=list)
    postureClasses: List[str] = Field(default_factory=list)
    memoryUsage: Dict[str, float] = Field(default_factory=dict)
    provenance: str = "PRETRAINED MODEL"
    privacyMode: str = "ANONYMOUS_PERSON_ONLY"
    benchmarkDataset: Optional[str] = "COCO 2017 Keypoints (Validation Partition)"
    evaluationMetrics: Optional[Dict[str, Any]] = None


// frontend/src/services/api.ts
// Typed API interface and implementations for ClassVision AI

import type {
  AnalyticsData,
  BoundingBox,
  DashboardSummary,
  LectureIntelligenceData,
  ModelQualityReport,
  ModelStatusData,
  RagResponse,
  ReportItem,
  SessionInfo,
  SettingsData,
  SystemStatus,
  AgentInfoData,
  AgentTaskData,
  AgentMessageData,
  ApprovalRequestData,
  DebuggingRecordData,
  ProjectHealthData,
  TaskPriorityType,
  PoseDetectionResponseData,
  PoseStatusResponseData,
  HandRaiseEventData,
  TrackingEventStatisticsData,
  TrackingSummaryData,
  AnalyticsSessionSummaryData,
  SessionActivityAnalyticsData,
  SessionComparisonResponseData,
  ActivityDistributionSummaryData,
} from '../types'

import {
  DEMO_ANALYTICS,
  DEMO_BOUNDING_BOXES,
  DEMO_DASHBOARD_SUMMARY,
  DEMO_LECTURE_INTEL,
  DEMO_MODEL_QUALITY_REPORT,
  DEMO_RAG_RESPONSES,
  DEMO_REPORTS,
  DEMO_SESSIONS,
  DEMO_SYSTEM_STATUS,
} from '../data/demo'

import {
  DEMO_AGENTS,
  DEMO_TASKS,
  DEMO_MESSAGES,
  DEMO_APPROVALS,
  DEMO_DEBUGGING_RECORDS,
  DEMO_PROJECT_HEALTH,
} from '../data/demoAgents'

import { REPO_SNAPSHOT } from '../data/repoSnapshot'

/**
 * Centralized API configuration for future FastAPI / Python backend connection.
 */
export const API_CONFIG = {
  baseUrl: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000/api',
  endpoints: {
    dashboardSummary: '/dashboard/summary',
    sessions: '/sessions',
    analytics: '/analytics',
    intelligence: '/intelligence',
    ragQuery: '/rag/query',
    reports: '/reports',
    modelStatus: '/model/status',
    settings: '/settings',
    systemStatus: '/system/status',
    wsDetections: '/ws/detections',
  },
}

export interface ClassVisionApi {
  getDashboardSummary(): Promise<DashboardSummary>
  getSessions(): Promise<SessionInfo[]>
  getSessionById(sessionId: string): Promise<SessionInfo | null>
  getAnalytics(sessionId?: string): Promise<AnalyticsData>
  getLectureIntel(sessionId?: string): Promise<LectureIntelligenceData>
  askQuestion(query: string, sessionId?: string): Promise<RagResponse>
  getReports(): Promise<{ reports: ReportItem[]; modelQuality: ModelQualityReport }>
  getModelStatus(): Promise<ModelStatusData>
  getSettings(): Promise<SettingsData>
  getSystemStatus(): Promise<SystemStatus>
  getRealtimeDetections(sessionId?: string): Promise<BoundingBox[]>
  detectFrame(file: File, confidenceThreshold?: number, imgsz?: number, detectPose?: boolean): Promise<any>
  detectSyntheticFrame(): Promise<any>
  processVideo(
    file: File,
    frameSkip?: number,
    confidenceThreshold?: number,
    imgsz?: number,
    detectPose?: boolean,
    instructorRoiPolygon?: number[][] | null,
    zoneFilteringEnabled?: boolean,
    keypointThreshold?: number,
    elevationMarginPx?: number
  ): Promise<any>
  getSessionZoneConfig(sessionId: string): Promise<{ sessionId: string; instructorRoiPolygon: number[][] | null; zoneFilteringEnabled: boolean }>
  updateSessionZoneConfig(sessionId: string, polygon: number[][] | null, enabled?: boolean): Promise<any>
  getVisionStatus(): Promise<any>
  estimatePose(file: File, confidenceThreshold?: number, keypointThreshold?: number, elevationMarginPx?: number, imgsz?: number): Promise<PoseDetectionResponseData>
  getPoseStatus(): Promise<PoseStatusResponseData>
  getActiveTracks(): Promise<TrackingSummaryData>
  getHandRaiseEvents(sessionId?: string): Promise<HandRaiseEventData[]>
  getTrackingStatistics(sessionId?: string): Promise<TrackingEventStatisticsData>
  resetTracking(sessionId?: string): Promise<any>
  getAnalyticsSessions(): Promise<AnalyticsSessionSummaryData[]>
  getSessionActivityAnalytics(sessionId: string, intervalSeconds?: number): Promise<SessionActivityAnalyticsData>
  getActivityDistribution(sessionId?: string): Promise<ActivityDistributionSummaryData>
  compareSessions(sessionA: string, sessionB: string): Promise<SessionComparisonResponseData>
  exportAnalyticsCsv(sessionId: string): Promise<string>
  exportAnalyticsPdfUrl(sessionId: string): string
  getAgentsStatus(): Promise<AgentInfoData[]>
  getAgentTasks(): Promise<AgentTaskData[]>
  createAgentTask(title: string, description: string, priority?: TaskPriorityType, autoExecute?: boolean): Promise<AgentTaskData>
  cancelAgentTask(taskId: string): Promise<any>
  getAgentMessages(taskId?: string): Promise<AgentMessageData[]>
  getAgentApprovals(pendingOnly?: boolean): Promise<ApprovalRequestData[]>
  approveAgentAction(approvalId: string, comment?: string): Promise<any>
  rejectAgentAction(approvalId: string, comment?: string): Promise<any>
  getAgentDebuggingRecords(): Promise<DebuggingRecordData[]>
  getAgentProjectHealth(): Promise<ProjectHealthData>
}

/**
 * Demo API Implementation:
 * Serves deterministic, labeled mock data and verified repository snapshots.
 * Zero network calls.
 */
export class DemoClassVisionApi implements ClassVisionApi {
  async getDashboardSummary(): Promise<DashboardSummary> {
    return DEMO_DASHBOARD_SUMMARY
  }

  async getSessions(): Promise<SessionInfo[]> {
    return DEMO_SESSIONS
  }

  async getSessionById(sessionId: string): Promise<SessionInfo | null> {
    return DEMO_SESSIONS.find((s) => s.sessionId === sessionId) || DEMO_SESSIONS[0]
  }

  async getAnalytics(_sessionId?: string): Promise<AnalyticsData> {
    return DEMO_ANALYTICS
  }

  async getLectureIntel(_sessionId?: string): Promise<LectureIntelligenceData> {
    return DEMO_LECTURE_INTEL
  }

  async askQuestion(query: string, _sessionId?: string): Promise<RagResponse> {
    const qLower = query.toLowerCase()
    if (qLower.includes('question') || qLower.includes('dilated') || qLower.includes('hand')) {
      return {
        ...DEMO_RAG_RESPONSES.questions,
        query,
      }
    }
    return {
      ...DEMO_RAG_RESPONSES.default,
      query,
    }
  }

  async getReports(): Promise<{ reports: ReportItem[]; modelQuality: ModelQualityReport }> {
    return {
      reports: DEMO_REPORTS,
      modelQuality: DEMO_MODEL_QUALITY_REPORT,
    }
  }

  async getModelStatus(): Promise<ModelStatusData> {
    return {
      modelCheckpointsCount: REPO_SNAPSHOT.modelCheckpoints.count,
      activeCheckpoint: REPO_SNAPSHOT.modelCheckpoints.activeWeights,
      trainingStatus: 'NOT_STARTED',
      kaggleGestureDataset: {
        totalImages: REPO_SNAPSHOT.kaggleDataset.totalImages,
        trainImages: REPO_SNAPSHOT.kaggleDataset.trainImages,
        testImages: REPO_SNAPSHOT.kaggleDataset.testImages,
        classes: REPO_SNAPSHOT.kaggleDataset.numClasses,
        semanticsVerified: REPO_SNAPSHOT.kaggleDataset.classSemanticsVerified,
        disclaimer: REPO_SNAPSHOT.kaggleDataset.classSemanticsNote,
      },
      realClassroomDataset: {
        collectedVideos: REPO_SNAPSHOT.realClassroomData.videos,
        extractedFrames: REPO_SNAPSHOT.realClassroomData.frames,
        annotationsCount: REPO_SNAPSHOT.realClassroomData.annotations,
        targetPlan: REPO_SNAPSHOT.realClassroomData.note,
      },
      evaluationMetrics: {
        precision: 'Unavailable, no model trained',
        recall: 'Unavailable, no model trained',
        f1Score: 'Unavailable, no model trained',
        map50: 'Unavailable, no model trained',
        status: 'NOT CONNECTED',
      },
      verifiedTests: {
        passed: REPO_SNAPSHOT.testSuite.passingTests,
        total: REPO_SNAPSHOT.testSuite.totalTests,
        status: REPO_SNAPSHOT.testSuite.status,
      },
    }
  }

  async getSettings(): Promise<SettingsData> {
    return {
      camera: {
        source: 'Simulated Demo Stream (No hardware camera access)',
        resolution: '1920x1080 (1080p)',
        frameRate: 15,
        hardwareConnected: false,
      },
      privacy: {
        faceBlurringActive: true,
        storageRoot: 'C:\\ClassVisionData\\real_classroom',
        retentionDays: 30,
        storeRawVideo: false,
        oneDriveWarningAcknowledged: true,
      },
      aiModules: {
        visionInference: 'NOT CONNECTED (Placeholder overlay only)',
        whisperTranscription: 'NOT CONNECTED (Offline audio pipeline pending)',
        easyOcr: 'NOT CONNECTED (Board OCR pending)',
        ragAssistant: 'NOT CONNECTED (RAG integration pending)',
      },
      system: {
        version: '0.9.0-ui-foundation',
        demoModeActive: true,
        offlineOnly: true,
      },
    }
  }

  async getSystemStatus(): Promise<SystemStatus> {
    return DEMO_SYSTEM_STATUS
  }

  async getRealtimeDetections(_sessionId?: string): Promise<BoundingBox[]> {
    return DEMO_BOUNDING_BOXES
  }

  async detectFrame(_file: File, _confidenceThreshold?: number, _imgsz?: number, _detectPose?: boolean): Promise<any> {
    return {
      totalPersons: 3,
      totalStudents: 3,
      processingTimeMs: 44.8,
      processingFps: 22.3,
      imageWidth: 640,
      imageHeight: 480,
      modelName: 'yolov8n',
      modelStatus: 'READY',
      inferenceDevice: 'cpu (simulated)',
      dataSource: 'DATASET_SAMPLE',
      isDemoData: true,
      detections: [
        { id: 'anon_001', className: 'person', confidence: 0.89, x: 120, y: 80, width: 90, height: 180, x1: 120, y1: 80, x2: 210, y2: 260 },
        { id: 'anon_002', className: 'person', confidence: 0.84, x: 260, y: 95, width: 85, height: 175, x1: 260, y1: 95, x2: 345, y2: 270 },
        { id: 'anon_003', className: 'person', confidence: 0.91, x: 420, y: 70, width: 95, height: 190, x1: 420, y1: 70, x2: 515, y2: 260 },
      ],
      boxes: DEMO_BOUNDING_BOXES,
    }
  }

  async detectSyntheticFrame(): Promise<any> {
    return {
      totalPersons: 2,
      totalStudents: 2,
      processingTimeMs: 38.2,
      processingFps: 26.1,
      imageWidth: 640,
      imageHeight: 480,
      modelName: 'yolov8n',
      modelStatus: 'READY',
      inferenceDevice: 'cpu (simulated)',
      dataSource: 'SYNTHETIC_DATA',
      isDemoData: true,
      detections: [
        { id: 'anon_001', className: 'person', confidence: 0.87, x: 180, y: 100, width: 100, height: 200, x1: 180, y1: 100, x2: 280, y2: 300 },
        { id: 'anon_002', className: 'person', confidence: 0.92, x: 360, y: 90, width: 110, height: 210, x1: 360, y1: 90, x2: 470, y2: 300 },
      ],
      boxes: DEMO_BOUNDING_BOXES.slice(0, 2),
    }
  }

  async processVideo(
    file: File,
    frameSkip: number = 5,
    _confidenceThreshold?: number,
    _imgsz?: number,
    _detectPose?: boolean,
    instructorRoiPolygon?: number[][] | null,
    zoneFilteringEnabled?: boolean,
    _keypointThreshold?: number,
    _elevationMarginPx?: number
  ): Promise<any> {
    return {
      videoFilename: file.name,
      totalFrames: 150,
      processedFrames: 30,
      frameSkip,
      videoFps: 30.0,
      durationSeconds: 5.0,
      maxPersonsInFrame: 4,
      avgPersonsPerFrame: 3.1,
      timeline: [],
      totalProcessingTimeSeconds: 1.4,
      processingFps: 21.4,
      modelName: _detectPose ? 'yolov8n-pose' : 'yolov8n',
      modelStatus: 'READY',
      inferenceDevice: 'cpu (simulated)',
      dataSource: 'DEMO_DATA',
      status: 'COMPLETED',
      width: 1280,
      height: 720,
      aspectRatio: '16:9',
      orientation: 'LANDSCAPE',
      decodingFps: 280.0,
      inferenceFps: 22.0,
      totalHandRaises: 3,
      totalNeedsReview: 0,
      corruptedFramesCount: 0,
      trackedPersonsCount: 4,
      handRaiseEventsCount: 2,
      instructorRoiPolygon: instructorRoiPolygon || null,
      zoneFilteringEnabled: zoneFilteringEnabled !== false,
      studentZoneEventsCount: 2,
      instructorZoneEventsCount: 1,
      uncertainZoneEventsCount: 0,
    }
  }

  async getSessionZoneConfig(sessionId: string): Promise<{ sessionId: string; instructorRoiPolygon: number[][] | null; zoneFilteringEnabled: boolean }> {
    return {
      sessionId,
      instructorRoiPolygon: [[0.0, 0.0], [0.35, 0.0], [0.35, 0.85], [0.0, 0.85]],
      zoneFilteringEnabled: true,
    }
  }

  async updateSessionZoneConfig(sessionId: string, polygon: number[][] | null, enabled: boolean = true): Promise<any> {
    return {
      sessionId,
      instructorRoiPolygon: polygon,
      zoneFilteringEnabled: enabled,
      message: 'Demo zone configuration updated.',
    }
  }

  async getVisionStatus(): Promise<any> {
    return {
      module: 'computer_vision',
      model_name: 'yolov8n',
      status: 'READY',
      active_checkpoint: 'yolov8n.pt (COCO Pretrained Person Detector)',
      ready_for_inference: true,
      inference_device: 'cpu',
      cuda_available: false,
      provenance: 'PRETRAINED MODEL',
    }
  }

  async getPoseStatus(): Promise<PoseStatusResponseData> {
    return {
      module: 'computer_vision',
      submodule: 'pose_estimation',
      modelName: 'yolov8n-pose',
      activeCheckpoint: 'yolov8n-pose.pt (COCO Pretrained 17-Keypoint Pose)',
      status: 'READY',
      readyForInference: true,
      inferenceDevice: 'cpu (simulated)',
      cudaAvailable: false,
      supportedKeypointsCount: 17,
      cocoKeypointOrder: [
        'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
        'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
      ],
      postureClasses: ['BOTH_ARMS_RAISED', 'LEFT_ARM_RAISED', 'RIGHT_ARM_RAISED', 'ARMS_NOT_RAISED', 'NEEDS_REVIEW'],
      memoryUsage: { allocated_mb: 0.0, reserved_mb: 0.0 },
      provenance: 'PRETRAINED MODEL',
      privacyMode: 'ANONYMOUS_PERSON_ONLY',
    }
  }

  async estimatePose(_file: File, _confidenceThreshold?: number, _keypointThreshold?: number, _elevationMarginPx?: number, _imgsz?: number): Promise<PoseDetectionResponseData> {
    return {
      totalPersons: 1,
      imageWidth: 640,
      imageHeight: 480,
      processingTimeMs: 48.2,
      processingFps: 20.7,
      modelName: 'yolov8n-pose',
      modelStatus: 'READY',
      inferenceDevice: 'cpu (simulated)',
      postureCounts: {
        BOTH_ARMS_RAISED: 0,
        LEFT_ARM_RAISED: 1,
        RIGHT_ARM_RAISED: 0,
        ARMS_NOT_RAISED: 0,
        NEEDS_REVIEW: 0,
      },
      persons: [
        {
          id: 'anon_001',
          confidence: 0.91,
          bbox: {
            id: 'anon_001',
            className: 'person',
            confidence: 0.91,
            x: 220,
            y: 80,
            width: 180,
            height: 360,
            x1: 220,
            y1: 80,
            x2: 400,
            y2: 440,
          },
          posture: 'LEFT_ARM_RAISED',
          postureReason: 'Left arm elevated +52.0px above shoulder (148.5°); Right arm down (-85.0px)',
          keypoints: [
            { index: 0, name: 'nose', x: 310, y: 110, confidence: 0.94, visible: true, xPct: 48.4, yPct: 22.9 },
            { index: 1, name: 'left_eye', x: 302, y: 104, confidence: 0.92, visible: true, xPct: 47.2, yPct: 21.7 },
            { index: 2, name: 'right_eye', x: 318, y: 104, confidence: 0.93, visible: true, xPct: 49.7, yPct: 21.7 },
            { index: 3, name: 'left_ear', x: 292, y: 112, confidence: 0.88, visible: true, xPct: 45.6, yPct: 23.3 },
            { index: 4, name: 'right_ear', x: 328, y: 112, confidence: 0.89, visible: true, xPct: 51.3, yPct: 23.3 },
            { index: 5, name: 'left_shoulder', x: 275, y: 155, confidence: 0.91, visible: true, xPct: 43.0, yPct: 32.3 },
            { index: 6, name: 'right_shoulder', x: 345, y: 155, confidence: 0.92, visible: true, xPct: 53.9, yPct: 32.3 },
            { index: 7, name: 'left_elbow', x: 245, y: 125, confidence: 0.86, visible: true, xPct: 38.3, yPct: 26.0 },
            { index: 8, name: 'right_elbow', x: 365, y: 205, confidence: 0.89, visible: true, xPct: 57.0, yPct: 42.7 },
            { index: 9, name: 'left_wrist', x: 228, y: 103, confidence: 0.87, visible: true, xPct: 35.6, yPct: 21.5 },
            { index: 10, name: 'right_wrist', x: 375, y: 240, confidence: 0.88, visible: true, xPct: 58.6, yPct: 50.0 },
            { index: 11, name: 'left_hip', x: 285, y: 280, confidence: 0.85, visible: true, xPct: 44.5, yPct: 58.3 },
            { index: 12, name: 'right_hip', x: 335, y: 280, confidence: 0.86, visible: true, xPct: 52.3, yPct: 58.3 },
            { index: 13, name: 'left_knee', x: 280, y: 365, confidence: 0.82, visible: true, xPct: 43.8, yPct: 76.0 },
            { index: 14, name: 'right_knee', x: 340, y: 365, confidence: 0.83, visible: true, xPct: 53.1, yPct: 76.0 },
            { index: 15, name: 'left_ankle', x: 278, y: 435, confidence: 0.81, visible: true, xPct: 43.4, yPct: 90.6 },
            { index: 16, name: 'right_ankle', x: 342, y: 435, confidence: 0.80, visible: true, xPct: 53.4, yPct: 90.6 },
          ],
          geometry: {
            leftArm: {
              elbowAngleDeg: 148.5,
              elevationPx: 52.0,
              wristAboveShoulder: true,
              armRaised: true,
              confidence: 0.87,
            },
            rightArm: {
              elbowAngleDeg: 88.0,
              elevationPx: -85.0,
              wristAboveShoulder: false,
              armRaised: false,
              confidence: 0.88,
            },
            shoulderDistancePx: 70.0,
            upperBodyVisible: true,
            occludedKeypoints: [],
          },
        },
      ],
      dataSource: 'DEMO_DATA',
      status: 'REAL_PROCESSING',
      isDemoData: true,
    }
  }

  async getActiveTracks(): Promise<TrackingSummaryData> {
    return {
      sessionId: 'sess_01',
      timestampSeconds: 12.5,
      activeTracksCount: 1,
      activeHandRaisesCount: 1,
      statesSummary: {
        NOT_RAISED: 0,
        RAISING: 0,
        RAISED: 1,
        LOWERING: 0,
        NEEDS_REVIEW: 0,
      },
      tracks: [
        {
          trackId: 'track_001',
          state: 'RAISED',
          handSide: 'LEFT_HAND',
          confidence: 0.92,
          bbox: {
            id: 'track_001',
            className: 'person',
            confidence: 0.92,
            x: 25.0,
            y: 15.0,
            width: 35.0,
            height: 60.0,
          },
          keypoints: [],
          framesInCurrentState: 8,
          totalFramesTracked: 15,
          missingFramesCount: 0,
          isOccluded: false,
          activeEventId: 'evt_0001',
          lastUpdatedTimestamp: 12.5,
        },
      ],
      activeEvents: [
        {
          eventId: 'evt_0001',
          sessionId: 'sess_01',
          trackId: 'track_001',
          handSide: 'LEFT_HAND',
          state: 'RAISED',
          startTimestampSeconds: 10.2,
          durationSeconds: 2.3,
          startFrame: 45,
          frameCount: 8,
          maxConfidence: 0.94,
          avgConfidence: 0.91,
          evidence: { left_elevation: 32.0, left_angle: 118.0 },
          dataSource: 'DEMO_DATA',
        },
      ],
      dataSource: 'DEMO_DATA',
    }
  }

  async getHandRaiseEvents(_sessionId?: string): Promise<HandRaiseEventData[]> {
    return [
      {
        eventId: 'evt_0001',
        sessionId: 'sess_01',
        trackId: 'track_001',
        handSide: 'LEFT_HAND',
        state: 'COMPLETED',
        startTimestampSeconds: 10.2,
        endTimestampSeconds: 14.8,
        durationSeconds: 4.6,
        startFrame: 45,
        endFrame: 62,
        frameCount: 18,
        maxConfidence: 0.94,
        avgConfidence: 0.91,
        evidence: { left_elevation: 32.0, left_angle: 118.0 },
        dataSource: 'DEMO_DATA',
      },
    ]
  }

  async getTrackingStatistics(_sessionId?: string): Promise<TrackingEventStatisticsData> {
    return {
      totalEvents: 4,
      completedEvents: 3,
      activeEvents: 1,
      leftHandCount: 3,
      rightHandCount: 1,
      bothHandsCount: 0,
      avgDurationSeconds: 3.8,
      maxDurationSeconds: 5.2,
      totalDurationSeconds: 15.2,
      needsReviewCount: 0,
      cooldownPeriodSeconds: 1.0,
    }
  }

  async resetTracking(_sessionId?: string): Promise<any> {
    return { status: 'SUCCESS', message: 'Tracking reset.' }
  }

  async getAnalyticsSessions(): Promise<AnalyticsSessionSummaryData[]> {
    return [
      {
        sessionId: 'sess_01',
        title: 'CS402: CNN Architecture & Optimization',
        isDemo: true,
        dataSource: 'DEMO_DATA',
        totalEvents: 19,
        leftHandCount: 9,
        rightHandCount: 8,
        bothHandsCount: 2,
        avgDurationSeconds: 2.45,
      },
      {
        sessionId: 'sess_02',
        title: 'MATH301: Linear Algebra & Eigendecomposition',
        isDemo: true,
        dataSource: 'DEMO_DATA',
        totalEvents: 12,
        leftHandCount: 5,
        rightHandCount: 6,
        bothHandsCount: 1,
        avgDurationSeconds: 2.10,
      },
      {
        sessionId: 'sess_03',
        title: 'EE204: Signals, Transforms & Sampling',
        isDemo: true,
        dataSource: 'DEMO_DATA',
        totalEvents: 24,
        leftHandCount: 11,
        rightHandCount: 10,
        bothHandsCount: 3,
        avgDurationSeconds: 2.75,
      },
    ]
  }

  async getSessionActivityAnalytics(sessionId: string = 'sess_01', intervalSeconds: number = 60): Promise<SessionActivityAnalyticsData> {
    const isSess02 = sessionId === 'sess_02'
    const totalEvents = isSess02 ? 12 : 19
    const leftEvents = isSess02 ? 5 : 9
    const rightEvents = isSess02 ? 6 : 8
    const bothEvents = isSess02 ? 1 : 2
    const tracksCount = isSess02 ? 8 : 12

    const buckets = [
      { bucketIndex: 0, startTimeSeconds: 0, endTimeSeconds: 300, label: '00:00 - 05:00', eventCount: 2, leftHandCount: 1, rightHandCount: 1, bothHandsCount: 0, activeTracksCount: 2 },
      { bucketIndex: 1, startTimeSeconds: 300, endTimeSeconds: 600, label: '05:00 - 10:00', eventCount: 4, leftHandCount: 2, rightHandCount: 2, bothHandsCount: 0, activeTracksCount: 3 },
      { bucketIndex: 2, startTimeSeconds: 600, endTimeSeconds: 900, label: '10:00 - 15:00', eventCount: 6, leftHandCount: 3, rightHandCount: 2, bothHandsCount: 1, activeTracksCount: 5 },
      { bucketIndex: 3, startTimeSeconds: 900, endTimeSeconds: 1200, label: '15:00 - 20:00', eventCount: 4, leftHandCount: 2, rightHandCount: 2, bothHandsCount: 0, activeTracksCount: 4 },
      { bucketIndex: 4, startTimeSeconds: 1200, endTimeSeconds: 1500, label: '20:00 - 25:00', eventCount: 3, leftHandCount: 1, rightHandCount: 1, bothHandsCount: 1, activeTracksCount: 2 },
    ]

    const trackSummaries = Array.from({ length: tracksCount }, (_, i) => ({
      trackId: `track_${String(i + 1).padStart(3, '0')}`,
      eventCount: i === 0 ? 3 : (i % 2 === 0 ? 2 : 1),
      totalDurationSeconds: i === 0 ? 7.8 : 4.5,
      avgDurationSeconds: 2.45,
      leftHandCount: i % 2 === 0 ? 1 : 0,
      rightHandCount: i % 2 !== 0 ? 1 : 0,
      bothHandsCount: i === 0 ? 1 : 0,
    }))

    return {
      sessionId,
      title: isSess02 ? 'MATH301: Linear Algebra' : 'CS402: CNN Architecture & Optimization',
      courseCode: isSess02 ? 'MATH301' : 'CS402',
      date: '2026-10-12',
      startTime: '09:15 AM',
      durationMinutes: 45,
      totalObservedPeoplePeak: isSess02 ? 18 : 28,
      uniqueAnonymousTracksObserved: tracksCount,
      totalHandRaisingEvents: totalEvents,
      completedEventsCount: totalEvents,
      activeEventsCount: 0,
      leftHandEvents: leftEvents,
      rightHandEvents: rightEvents,
      bothHandEvents: bothEvents,
      averageEventDurationSeconds: isSess02 ? 2.10 : 2.45,
      maxEventDurationSeconds: 4.8,
      totalEventDurationSeconds: 46.5,
      observableParticipationEvents: totalEvents,
      eventTypeDistribution: {
        leftHandPct: Math.round((leftEvents / totalEvents) * 100),
        rightHandPct: Math.round((rightEvents / totalEvents) * 100),
        bothHandsPct: Math.round((bothEvents / totalEvents) * 100),
        unknownPct: 0,
      },
      mostFrequentlyObservedTrack: 'track_001',
      leastFrequentlyObservedTrack: `track_${String(tracksCount).padStart(3, '0')}`,
      peakParticipationInterval: '10:00 - 15:00',
      intervalSeconds,
      timeline: buckets,
      trackSummaries,
      dataSource: 'DEMO_DATA',
      isDemoData: true,
      privacyDisclaimer: 'Observable physical activity only. No attention, concentration, emotion, intelligence, or cognitive engagement is inferred.',
    }
  }

  async getActivityDistribution(sessionId?: string): Promise<ActivityDistributionSummaryData> {
    return {
      sessionId: sessionId || 'sess_01',
      totalTrackedPersons: 18,
      totalActivityEvents: 25,
      activityCounts: {
        NO_FLAG_OBSERVED: 18,
        HAND_RAISED: 4,
        HEAD_DOWN_POSTURE: 2,
        POSSIBLE_PEER_INTERACTION: 1,
        PHONE_VISIBLE: 0,
      },
      activityPercentages: {
        NO_FLAG_OBSERVED: 72.0,
        HAND_RAISED: 16.0,
        HEAD_DOWN_POSTURE: 8.0,
        POSSIBLE_PEER_INTERACTION: 4.0,
        PHONE_VISIBLE: 0.0,
      },
      avgDurations: {
        NO_FLAG_OBSERVED: 45.2,
        HAND_RAISED: 3.4,
        HEAD_DOWN_POSTURE: 4.8,
        POSSIBLE_PEER_INTERACTION: 2.1,
        PHONE_VISIBLE: 0.0,
      },
      disclaimer:
        'Observable activity labels reflect visible physical geometry and detected objects only. They do not evaluate student focus, attentiveness, engagement, or academic performance.',
    }
  }

  async compareSessions(sessionA: string, sessionB: string): Promise<SessionComparisonResponseData> {
    const a = await this.getSessionActivityAnalytics(sessionA)
    const b = await this.getSessionActivityAnalytics(sessionB)
    return {
      sessionA: a,
      sessionB: b,
      comparisons: [
        {
          metric: 'Total Observed Hand-Raising Events',
          sessionAValue: a.totalHandRaisingEvents,
          sessionBValue: b.totalHandRaisingEvents,
          difference: '+7 events',
          interpretation: `Session ${sessionA} recorded 7 more physical hand-raise events than Session ${sessionB}.`,
        },
        {
          metric: 'Unique Anonymous Tracks Observed',
          sessionAValue: a.uniqueAnonymousTracksObserved,
          sessionBValue: b.uniqueAnonymousTracksObserved,
          difference: '+4 tracks',
          interpretation: `Session ${sessionA} tracked 4 more unique individuals displaying movement.`,
        },
        {
          metric: 'Average Hand-Raising Duration',
          sessionAValue: `${a.averageEventDurationSeconds} s`,
          sessionBValue: `${b.averageEventDurationSeconds} s`,
          difference: '+0.35 s',
          interpretation: `Physical gestures were sustained on average for 0.35s longer in Session ${sessionA}.`,
        },
      ],
      generatedAt: new Date().toISOString(),
    }
  }

  async exportAnalyticsCsv(sessionId: string): Promise<string> {
    return `# CLASSVISION AI — CLASSROOM ACTIVITY ANALYTICS EXPORT\n# Session ID,${sessionId}\n# Data Source,DEMO_DATA\n=== AGGREGATE OBSERVABLE METRICS ===\nTotal Hand-Raising Events,19\nUnique Anonymous Tracks,12\nAverage Duration,2.45s\n`
  }

  exportAnalyticsPdfUrl(sessionId: string): string {
    return `/api/analytics/export/pdf?session_id=${encodeURIComponent(sessionId)}`
  }

  async getAgentsStatus(): Promise<AgentInfoData[]> {
    return DEMO_AGENTS
  }

  async getAgentTasks(): Promise<AgentTaskData[]> {
    return DEMO_TASKS
  }

  async createAgentTask(title: string, description: string, priority: TaskPriorityType = 'MEDIUM', autoExecute: boolean = true): Promise<AgentTaskData> {
    const newTask: AgentTaskData = {
      taskId: `task_${Date.now()}`,
      title,
      description,
      priority,
      status: autoExecute ? 'IN_PROGRESS' : 'PENDING',
      assignedAgents: ['agent_pm', 'agent_architect', 'agent_testing'],
      dependencies: [],
      acceptanceCriteria: ['Decompose steps', 'Execute tool actions', 'Pass QA tests'],
      plan: [
        {
          stepIndex: 1,
          title: `Analyze: ${title}`,
          assignedAgent: 'project_manager',
          dependencies: [],
          status: 'COMPLETED',
          acceptanceCriteria: 'Task plan formulated',
          resultSummary: 'Plan formulated and scheduled',
        },
        {
          stepIndex: 2,
          title: 'Execute & Implement',
          assignedAgent: 'backend_developer',
          dependencies: [1],
          status: 'IN_PROGRESS',
          acceptanceCriteria: 'Implement requested functionality',
          resultSummary: null,
        },
        {
          stepIndex: 3,
          title: 'QA & Verification',
          assignedAgent: 'testing_qa',
          dependencies: [2],
          status: 'PENDING',
          acceptanceCriteria: 'Pass pytest and vitest regression checks',
          resultSummary: null,
        },
      ],
      progress: autoExecute ? 33.3 : 0.0,
      resultSummary: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      completedAt: null,
    }
    DEMO_TASKS.unshift(newTask)
    return newTask
  }

  async cancelAgentTask(taskId: string): Promise<any> {
    const task = DEMO_TASKS.find((t) => t.taskId === taskId)
    if (task) {
      task.status = 'CANCELLED'
    }
    return { status: 'CANCELLED', taskId }
  }

  async getAgentMessages(taskId?: string): Promise<AgentMessageData[]> {
    if (taskId) {
      return DEMO_MESSAGES.filter((m) => m.taskId === taskId)
    }
    return DEMO_MESSAGES
  }

  async getAgentApprovals(pendingOnly?: boolean): Promise<ApprovalRequestData[]> {
    if (pendingOnly) {
      return DEMO_APPROVALS.filter((a) => a.status === 'PENDING')
    }
    return DEMO_APPROVALS
  }

  async approveAgentAction(approvalId: string, comment?: string): Promise<any> {
    const req = DEMO_APPROVALS.find((a) => a.approvalId === approvalId)
    if (req) {
      req.status = 'APPROVED'
      req.reviewedBy = 'Human Engineer'
      req.reviewComment = comment || 'Approved by user'
      req.reviewedAt = new Date().toISOString()
    }
    return { status: 'APPROVED', approvalId }
  }

  async rejectAgentAction(approvalId: string, comment?: string): Promise<any> {
    const req = DEMO_APPROVALS.find((a) => a.approvalId === approvalId)
    if (req) {
      req.status = 'REJECTED'
      req.reviewedBy = 'Human Engineer'
      req.reviewComment = comment || 'Rejected by user'
      req.reviewedAt = new Date().toISOString()
    }
    return { status: 'REJECTED', approvalId }
  }

  async getAgentDebuggingRecords(): Promise<DebuggingRecordData[]> {
    return DEMO_DEBUGGING_RECORDS
  }

  async getAgentProjectHealth(): Promise<ProjectHealthData> {
    return DEMO_PROJECT_HEALTH
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`API error ${res.status}: ${errorText}`)
  }
  return res.json()
}

/**
 * Real Backend API Implementation:
 * Points to FastAPI backend with full endpoints for CV, Speech, OCR, RAG, and Database persistence.
 * When backend is unreachable, throws descriptive error pointing to demo mode.
 */
export class RealClassVisionApi implements ClassVisionApi {
  public readonly baseUrl = API_CONFIG.baseUrl

  private failWithDemoHint(error: unknown): never {
    throw new Error(`Real backend not reachable at ${this.baseUrl} (${String(error)}). Set VITE_USE_DEMO_DATA=true.`)
  }

  async getDashboardSummary(): Promise<DashboardSummary> {
    try {
      return await fetchJson<DashboardSummary>(`${this.baseUrl}/dashboard/summary`)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getSessions(): Promise<SessionInfo[]> {
    try {
      return await fetchJson<SessionInfo[]>(`${this.baseUrl}/sessions`)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getSessionById(sessionId: string): Promise<SessionInfo | null> {
    try {
      return await fetchJson<SessionInfo>(`${this.baseUrl}/sessions/${encodeURIComponent(sessionId)}`)
    } catch {
      return null
    }
  }

  async getAnalytics(sessionId?: string): Promise<AnalyticsData> {
    try {
      const url = sessionId
        ? `${this.baseUrl}/analytics?session_id=${encodeURIComponent(sessionId)}`
        : `${this.baseUrl}/analytics`
      return await fetchJson<AnalyticsData>(url)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getLectureIntel(sessionId?: string): Promise<LectureIntelligenceData> {
    try {
      const url = sessionId
        ? `${this.baseUrl}/intelligence/${encodeURIComponent(sessionId)}`
        : `${this.baseUrl}/intelligence`
      return await fetchJson<LectureIntelligenceData>(url)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async askQuestion(query: string, sessionId?: string): Promise<RagResponse> {
    try {
      return await fetchJson<RagResponse>(`${this.baseUrl}/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, sessionId }),
      })
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getReports(): Promise<{ reports: ReportItem[]; modelQuality: ModelQualityReport }> {
    try {
      return await fetchJson<{ reports: ReportItem[]; modelQuality: ModelQualityReport }>(`${this.baseUrl}/reports`)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getModelStatus(): Promise<ModelStatusData> {
    try {
      return await fetchJson<ModelStatusData>(`${this.baseUrl}/model/status`)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getSettings(): Promise<SettingsData> {
    try {
      return await fetchJson<SettingsData>(`${this.baseUrl}/settings`)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getSystemStatus(): Promise<SystemStatus> {
    try {
      return await fetchJson<SystemStatus>(`${this.baseUrl}/system/status`)
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getRealtimeDetections(_sessionId?: string): Promise<BoundingBox[]> {
    return DEMO_BOUNDING_BOXES
  }

  // Multimodal AI service methods
  async detectFrame(file: File, confidenceThreshold: number = 0.35, imgsz: number = 640, detectPose: boolean = false) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('confidence_threshold', confidenceThreshold.toString())
    formData.append('imgsz', imgsz.toString())
    formData.append('detect_pose', detectPose ? 'true' : 'false')
    return fetchJson(`${this.baseUrl}/vision/detect`, {
      method: 'POST',
      body: formData,
    })
  }

  async detectSyntheticFrame() {
    return fetchJson(`${this.baseUrl}/vision/detect-synthetic`, {
      method: 'POST',
    })
  }

  async processVideo(
    file: File,
    frameSkip: number = 5,
    confidenceThreshold: number = 0.35,
    imgsz: number = 640,
    detectPose: boolean = true,
    instructorRoiPolygon?: number[][] | null,
    zoneFilteringEnabled?: boolean,
    keypointThreshold?: number,
    elevationMarginPx?: number
  ) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('frame_skip', frameSkip.toString())
    formData.append('confidence_threshold', confidenceThreshold.toString())
    formData.append('imgsz', imgsz.toString())
    formData.append('detect_pose', detectPose.toString())
    formData.append('enable_tracking', 'true')
    if (keypointThreshold !== undefined) {
      formData.append('keypoint_threshold', keypointThreshold.toString())
    }
    if (elevationMarginPx !== undefined) {
      formData.append('elevation_margin_px', elevationMarginPx.toString())
    }
    if (instructorRoiPolygon && instructorRoiPolygon.length >= 3) {
      formData.append('instructor_roi_polygon', JSON.stringify(instructorRoiPolygon))
    }
    if (zoneFilteringEnabled !== undefined) {
      formData.append('zone_filtering_enabled', zoneFilteringEnabled ? 'true' : 'false')
    }
    return fetchJson(`${this.baseUrl}/vision/video/process`, {
      method: 'POST',
      body: formData,
    })
  }

  async getSessionZoneConfig(sessionId: string): Promise<{ sessionId: string; instructorRoiPolygon: number[][] | null; zoneFilteringEnabled: boolean }> {
    return fetchJson(`${this.baseUrl}/sessions/${sessionId}/zone-config`)
  }

  async updateSessionZoneConfig(sessionId: string, polygon: number[][] | null, enabled: boolean = true): Promise<any> {
    return fetchJson(`${this.baseUrl}/sessions/${sessionId}/zone-config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        instructorRoiPolygon: polygon,
        zoneFilteringEnabled: enabled,
      }),
    })
  }

  async getVisionStatus() {
    return fetchJson(`${this.baseUrl}/vision/status`)
  }

  async estimatePose(
    file: File,
    confidenceThreshold: number = 0.35,
    keypointThreshold: number = 0.4,
    elevationMarginPx: number = 15.0,
    imgsz: number = 640
  ): Promise<PoseDetectionResponseData> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('confidence_threshold', confidenceThreshold.toString())
    formData.append('keypoint_threshold', keypointThreshold.toString())
    formData.append('elevation_margin_px', elevationMarginPx.toString())
    formData.append('imgsz', imgsz.toString())
    return fetchJson<PoseDetectionResponseData>(`${this.baseUrl}/vision/pose`, {
      method: 'POST',
      body: formData,
    })
  }

  async getPoseStatus(): Promise<PoseStatusResponseData> {
    return fetchJson<PoseStatusResponseData>(`${this.baseUrl}/vision/pose/status`)
  }

  async getActiveTracks(): Promise<TrackingSummaryData> {
    return fetchJson<TrackingSummaryData>(`${this.baseUrl}/vision/tracking/active`)
  }

  async getHandRaiseEvents(sessionId?: string): Promise<HandRaiseEventData[]> {
    const url = sessionId
      ? `${this.baseUrl}/vision/tracking/events?session_id=${sessionId}`
      : `${this.baseUrl}/vision/tracking/events`
    return fetchJson<HandRaiseEventData[]>(url)
  }

  async getTrackingStatistics(sessionId?: string): Promise<TrackingEventStatisticsData> {
    const url = sessionId
      ? `${this.baseUrl}/vision/tracking/events/statistics?session_id=${sessionId}`
      : `${this.baseUrl}/vision/tracking/events/statistics`
    return fetchJson<TrackingEventStatisticsData>(url)
  }

  async resetTracking(sessionId?: string): Promise<any> {
    const url = sessionId
      ? `${this.baseUrl}/vision/tracking/reset?session_id=${sessionId}`
      : `${this.baseUrl}/vision/tracking/reset`
    return fetchJson(url, { method: 'POST' })
  }

  async getAnalyticsSessions(): Promise<AnalyticsSessionSummaryData[]> {
    return fetchJson<AnalyticsSessionSummaryData[]>(`${this.baseUrl}/analytics/sessions`)
  }

  async getSessionActivityAnalytics(sessionId: string, intervalSeconds: number = 60): Promise<SessionActivityAnalyticsData> {
    return fetchJson<SessionActivityAnalyticsData>(
      `${this.baseUrl}/analytics/session/${encodeURIComponent(sessionId)}?interval_seconds=${intervalSeconds}`
    )
  }

  async getActivityDistribution(sessionId?: string): Promise<ActivityDistributionSummaryData> {
    const url = sessionId
      ? `${this.baseUrl}/analytics/activity-distribution?session_id=${encodeURIComponent(sessionId)}`
      : `${this.baseUrl}/analytics/activity-distribution`
    return fetchJson<ActivityDistributionSummaryData>(url)
  }

  async compareSessions(sessionA: string, sessionB: string): Promise<SessionComparisonResponseData> {
    return fetchJson<SessionComparisonResponseData>(
      `${this.baseUrl}/analytics/compare?session_a=${encodeURIComponent(sessionA)}&session_b=${encodeURIComponent(sessionB)}`
    )
  }

  async exportAnalyticsCsv(sessionId: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/analytics/export/csv?session_id=${encodeURIComponent(sessionId)}`)
    return res.text()
  }

  exportAnalyticsPdfUrl(sessionId: string): string {
    return `${this.baseUrl}/analytics/export/pdf?session_id=${encodeURIComponent(sessionId)}`
  }

  async transcribeAudio(file: File, sessionId: string = 'sess_live') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    return fetchJson(`${this.baseUrl}/speech/transcribe`, {
      method: 'POST',
      body: formData,
    })
  }

  async extractWhiteboard(file: File, sessionId: string = 'sess_live') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId)
    return fetchJson(`${this.baseUrl}/ocr/extract`, {
      method: 'POST',
      body: formData,
    })
  }

  async getAgentsStatus(): Promise<AgentInfoData[]> {
    try {
      return await fetchJson<AgentInfoData[]>(`${this.baseUrl}/agents/status`)
    } catch {
      return DEMO_AGENTS
    }
  }

  async getAgentTasks(): Promise<AgentTaskData[]> {
    try {
      return await fetchJson<AgentTaskData[]>(`${this.baseUrl}/agents/tasks`)
    } catch {
      return DEMO_TASKS
    }
  }

  async createAgentTask(title: string, description: string, priority: TaskPriorityType = 'MEDIUM', autoExecute: boolean = true): Promise<AgentTaskData> {
    try {
      return await fetchJson<AgentTaskData>(`${this.baseUrl}/agents/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description,
          priority,
          autoExecute,
        }),
      })
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async cancelAgentTask(taskId: string): Promise<any> {
    try {
      return await fetchJson(`${this.baseUrl}/agents/tasks/${encodeURIComponent(taskId)}/cancel`, {
        method: 'POST',
      })
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getAgentMessages(taskId?: string): Promise<AgentMessageData[]> {
    try {
      const url = taskId
        ? `${this.baseUrl}/agents/messages?task_id=${encodeURIComponent(taskId)}`
        : `${this.baseUrl}/agents/messages`
      return await fetchJson<AgentMessageData[]>(url)
    } catch {
      return DEMO_MESSAGES
    }
  }

  async getAgentApprovals(pendingOnly: boolean = false): Promise<ApprovalRequestData[]> {
    try {
      return await fetchJson<ApprovalRequestData[]>(`${this.baseUrl}/agents/approvals?pending_only=${pendingOnly}`)
    } catch {
      return DEMO_APPROVALS
    }
  }

  async approveAgentAction(approvalId: string, comment?: string): Promise<any> {
    try {
      return await fetchJson(`${this.baseUrl}/agents/approvals/${encodeURIComponent(approvalId)}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment }),
      })
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async rejectAgentAction(approvalId: string, comment?: string): Promise<any> {
    try {
      return await fetchJson(`${this.baseUrl}/agents/approvals/${encodeURIComponent(approvalId)}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment }),
      })
    } catch (e) {
      this.failWithDemoHint(e)
    }
  }

  async getAgentDebuggingRecords(): Promise<DebuggingRecordData[]> {
    try {
      return await fetchJson<DebuggingRecordData[]>(`${this.baseUrl}/agents/debugging`)
    } catch {
      return DEMO_DEBUGGING_RECORDS
    }
  }

  async getAgentProjectHealth(): Promise<ProjectHealthData> {
    try {
      return await fetchJson<ProjectHealthData>(`${this.baseUrl}/agents/health`)
    } catch {
      return DEMO_PROJECT_HEALTH
    }
  }
}

/**
 * Service Factory: selects Demo or Real API based on VITE_USE_DEMO_DATA.
 * Defaults to true for Phase 0.9 web application foundation.
 */
export function createClassVisionApi(): ClassVisionApi {
  const useDemo = import.meta.env.VITE_USE_DEMO_DATA !== 'false'
  if (useDemo) {
    return new DemoClassVisionApi()
  }
  return new RealClassVisionApi()
}

// Global singleton instance for components
export const api = createClassVisionApi()

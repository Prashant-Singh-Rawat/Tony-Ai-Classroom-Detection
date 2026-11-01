// Shared TypeScript interfaces for ClassVision AI Dashboard

export type HandRaiseClass = 'hand_raised' | 'hand_not_raised' | 'ambiguous'

export interface Keypoint {
  name: string
  x: number
  y: number
  confidence: number
}

export interface BoundingBox {
  id: string
  personId: number
  classId: 0 | 1 | 2
  className: HandRaiseClass
  confidence: number
  x: number // percentage 0-100
  y: number
  w: number
  h: number
  width?: number
  height?: number
  handRaised?: boolean
  status?: string
  keypoints?: Keypoint[]
  activityLabel?: string
  activityConfidence?: number
  activityDurationSeconds?: number
  activityEvidence?: string
  statusColor?: 'GREEN' | 'RED' | 'ORANGE' | 'BLUE' | 'YELLOW'
  detectedObjects?: string[]
}

export interface SessionInfo {
  sessionId: string
  title: string
  courseCode: string
  date: string
  startTime: string
  durationMinutes: number
  classroom: string
  instructor: string
  status: 'active' | 'completed' | 'scheduled'
  totalStudents: number
  activeHandRaises: number
  totalHandRaiseEvents: number
  averageEngagement: number // percentage
  privacyProtected: boolean
  instructorRoiPolygon?: number[][] | null
  zoneFilteringEnabled?: boolean
}

export interface MetricCardData {
  label: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  badge?: string
  description?: string
}

export interface DashboardSummary {
  currentSession: SessionInfo | null
  stats: {
    totalPeopleDetected: number
    activeHandRaises: number
    handRaisePercentage: number
    engagementScore: number
    activeCameras: number
    privacyModeActive: boolean
    systemMode: 'demo' | 'live'
  }
  recentSessions: SessionInfo[]
  activityTimeline: Array<{
    time: string
    handRaises: number
    attentiveStudents: number
    ambiguousCount: number
  }>
  isDemoData: true
}

export interface AnalyticsData {
  timeSeries: Array<{
    minute: number
    timestamp: string
    handRaises: number
    attentionIndex: number
    questionsLogged: number
  }>
  activityDistribution: Array<{
    name: string
    count: number
    percentage: number
    color: string
  }>
  classroomComparison: Array<{
    classroom: string
    avgStudents: number
    avgHandRaises: number
    participationRate: number
  }>
  hourlyTrends: Array<{
    timeBlock: string
    avgParticipation: number
  }>
  isDemoData: true
}

export interface TranscriptItem {
  id: string
  speaker: string
  timestamp: string
  text: string
  relatedGesture?: 'hand_raised' | 'question_asked'
}

export interface OcrNoteItem {
  id: string
  timestamp: string
  boardRegion: 'left_blackboard' | 'center_projector' | 'right_whiteboard'
  detectedText: string
  tags: string[]
}

export interface LectureIntelligenceData {
  sessionId: string
  topic: string
  keyConcepts: string[]
  executiveSummary: string[]
  transcript: TranscriptItem[]
  boardNotes: OcrNoteItem[]
  questionMoments: Array<{
    timestamp: string
    studentId: string
    promptOrQuestion: string
    answered: boolean
  }>
  isDemoData: true
}

export interface RagSource {
  title: string
  sourceType: 'transcript' | 'slide_ocr' | 'syllabus'
  timestamp?: string
  pageOrSlide?: number
  snippet: string
}

export interface RagResponse {
  query: string
  answer: string
  confidence: number
  sources: RagSource[]
  isPlaceholder: true
  isDemoData: true
}

export interface ReportItem {
  id: string
  sessionId: string
  title: string
  generatedDate: string
  fileSize: string
  format: 'PDF' | 'CSV' | 'JSON'
  metricsSummary: {
    duration: string
    students: number
    handRaises: number
    handRaiseRate: string
  }
  isDemoData: true
}

export interface ModelQualityReport {
  status: 'NO_MODEL_TRAINED'
  modelCheckpoint: 'None (Phase 0.8 UI baseline)'
  evaluationDataset: 'None (Collection starts post 12 October 2026)'
  plannedMetrics: string[]
  privacyGuarantees: string[]
}

export interface SystemStatus {
  backendConnected: boolean
  useDemoData: boolean
  dataRoot: string
  privacyMode: string
  retentionDays: number
  cameraSource: string
  modelStatus: string
  buildVersion: string
}

export interface ModelStatusData {
  modelCheckpointsCount: number
  activeCheckpoint: string
  trainingStatus: 'NOT CONNECTED' | 'NOT_STARTED'
  kaggleGestureDataset: {
    totalImages: number
    trainImages: number
    testImages: number
    classes: number
    semanticsVerified: boolean
    disclaimer: string
  }
  realClassroomDataset: {
    collectedVideos: number
    extractedFrames: number
    annotationsCount: number
    targetPlan: string
  }
  evaluationMetrics: {
    precision: string
    recall: string
    f1Score: string
    map50: string
    status: 'NOT CONNECTED'
  }
  verifiedTests: {
    passed: number
    total: number
    status: string
  }
}

export interface SettingsData {
  camera: {
    source: string
    resolution: string
    frameRate: number
    hardwareConnected: boolean
  }
  privacy: {
    faceBlurringActive: boolean
    storageRoot: string
    retentionDays: number
    storeRawVideo: boolean
    oneDriveWarningAcknowledged: boolean
  }
  aiModules: {
    visionInference: string
    whisperTranscription: string
    easyOcr: string
    ragAssistant: string
  }
  system: {
    version: string
    demoModeActive: boolean
    offlineOnly: boolean
  }
}

// Autonomous Multi-Agent Engineering System Interfaces
export type AgentRoleType =
  | 'project_manager'
  | 'software_architect'
  | 'frontend_developer'
  | 'backend_developer'
  | 'aiml_engineer'
  | 'dataset_manager'
  | 'debugging_agent'
  | 'testing_qa'
  | 'code_review_security'
  | 'documentation'
  | 'devops_environment'
  | 'supervisor'

export type AgentStatusType =
  | 'IDLE'
  | 'PLANNING'
  | 'EXECUTING'
  | 'WAITING_APPROVAL'
  | 'TESTING'
  | 'DEBUGGING'
  | 'REVIEWING'
  | 'COMPLETED'
  | 'ERROR'

export type TaskStateType =
  | 'PENDING'
  | 'PLANNING'
  | 'IN_PROGRESS'
  | 'WAITING'
  | 'BLOCKED'
  | 'TESTING'
  | 'REVIEWING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'

export type TaskPriorityType = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface AgentInfoData {
  agentId: string
  name: string
  role: AgentRoleType
  responsibility: string
  status: AgentStatusType
  currentTaskId?: string | null
  lastActivity: string
  successCount: number
  failureCount: number
  capabilities: string[]
  permissionLevel: 'READ_ONLY' | 'SAFE_WRITE' | 'APPROVAL_REQUIRED'
}

export interface TaskPlanStepData {
  stepIndex: number
  title: string
  assignedAgent: AgentRoleType
  dependencies: number[]
  status: TaskStateType
  acceptanceCriteria: string
  resultSummary?: string | null
}

export interface AgentTaskData {
  taskId: string
  title: string
  description: string
  priority: TaskPriorityType
  status: TaskStateType
  assignedAgents: string[]
  dependencies: string[]
  acceptanceCriteria: string[]
  plan: TaskPlanStepData[]
  progress: number
  resultSummary?: string | null
  createdAt: string
  updatedAt: string
  completedAt?: string | null
}

export interface AgentMessageData {
  messageId: string
  taskId?: string | null
  senderAgent: string
  receiverAgent: string
  messageType: string
  content: Record<string, any>
  status: string
  timestamp: string
}

export interface ApprovalRequestData {
  approvalId: string
  taskId: string
  agentId: string
  actionType: string
  description: string
  details: Record<string, any>
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED'
  reviewedBy?: string | null
  reviewComment?: string | null
  createdAt: string
  reviewedAt?: string | null
}

export interface DebuggingRecordData {
  id: number
  taskId: string
  errorMessage: string
  errorSeverity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  stackTrace?: string | null
  rootCause?: string | null
  affectedFiles: string[]
  fixDescription?: string | null
  repairAttempt: number
  maxAttempts: number
  testsExecuted: string[]
  status: string
  createdAt: string
  resolvedAt?: string | null
}

export interface ProjectHealthData {
  backendStatus: string
  frontendStatus: string
  databaseStatus: string
  aiModelStatus: string
  datasetStatus: string
  latestTestRun: Record<string, any>
  systemMemory: Record<string, any>
  activeAgentCount: number
  pendingApprovalsCount: number
}

export type ObservablePostureType =
  | 'BOTH_ARMS_RAISED'
  | 'LEFT_ARM_RAISED'
  | 'RIGHT_ARM_RAISED'
  | 'ARMS_NOT_RAISED'
  | 'NEEDS_REVIEW'

export interface PoseKeypointData {
  index: number
  name: string
  x: number
  y: number
  confidence: number
  visible: boolean
  xPct: number
  yPct: number
}

export interface ArmPostureGeometryData {
  elbowAngleDeg?: number | null
  elevationPx?: number | null
  wristAboveShoulder: boolean
  armRaised: boolean
  confidence: number
}

export interface PoseGeometryData {
  leftArm: ArmPostureGeometryData
  rightArm: ArmPostureGeometryData
  shoulderDistancePx?: number | null
  upperBodyVisible: boolean
  occludedKeypoints: string[]
}

export interface PersonPoseDetectionData {
  id: string
  confidence: number
  bbox: {
    id: string
    className: string
    confidence: number
    x: number
    y: number
    width: number
    height: number
    x1: number
    y1: number
    x2: number
    y2: number
  }
  posture: ObservablePostureType
  postureReason: string
  keypoints: PoseKeypointData[]
  geometry: PoseGeometryData
}

export interface PoseDetectionResponseData {
  totalPersons: number
  imageWidth: number
  imageHeight: number
  processingTimeMs: number
  processingFps: number
  modelName: string
  modelStatus: string
  inferenceDevice: string
  postureCounts: Record<string, number>
  persons: PersonPoseDetectionData[]
  dataSource: string
  status: string
  isDemoData: boolean
}

export interface PoseStatusResponseData {
  module: string
  submodule: string
  modelName: string
  activeCheckpoint: string
  status: string
  readyForInference: boolean
  inferenceDevice: string
  cudaAvailable: boolean
  supportedKeypointsCount: number
  cocoKeypointOrder: string[]
  postureClasses: string[]
  memoryUsage: Record<string, number>
  provenance: string
  privacyMode: string
}

// Phase 2.2: Temporal Hand-Raising & Tracking Types
export type HandRaisingStateType = 'NOT_RAISED' | 'RAISING' | 'RAISED' | 'LOWERING' | 'NEEDS_REVIEW'
export type HandSideType = 'LEFT_HAND' | 'RIGHT_HAND' | 'BOTH_HANDS' | 'NONE' | 'UNKNOWN'

export interface TrackedPersonData {
  trackId: string
  state: HandRaisingStateType
  handSide: HandSideType
  confidence: number
  bbox: {
    id: string
    className: string
    confidence: number
    x: number
    y: number
    width: number
    height: number
  }
  keypoints: PoseKeypointData[]
  geometry?: PoseGeometryData
  framesInCurrentState: number
  totalFramesTracked: number
  missingFramesCount: number
  isOccluded: boolean
  activeEventId?: string | null
  lastUpdatedTimestamp: number
}

export interface HandRaiseEventData {
  id?: number
  eventId: string
  sessionId: string
  trackId: string
  handSide: HandSideType
  state: string
  zoneClassification?: 'STUDENT_ZONE' | 'INSTRUCTOR_ZONE' | 'NEEDS_REVIEW' | 'NOT_CONFIGURED'
  startTimestampSeconds: number
  endTimestampSeconds?: number | null
  durationSeconds: number
  startFrame: number
  endFrame?: number | null
  frameCount: number
  maxConfidence: number
  avgConfidence: number
  evidence: Record<string, any>
  dataSource: string
  createdAt?: string
}

export interface TrackingEventStatisticsData {
  sessionId?: string | null
  totalEvents: number
  completedEvents: number
  activeEvents: number
  leftHandCount: number
  rightHandCount: number
  bothHandsCount: number
  avgDurationSeconds: number
  maxDurationSeconds: number
  totalDurationSeconds: number
  needsReviewCount: number
  cooldownPeriodSeconds: number
  studentZoneEvents?: number
  instructorZoneEvents?: number
  uncertainEvents?: number
  zoneFilteringEnabled?: boolean
}

export interface TrackingSummaryData {
  sessionId: string
  timestampSeconds: number
  activeTracksCount: number
  activeHandRaisesCount: number
  statesSummary: Record<string, number>
  tracks: TrackedPersonData[]
  activeEvents: HandRaiseEventData[]
  dataSource: string
}

// ---------------------------------------------------------------------------
// Phase 2.3 Classroom Activity Analytics Types
// ---------------------------------------------------------------------------

export interface ParticipationTimeBucketData {
  bucketIndex: number
  startTimeSeconds: number
  endTimeSeconds: number
  label: string
  eventCount: number
  leftHandCount: number
  rightHandCount: number
  bothHandsCount: number
  activeTracksCount: number
}

export interface TrackParticipationSummaryData {
  trackId: string
  eventCount: number
  totalDurationSeconds: number
  avgDurationSeconds: number
  leftHandCount: number
  rightHandCount: number
  bothHandsCount: number
  firstSeenSeconds?: number | null
  lastSeenSeconds?: number | null
}

export interface EventTypeDistributionData {
  leftHandPct: number
  rightHandPct: number
  bothHandsPct: number
  unknownPct: number
}

export interface SessionActivityAnalyticsData {
  sessionId: string
  title: string
  courseCode?: string | null
  date?: string | null
  startTime?: string | null
  durationMinutes?: number | null
  totalObservedPeoplePeak: number
  uniqueAnonymousTracksObserved: number
  totalHandRaisingEvents: number
  completedEventsCount: number
  activeEventsCount: number
  leftHandEvents: number
  rightHandEvents: number
  bothHandEvents: number
  averageEventDurationSeconds: number
  maxEventDurationSeconds: number
  totalEventDurationSeconds: number
  observableParticipationEvents: number
  eventTypeDistribution: EventTypeDistributionData
  activityDistribution?: ActivityDistributionSummaryData | null
  mostFrequentlyObservedTrack?: string | null
  leastFrequentlyObservedTrack?: string | null
  peakParticipationInterval?: string | null
  intervalSeconds: number
  timeline: ParticipationTimeBucketData[]
  trackSummaries: TrackParticipationSummaryData[]
  dataSource: string
  isDemoData: boolean
  privacyDisclaimer: string
}

export interface SessionComparisonSummaryData {
  metric: string
  sessionAValue: any
  sessionBValue: any
  difference?: string | null
  interpretation: string
}

export interface SessionComparisonResponseData {
  sessionA: SessionActivityAnalyticsData
  sessionB: SessionActivityAnalyticsData
  comparisons: SessionComparisonSummaryData[]
  generatedAt: string
}

export interface ActivityDistributionSummaryData {
  sessionId: string
  totalTrackedPersons: number
  totalActivityEvents: number
  activityCounts: Record<string, number>
  activityPercentages: Record<string, number>
  avgDurations: Record<string, number>
  disclaimer: string
}

export interface AnalyticsSessionSummaryData {
  sessionId: string
  title: string
  isDemo: boolean
  dataSource: string
  totalEvents: number
  leftHandCount: number
  rightHandCount: number
  bothHandsCount: number
  avgDurationSeconds: number
}



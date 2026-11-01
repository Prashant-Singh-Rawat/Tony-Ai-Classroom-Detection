// frontend/src/data/demo/index.ts
// ALL DEMO VALUES LIVE HERE AND NOWHERE ELSE.
// This data is strictly marked as simulated demonstration data for Phase 0.8.

import type {
  AnalyticsData,
  BoundingBox,
  DashboardSummary,
  LectureIntelligenceData,
  ModelQualityReport,
  RagResponse,
  ReportItem,
  SessionInfo,
  SystemStatus,
} from '../../types'

export const DEMO_SESSIONS: SessionInfo[] = [
  {
    sessionId: 'sess_01',
    title: 'CS402: Convolutional Neural Networks & Optimization',
    courseCode: 'CS402',
    date: '2026-10-12',
    startTime: '09:15 AM',
    durationMinutes: 45,
    classroom: 'Lecture Hall 302',
    instructor: 'Dr. A. Sharma',
    status: 'active',
    totalStudents: 28,
    activeHandRaises: 4,
    totalHandRaiseEvents: 19,
    averageEngagement: 86.4,
    privacyProtected: true,
  },
  {
    sessionId: 'sess_02',
    title: 'MATH301: Linear Algebra & Eigendecompositions',
    courseCode: 'MATH301',
    date: '2026-10-12',
    startTime: '11:00 AM',
    durationMinutes: 50,
    classroom: 'Seminar Room 105',
    instructor: 'Prof. K. Verma',
    status: 'completed',
    totalStudents: 18,
    activeHandRaises: 0,
    totalHandRaiseEvents: 12,
    averageEngagement: 78.2,
    privacyProtected: true,
  },
  {
    sessionId: 'sess_03',
    title: 'EE204: Signals, Transforms & Nyquist Sampling',
    courseCode: 'EE204',
    date: '2026-10-13',
    startTime: '02:00 PM',
    durationMinutes: 55,
    classroom: 'Hall 401',
    instructor: 'Dr. M. Iyer',
    status: 'completed',
    totalStudents: 34,
    activeHandRaises: 0,
    totalHandRaiseEvents: 24,
    averageEngagement: 82.0,
    privacyProtected: true,
  },
]

export const DEMO_BOUNDING_BOXES: BoundingBox[] = [
  {
    id: 'box_01',
    personId: 1,
    classId: 0,
    className: 'hand_raised',
    confidence: 0.94,
    x: 18,
    y: 28,
    w: 14,
    h: 42,
  },
  {
    id: 'box_02',
    personId: 2,
    classId: 0,
    className: 'hand_raised',
    confidence: 0.91,
    x: 42,
    y: 22,
    w: 13,
    h: 46,
  },
  {
    id: 'box_03',
    personId: 3,
    classId: 0,
    className: 'hand_raised',
    confidence: 0.88,
    x: 74,
    y: 35,
    w: 15,
    h: 38,
  },
  {
    id: 'box_04',
    personId: 4,
    classId: 0,
    className: 'hand_raised',
    confidence: 0.85,
    x: 88,
    y: 38,
    w: 11,
    h: 40,
  },
  {
    id: 'box_05',
    personId: 5,
    classId: 1,
    className: 'hand_not_raised',
    confidence: 0.96,
    x: 8,
    y: 32,
    w: 12,
    h: 36,
  },
  {
    id: 'box_06',
    personId: 6,
    classId: 1,
    className: 'hand_not_raised',
    confidence: 0.98,
    x: 32,
    y: 34,
    w: 12,
    h: 35,
  },
  {
    id: 'box_07',
    personId: 7,
    classId: 1,
    className: 'hand_not_raised',
    confidence: 0.95,
    x: 58,
    y: 30,
    w: 13,
    h: 38,
  },
  {
    id: 'box_08',
    personId: 8,
    classId: 2,
    className: 'ambiguous',
    confidence: 0.72,
    x: 24,
    y: 50,
    w: 14,
    h: 34,
  },
  {
    id: 'box_09',
    personId: 9,
    classId: 1,
    className: 'hand_not_raised',
    confidence: 0.93,
    x: 68,
    y: 52,
    w: 14,
    h: 36,
  },
]

export const DEMO_DASHBOARD_SUMMARY: DashboardSummary = {
  currentSession: DEMO_SESSIONS[0],
  stats: {
    totalPeopleDetected: 28,
    activeHandRaises: 4,
    handRaisePercentage: 14.3,
    engagementScore: 86,
    activeCameras: 1,
    privacyModeActive: true,
    systemMode: 'demo',
  },
  recentSessions: DEMO_SESSIONS,
  activityTimeline: [
    { time: '09:15', handRaises: 0, attentiveStudents: 27, ambiguousCount: 1 },
    { time: '09:20', handRaises: 1, attentiveStudents: 26, ambiguousCount: 1 },
    { time: '09:25', handRaises: 2, attentiveStudents: 25, ambiguousCount: 1 },
    { time: '09:30', handRaises: 5, attentiveStudents: 22, ambiguousCount: 1 }, // Prompted question segment
    { time: '09:35', handRaises: 4, attentiveStudents: 23, ambiguousCount: 1 },
    { time: '09:40', handRaises: 2, attentiveStudents: 25, ambiguousCount: 1 },
    { time: '09:45', handRaises: 4, attentiveStudents: 23, ambiguousCount: 1 },
  ],
  isDemoData: true,
}

export const DEMO_ANALYTICS: AnalyticsData = {
  timeSeries: [
    { minute: 5, timestamp: '09:20', handRaises: 1, attentionIndex: 88, questionsLogged: 0 },
    { minute: 10, timestamp: '09:25', handRaises: 2, attentionIndex: 85, questionsLogged: 1 },
    { minute: 15, timestamp: '09:30', handRaises: 6, attentionIndex: 92, questionsLogged: 3 },
    { minute: 20, timestamp: '09:35', handRaises: 4, attentionIndex: 89, questionsLogged: 2 },
    { minute: 25, timestamp: '09:40', handRaises: 2, attentionIndex: 84, questionsLogged: 1 },
    { minute: 30, timestamp: '09:45', handRaises: 5, attentionIndex: 90, questionsLogged: 2 },
    { minute: 35, timestamp: '09:50', handRaises: 1, attentionIndex: 81, questionsLogged: 0 },
    { minute: 40, timestamp: '09:55', handRaises: 3, attentionIndex: 87, questionsLogged: 1 },
  ],
  activityDistribution: [
    { name: 'Listening & Attentive', count: 20, percentage: 71.4, color: '#0F766E' },
    { name: 'Active Hand Raise', count: 4, percentage: 14.3, color: '#8b5cf6' },
    { name: 'Note Taking & Typing', count: 3, percentage: 10.7, color: '#10b981' },
    { name: 'Ambiguous / Occluded', count: 1, percentage: 3.6, color: '#f59e0b' },
  ],
  classroomComparison: [
    { classroom: 'Lecture Hall 302', avgStudents: 28, avgHandRaises: 19, participationRate: 67.8 },
    { classroom: 'Seminar Room 105', avgStudents: 18, avgHandRaises: 12, participationRate: 66.7 },
    { classroom: 'Hall 401', avgStudents: 34, avgHandRaises: 24, participationRate: 70.5 },
  ],
  hourlyTrends: [
    { timeBlock: '09:00 - 10:00 AM', avgParticipation: 86.4 },
    { timeBlock: '11:00 - 12:00 PM', avgParticipation: 78.2 },
    { timeBlock: '02:00 - 03:00 PM', avgParticipation: 82.0 },
  ],
  isDemoData: true,
}

export const DEMO_LECTURE_INTEL: LectureIntelligenceData = {
  sessionId: 'sess_01',
  topic: 'CS402: CNN Architecture & Gradient Optimization',
  keyConcepts: [
    'Convolution Kernels & Spatial Feature Maps',
    'Pooling Layers (Max vs Average)',
    'Vanishing Gradient Problem',
    'Adam & RMSProp Adaptive Learning Rates',
  ],
  executiveSummary: [
    'Lecturer introduced 2D spatial convolution mathematics, contrasting local receptive fields with dense feedforward layers.',
    'Prompted class interaction at 09:30 on vanishing gradients generated 5 concurrent hand-raises from center and rear seating rows.',
    'Whiteboard formulas covered chain rule backpropagation with mathematical derivation of weight update tensors.',
    'Closing segment demonstrated PyTorch convolutional layer parameter calculation (stride, padding, output dimensions).',
  ],
  transcript: [
    {
      id: 'tr_1',
      speaker: 'Instructor (Dr. Sharma)',
      timestamp: '09:16:12',
      text: 'Good morning everyone. Today we move into convolutional layers and why standard multilayer perceptrons fail on high-resolution image inputs.',
    },
    {
      id: 'tr_2',
      speaker: 'Instructor (Dr. Sharma)',
      timestamp: '09:24:45',
      text: 'Notice that parameter sharing drastically shrinks our weight matrix compared to dense connections.',
    },
    {
      id: 'tr_3',
      speaker: 'Student 1 (Front Row)',
      timestamp: '09:30:18',
      text: 'Professor, does dilated convolution preserve the spatial dimensions without downsampling?',
      relatedGesture: 'hand_raised',
    },
    {
      id: 'tr_4',
      speaker: 'Instructor (Dr. Sharma)',
      timestamp: '09:30:45',
      text: 'Precisely! Dilated convolution expands the receptive field exponentially without increasing parameter count.',
    },
  ],
  boardNotes: [
    {
      id: 'ocr_1',
      timestamp: '09:22:10',
      boardRegion: 'center_projector',
      detectedText: 'Out_dim = ((W - K + 2P) / S) + 1',
      tags: ['Formula', 'Conv2D', 'Dimension'],
    },
    {
      id: 'ocr_2',
      timestamp: '09:35:40',
      boardRegion: 'left_blackboard',
      detectedText: 'W_new = W_old - lr * (m_t / sqrt(v_t + eps))',
      tags: ['Adam Optimizer', 'Gradient Descent'],
    },
  ],
  questionMoments: [
    {
      timestamp: '09:30:15',
      studentId: 'Student-Row1-Seat3',
      promptOrQuestion: 'Clarification regarding dilated convolution receptive field',
      answered: true,
    },
    {
      timestamp: '09:44:10',
      studentId: 'Student-Row4-Seat2',
      promptOrQuestion: 'Difference between batch normalization and layer normalization in CNNs',
      answered: true,
    },
  ],
  isDemoData: true,
}

export const DEMO_RAG_RESPONSES: Record<string, RagResponse> = {
  default: {
    query: 'What was covered regarding gradient descent and optimizers?',
    answer:
      'In session sess_01, the instructor compared SGD with Adam optimization. Key points included adaptive learning rate scaling using first and second momentum estimates (m_t and v_t) and how Adam mitigates oscillation across steep ravines in the loss landscape.',
    confidence: 0.92,
    sources: [
      {
        title: 'Lecture Audio Transcript',
        sourceType: 'transcript',
        timestamp: '09:35:10',
        snippet: 'Dr. Sharma: "Adam combines AdaGrad and RMSProp with momentum buffers."',
      },
      {
        title: 'Blackboard OCR Extraction',
        sourceType: 'slide_ocr',
        snippet: 'W_new = W_old - lr * (m_t / sqrt(v_t + eps))',
      },
    ],
    isPlaceholder: true,
    isDemoData: true,
  },
  questions: {
    query: 'Did students ask questions during the dilated convolution topic?',
    answer:
      'Yes, at timestamp 09:30:18, a student in the front row raised a hand to ask whether dilated convolutions preserve spatial resolution without downsampling. The lecturer confirmed this advantage.',
    confidence: 0.95,
    sources: [
      {
        title: 'Gesture Timeline & Transcript Synchrony',
        sourceType: 'transcript',
        timestamp: '09:30:18',
        snippet: 'Student 1: "Professor, does dilated convolution preserve spatial dimensions...?"',
      },
    ],
    isPlaceholder: true,
    isDemoData: true,
  },
}

export const DEMO_REPORTS: ReportItem[] = [
  {
    id: 'rep_01',
    sessionId: 'sess_01',
    title: 'Executive Session Summary — CS402 (12 Oct 2026)',
    generatedDate: '2026-10-12 10:15 AM',
    fileSize: '1.4 MB',
    format: 'PDF',
    metricsSummary: {
      duration: '45 mins',
      students: 28,
      handRaises: 19,
      handRaiseRate: '0.42 / min',
    },
    isDemoData: true,
  },
  {
    id: 'rep_02',
    sessionId: 'sess_01',
    title: 'Frame-by-Frame Detection Event Log — CS402',
    generatedDate: '2026-10-12 10:16 AM',
    fileSize: '420 KB',
    format: 'CSV',
    metricsSummary: {
      duration: '45 mins',
      students: 28,
      handRaises: 19,
      handRaiseRate: '19 events logged',
    },
    isDemoData: true,
  },
]

export const DEMO_MODEL_QUALITY_REPORT: ModelQualityReport = {
  status: 'NO_MODEL_TRAINED',
  modelCheckpoint: 'None (Phase 0.8 UI baseline)',
  evaluationDataset: 'None (Collection starts post 12 October 2026)',
  plannedMetrics: [
    'Hand-Raised Precision, Recall & F1-Score',
    'Person-Level Bounding Box mAP@0.5',
    'Distance-Stratified Confusion Matrix (Near, Mid, Far)',
    'Ambiguous Rate & Escalation Stability',
  ],
  privacyGuarantees: [
    'No facial recognition or identity tracking',
    'Local offline execution (Zero Cloud Sync)',
    'Full OneDrive sync isolation via CLASSVISION_REAL_DATA_ROOT',
    'No audio recording or transcription transmission',
  ],
}

export const DEMO_SYSTEM_STATUS: SystemStatus = {
  backendConnected: false, // UI baseline stage
  useDemoData: true,
  dataRoot: 'C:\\ClassVisionData\\real_classroom (Configured via env)',
  privacyMode: 'Strict Offline / Edge Face-Blurring Simulation Active',
  retentionDays: 30,
  cameraSource: 'Simulated Demo Stream (No hardware camera access)',
  modelStatus: 'No model trained — awaiting real classroom dataset',
  buildVersion: '0.8.0-ui-baseline',
}

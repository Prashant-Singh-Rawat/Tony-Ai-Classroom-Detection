// frontend/src/pages/MonitoringPage.tsx
import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  Shield,
  Sliders,
  Play,
  Upload,
  AlertTriangle,
  Cpu,
  Clock,
  Video,
  CheckCircle2,
  Camera,
  CameraOff,
  Radio,
  WifiOff,
  Hand,
  Activity,
  Timer,
  UserCheck,
  RefreshCw,
  Eye,
  ChevronDown,
  Settings,
  Filter,
  Tag,
} from 'lucide-react'
import { api } from '../services'
import type {
  BoundingBox,
  Keypoint,
  PoseDetectionResponseData,
  TrackedPersonData,
  HandRaiseEventData,
  TrackingEventStatisticsData,
} from '../types'
import { DataStatusBadge } from '../components/DataStatusBadge'

interface PersonDetectionBox {
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

interface ImageDetectionResult {
  totalPersons: number
  totalStudents?: number
  activeHandRaises?: number
  imageWidth: number
  imageHeight: number
  processingTimeMs: number
  processingFps: number
  modelName: string
  inferenceDevice: string
  dataSource: string
  detections: PersonDetectionBox[]
  boxes: BoundingBox[]
}

interface VideoFrameSummary {
  frameIndex: number
  timestampSeconds: number
  personCount: number
  detections?: PersonDetectionBox[]
  boxes?: BoundingBox[]
  handRaisedCount?: number
  needsReviewCount?: number
  decodingTimeMs?: number
  inferenceTimeMs?: number
}

interface VideoProcessResult {
  videoFilename: string
  totalFrames: number
  processedFrames: number
  frameSkip: number
  videoFps: number
  durationSeconds: number
  maxPersonsInFrame: number
  avgPersonsPerFrame: number
  totalProcessingTimeSeconds: number
  processingFps: number
  modelName: string
  inferenceDevice: string
  dataSource: string
  status: string
  timeline?: VideoFrameSummary[]
  width?: number
  height?: number
  aspectRatio?: string
  orientation?: string
  decodingFps?: number
  inferenceFps?: number
  totalHandRaises?: number
  totalNeedsReview?: number
  corruptedFramesCount?: number
  peakRamMb?: number
  peakVramMb?: number
  trackedPersonsCount?: number
  handRaiseEventsCount?: number
  instructorRoiPolygon?: number[][] | null
  zoneFilteringEnabled?: boolean
  studentZoneEventsCount?: number
  instructorZoneEventsCount?: number
  uncertainZoneEventsCount?: number
}

function isVideoFile(f: File | null): boolean {
  if (!f) return false
  if (f.type && f.type.startsWith('video/')) return true
  const name = f.name.toLowerCase()
  return name.endsWith('.mp4') || name.endsWith('.avi') || name.endsWith('.webm') || name.endsWith('.mov') || name.endsWith('.mkv')
}

function isImageFile(f: File | null): boolean {
  if (!f) return false
  if (f.type && f.type.startsWith('image/')) return true
  const name = f.name.toLowerCase()
  return name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png') || name.endsWith('.webp') || name.endsWith('.bmp')
}

type ActivityCategory =
  | 'facing_board'
  | 'hand_raised'
  | 'phone_visible'
  | 'head_down'
  | 'turned_sideways'
  | 'needs_review'

interface ActivityBoxConfig {
  category: ActivityCategory
  colorName: 'GREEN' | 'BLUE' | 'RED' | 'ORANGE' | 'YELLOW' | 'GREY'
  border: string
  text: string
  badgeBg: string
  label: string
  isHand: boolean
}

function getActivityBoxConfig(det: BoundingBox): ActivityBoxConfig {
  const rawLabel = (det.activityLabel || '').trim()

  // 1. RED: Phone visible (COCO class 67 detected overlapping person)
  if (
    rawLabel === 'Phone visible' ||
    rawLabel === 'PHONE_VISIBLE' ||
    (det.classId as number) === 67 ||
    det.detectedObjects?.includes('cell phone') ||
    rawLabel.toLowerCase().includes('phone')
  ) {
    return {
      category: 'phone_visible',
      colorName: 'RED',
      border: 'border-red-500 border-2 md:border-[2.5px] bg-red-500/15 shadow-red-500/30',
      text: 'text-red-400 font-extrabold',
      badgeBg: 'border-red-500/80 bg-slate-950/90 text-red-300 backdrop-blur-sm',
      label: 'Phone visible',
      isHand: false,
    }
  }

  // 2. BLUE: Hand raised (Left / Right / Both)
  if (
    rawLabel.startsWith('Hand raised') ||
    rawLabel.includes('HAND_RAISED') ||
    det.handRaised
  ) {
    let display = 'Hand raised'
    if (rawLabel === 'Hand raised (Left)' || rawLabel === 'LEFT_HAND_RAISED') {
      display = 'Hand raised (Left)'
    } else if (rawLabel === 'Hand raised (Right)' || rawLabel === 'RIGHT_HAND_RAISED') {
      display = 'Hand raised (Right)'
    } else if (rawLabel === 'Hand raised (Both)' || rawLabel === 'BOTH_HANDS_RAISED') {
      display = 'Hand raised (Both)'
    } else if (rawLabel.startsWith('Hand raised (')) {
      display = rawLabel
    }

    return {
      category: 'hand_raised',
      colorName: 'BLUE',
      border: 'border-blue-500 border-2 md:border-[2.5px] bg-blue-500/15 shadow-blue-500/30',
      text: 'text-blue-400 font-extrabold',
      badgeBg: 'border-blue-500/80 bg-slate-950/90 text-blue-300 backdrop-blur-sm',
      label: display,
      isHand: true,
    }
  }

  // 3. YELLOW: Head down (Reading / Writing)
  if (
    rawLabel.startsWith('Head down') ||
    rawLabel === 'HEAD_DOWN_POSTURE' ||
    rawLabel.toLowerCase().includes('head down')
  ) {
    let display = 'Head down'
    if (rawLabel.includes('(') && rawLabel.includes(')')) {
      display = rawLabel
    } else if (det.activityDurationSeconds !== undefined && det.activityDurationSeconds > 0) {
      display = `Head down (${Math.round(det.activityDurationSeconds)}s)`
    }
    return {
      category: 'head_down',
      colorName: 'YELLOW',
      border: 'border-yellow-400 border-2 md:border-[2.5px] bg-yellow-400/15 shadow-yellow-400/30',
      text: 'text-yellow-300 font-bold',
      badgeBg: 'border-yellow-400/80 bg-slate-950/90 text-yellow-300 backdrop-blur-sm',
      label: display,
      isHand: false,
    }
  }

  // 4. ORANGE: Turned sideways (Peer interaction)
  if (
    rawLabel === 'Turned sideways (possible interaction)' ||
    rawLabel === 'TURNED_SIDEWAYS' ||
    rawLabel === 'POSSIBLE_PEER_INTERACTION' ||
    rawLabel === 'POSSIBLE_SPEAKING' ||
    rawLabel.toLowerCase().includes('turned sideways')
  ) {
    return {
      category: 'turned_sideways',
      colorName: 'ORANGE',
      border: 'border-orange-500 border-2 md:border-[2.5px] bg-orange-500/15 shadow-orange-500/30',
      text: 'text-orange-400 font-bold',
      badgeBg: 'border-orange-500/80 bg-slate-950/90 text-orange-300 backdrop-blur-sm',
      label: 'Turned sideways',
      isHand: false,
    }
  }

  // 5. GREY: Needs review (Ambiguous or low confidence)
  if (
    rawLabel === 'Needs review' ||
    rawLabel === 'NEEDS_REVIEW' ||
    det.status === 'NEEDS_REVIEW' ||
    det.classId === 2
  ) {
    return {
      category: 'needs_review',
      colorName: 'GREY',
      border: 'border-slate-400 border-2 md:border-[2.5px] bg-slate-400/15 shadow-slate-400/20',
      text: 'text-slate-300 font-bold',
      badgeBg: 'border-slate-400/80 bg-slate-950/90 text-slate-300 backdrop-blur-sm',
      label: 'Needs review',
      isHand: false,
    }
  }

  // 6. GREEN: Facing board (Default forward-facing posture)
  return {
    category: 'facing_board',
    colorName: 'GREEN',
    border: 'border-emerald-500 border-2 md:border-[2.5px] bg-emerald-500/15 shadow-emerald-500/20',
    text: 'text-emerald-400 font-semibold',
    badgeBg: 'border-emerald-500/80 bg-slate-950/90 text-emerald-300 backdrop-blur-sm',
    label: 'Facing board',
    isHand: false,
  }
}

export const MonitoringPage: React.FC = () => {
  const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true'

  // Mode selection
  const [activeTab, setActiveTab] = useState<'real_yolo' | 'simulated_viewport'>('real_yolo')

  // Real Detection State
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [inferenceMode, setInferenceMode] = useState<'person_detection' | 'pose_estimation'>('pose_estimation')
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.35)
  const [keypointThreshold, setKeypointThreshold] = useState<number>(0.4)
  const [elevationMarginPx, setElevationMarginPx] = useState<number>(15.0)
  const [detectPose, setDetectPose] = useState<boolean>(true)
  const [frameSkip, setFrameSkip] = useState<number>(5)
  const [detectionResult, setDetectionResult] = useState<ImageDetectionResult | null>(null)
  const [poseResult, setPoseResult] = useState<PoseDetectionResponseData | null>(null)
  const [videoResult, setVideoResult] = useState<VideoProcessResult | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [hardwareStatus, setHardwareStatus] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadedVideoRef = useRef<HTMLVideoElement>(null)
  const [currentVideoTime, setCurrentVideoTime] = useState<number>(0)
  const [videoNativeDims, setVideoNativeDims] = useState<{ width: number; height: number }>({ width: 960, height: 540 })
  const [mediaAspectRatio, setMediaAspectRatio] = useState<number>(16 / 9)

  const handleVideoLoadedMetadata = () => {
    if (uploadedVideoRef.current) {
      const nw = uploadedVideoRef.current.videoWidth || 960
      const nh = uploadedVideoRef.current.videoHeight || 540
      setVideoNativeDims({ width: nw, height: nh })
      if (nw > 0 && nh > 0) {
        setMediaAspectRatio(nw / nh)
      }
    }
  }

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget
    if (img.naturalWidth > 0 && img.naturalHeight > 0) {
      setMediaAspectRatio(img.naturalWidth / img.naturalHeight)
    }
  }

  const handleVideoTimeUpdate = () => {
    if (uploadedVideoRef.current) {
      setCurrentVideoTime(uploadedVideoRef.current.currentTime)
    }
  }

  const activeVideoFrame = useMemo(() => {
    if (!videoResult?.timeline || videoResult.timeline.length === 0) return null
    const t = currentVideoTime
    let closest = videoResult.timeline[0]
    let minDiff = Math.abs(closest.timestampSeconds - t)
    for (let i = 1; i < videoResult.timeline.length; i++) {
      const diff = Math.abs(videoResult.timeline[i].timestampSeconds - t)
      if (diff < minDiff) {
        minDiff = diff
        closest = videoResult.timeline[i]
      }
    }
    // Keep the closest sampled frame active when paused or seeking so boxes remain synchronized
    return closest
  }, [videoResult, currentVideoTime])

  // Teacher Zone Exclusion (Instructor ROI) State
  const [zoneFilteringEnabled, setZoneFilteringEnabled] = useState<boolean>(true)
  const [showZoneOverlay, setShowZoneOverlay] = useState<boolean>(true)
  const [activeZonePreset, setActiveZonePreset] = useState<'left' | 'right' | 'center' | 'full' | 'disabled'>('left')
  const [instructorPolygon, setInstructorPolygon] = useState<number[][] | null>([
    [0.0, 0.0],
    [0.38, 0.0],
    [0.38, 0.85],
    [0.0, 0.85],
  ])
  const [zoneCompareMode, setZoneCompareMode] = useState<'filtered' | 'raw'>('filtered')

  const setZonePreset = (preset: 'left' | 'right' | 'center' | 'full' | 'disabled') => {
    setActiveZonePreset(preset)
    if (preset === 'left') {
      setInstructorPolygon([[0.0, 0.0], [0.38, 0.0], [0.38, 0.85], [0.0, 0.85]])
      setZoneFilteringEnabled(true)
    } else if (preset === 'right') {
      setInstructorPolygon([[0.62, 0.0], [1.0, 0.0], [1.0, 0.85], [0.62, 0.85]])
      setZoneFilteringEnabled(true)
    } else if (preset === 'center') {
      setInstructorPolygon([[0.25, 0.0], [0.75, 0.0], [0.75, 0.70], [0.25, 0.70]])
      setZoneFilteringEnabled(true)
    } else if (preset === 'full') {
      setInstructorPolygon([[0.0, 0.0], [1.0, 0.0], [1.0, 0.40], [0.0, 0.40]])
      setZoneFilteringEnabled(true)
    } else if (preset === 'disabled') {
      setInstructorPolygon(null)
      setZoneFilteringEnabled(false)
    }
  }

  // Webcam & WebSocket Streaming State
  const [isWebcamActive, setIsWebcamActive] = useState(false)
  const [, setVideoMetadataLoaded] = useState(false)
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('connecting')
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const streamingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Simulated Canvas State (Legacy Phase 0.9 compatibility)
  const [demoBoxes, setDemoBoxes] = useState<BoundingBox[]>([])
  const [showBoxes, setShowBoxes] = useState(true)
  const [blurFaces, setBlurFaces] = useState(true)
  const [showKeypoints, setShowKeypoints] = useState(true)
  const [filterClass, setFilterClass] = useState<'all' | 'raised' | 'ambiguous'>('all')

  // Phase 2.2: Temporal Hand-Raising Tracking State
  const [trackedPersons, setTrackedPersons] = useState<TrackedPersonData[]>([])
  const [activeEvents, setActiveEvents] = useState<HandRaiseEventData[]>([])
  const [recentEvents, setRecentEvents] = useState<HandRaiseEventData[]>([])
  const [trackingStats, setTrackingStats] = useState<TrackingEventStatisticsData | null>(null)

  // Phase 2.8: Privacy-Chained Live Webcam Pipeline & SQLite Event Persistence
  const [clientSideBlurActive, setClientSideBlurActive] = useState(true)
  const [serverSideBlurActive, setServerSideBlurActive] = useState(true)
  const [persistedEventsCount, setPersistedEventsCount] = useState(0)
  const [dbPersistenceStatus, setDbPersistenceStatus] = useState<'CONNECTED' | 'SAVED' | 'IDLE' | 'ERROR'>('CONNECTED')
  const [dbErrorMessage, setDbErrorMessage] = useState<string | null>(null)
  const [serverSideBlurApplied, setServerSideBlurApplied] = useState(true)
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<ActivityCategory | null>(null)

  const activeDetections: BoundingBox[] = useMemo(() => {
    if (isWebcamActive) {
      return detectionResult?.boxes || []
    }
    if (isVideoFile(selectedFile)) {
      if (activeVideoFrame?.boxes) return activeVideoFrame.boxes
      if (videoResult?.timeline && videoResult.timeline.length > 0) {
        return videoResult.timeline[0].boxes || []
      }
      return []
    }
    if (detectionResult?.boxes) {
      return detectionResult.boxes
    }
    return []
  }, [isWebcamActive, selectedFile, activeVideoFrame, videoResult, detectionResult])

  const categoryCounts = useMemo(() => {
    const counts: Record<ActivityCategory, number> = {
      facing_board: 0,
      hand_raised: 0,
      phone_visible: 0,
      head_down: 0,
      turned_sideways: 0,
      needs_review: 0,
    }
    activeDetections.forEach((det) => {
      const cfg = getActivityBoxConfig(det)
      counts[cfg.category] = (counts[cfg.category] || 0) + 1
    })
    return counts
  }, [activeDetections])

  const lowConfidenceCount = useMemo(() => {
    return activeDetections.filter(
      (det) => det.confidence >= 0.15 && det.confidence <= 0.30
    ).length
  }, [activeDetections])
  const [clientSideBlurDetected, setClientSideBlurDetected] = useState(false)
  const detectionResultRef = useRef<ImageDetectionResult | null>(null)

  const refreshTrackingData = async () => {
    try {
      const stats = await api.getTrackingStatistics()
      setTrackingStats(stats)
      const evts = await api.getHandRaiseEvents()
      setRecentEvents(evts)
      const active = await api.getActiveTracks()
      setTrackedPersons(active.tracks)
      setActiveEvents(active.activeEvents)
    } catch {
      // ignore
    }
  }

  const handleResetTracking = async () => {
    try {
      await api.resetTracking()
      await refreshTrackingData()
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    detectionResultRef.current = detectionResult
  }, [detectionResult])

  const handleResetWebSocketSession = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'reset',
          sessionId: 'sess_live',
        })
      )
    }
    setTrackedPersons([])
    setActiveEvents([])
  }

  // Initial data load
  useEffect(() => {
    let isMounted = true
    api.getRealtimeDetections().then(setDemoBoxes)
    api.getVisionStatus().then(setHardwareStatus).catch(() => null)
    Promise.all([
      api.getTrackingStatistics(),
      api.getHandRaiseEvents(),
      api.getActiveTracks(),
    ]).then(([stats, evts, active]) => {
      if (isMounted) {
        setTrackingStats(stats)
        setRecentEvents(evts)
        setTrackedPersons(active.tracks)
        setActiveEvents(active.activeEvents)
      }
    }).catch(() => null)

    return () => {
      isMounted = false
    }
  }, [])

  // WebSocket Connection Lifecycle
  useEffect(() => {
    let ws: WebSocket | null = null
    try {
      const isHttps = window.location.protocol === 'https:'
      const wsProtocol = isHttps ? 'wss:' : 'ws:'
      const host = window.location.hostname || 'localhost'
      const port = '8000'
      const wsUrl = `${wsProtocol}//${host}:${port}/api/ws/detections`

      ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setWsStatus('connected')
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'detections' && msg.status === 'REAL_PROCESSING') {
            const boxes: BoundingBox[] = msg.detections || []
            const activeRaises = msg.activeHandRaises ?? boxes.filter((b) => b.handRaised).length

            if (msg.trackedPersons) {
              setTrackedPersons(msg.trackedPersons)
            }
            if (msg.activeEvents) {
              setActiveEvents(msg.activeEvents)
            }

            const currentImgW = msg.imageWidth || videoRef.current?.videoWidth || 640
            const currentImgH = msg.imageHeight || videoRef.current?.videoHeight || 480

            setDetectionResult({
              totalPersons: msg.totalPersons ?? boxes.length,
              totalStudents: msg.totalPersons ?? boxes.length,
              activeHandRaises: activeRaises,
              imageWidth: currentImgW,
              imageHeight: currentImgH,
              processingTimeMs: msg.processingTimeMs ?? 45,
              processingFps: msg.processingFps ?? 22,
              modelName: detectPose ? 'yolov8n-pose' : 'yolov8n',
              inferenceDevice: msg.inferenceDevice || 'cpu',
              dataSource: 'REAL_PROCESSING',
              detections: boxes.map((b) => ({
                id: b.id,
                className: b.handRaised ? 'Hand Raised' : 'person',
                confidence: b.confidence,
                x: (b.x / 100) * currentImgW,
                y: (b.y / 100) * currentImgH,
                width: (b.w / 100) * currentImgW,
                height: (b.h / 100) * currentImgH,
                x1: (b.x / 100) * currentImgW,
                y1: (b.y / 100) * currentImgH,
                x2: ((b.x + b.w) / 100) * currentImgW,
                y2: ((b.y + b.h) / 100) * currentImgH,
              })),
              boxes: boxes,
            })

            if (msg.persistedEventsCount !== undefined) {
              setPersistedEventsCount(msg.persistedEventsCount)
            }
            if (msg.dbPersistenceStatus) {
              setDbPersistenceStatus(msg.dbPersistenceStatus)
            }
            if (msg.dbErrorMessage) {
              setDbErrorMessage(msg.dbErrorMessage)
            } else {
              setDbErrorMessage(null)
            }
            if (msg.serverSideBlurApplied !== undefined) {
              setServerSideBlurApplied(msg.serverSideBlurApplied)
            }
            if (msg.clientSideBlurDetected !== undefined) {
              setClientSideBlurDetected(msg.clientSideBlurDetected)
            }
          }
        } catch {
          // ignore parsing error
        }
      }

      ws.onerror = () => {
        setWsStatus('error')
      }

      ws.onclose = () => {
        setWsStatus('disconnected')
      }
    } catch {
      // ignore init error
    }

    return () => {
      if (ws) {
        ws.close()
        wsRef.current = null
      }
    }
  }, [detectPose])

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setWsStatus('disconnected')
  }

  const reconnectWebSocket = () => {
    disconnectWebSocket()
    setWsStatus('connecting')
    try {
      const isHttps = window.location.protocol === 'https:'
      const wsProtocol = isHttps ? 'wss:' : 'ws:'
      const host = window.location.hostname || 'localhost'
      const port = '8000'
      const wsUrl = `${wsProtocol}//${host}:${port}/api/ws/detections`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => setWsStatus('connected')
      ws.onerror = () => setWsStatus('error')
      ws.onclose = () => setWsStatus('disconnected')
    } catch {
      setWsStatus('error')
    }
  }

  // Helper: Attach MediaStream to Video Element with robust attributes
  const attachStreamToVideo = (video: HTMLVideoElement, stream: MediaStream) => {
    if (video.srcObject !== stream) {
      video.srcObject = stream
    }
    video.muted = true
    video.playsInline = true
    video.setAttribute('playsinline', 'true')
    video.setAttribute('muted', 'true')

    video.onloadedmetadata = () => {
      setVideoMetadataLoaded(true)
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        setMediaAspectRatio(video.videoWidth / video.videoHeight)
      }
    }

    const playPromise = video.play()
    if (playPromise !== undefined) {
      playPromise.catch((playErr: any) => {
        console.warn('Webcam playback auto-play notice:', playErr)
      })
    }
  }

  // Webcam Controls
  const startWebcam = async () => {
    try {
      setErrorMessage(null)

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Webcam API is not supported in this browser environment.')
      }

      // Ensure WebSocket connection is ready
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        reconnectWebSocket()
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280, min: 640 },
          height: { ideal: 720, min: 480 },
          facingMode: 'user',
        },
        audio: false,
      })

      // Hardware disconnect listener (e.g. camera unplugged or permission revoked)
      stream.getVideoTracks().forEach((track) => {
        track.onended = () => {
          setErrorMessage('Webcam stream disconnected or video track stopped.')
          stopWebcam()
        }
      })

      mediaStreamRef.current = stream

      if (videoRef.current) {
        attachStreamToVideo(videoRef.current, stream)
      }

      setIsWebcamActive(true)
      setSelectedFile(null)
      setPreviewUrl(null)
      setVideoResult(null)
      setDetectionResult(null)
    } catch (err: any) {
      console.error('Webcam access error:', err)
      let msg = err.message || 'Camera permission denied or device not found.'
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = 'Webcam permission denied. Please grant camera access in browser permissions.'
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        msg = 'Webcam unavailable. No camera hardware was detected on this device.'
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        msg = 'Webcam is currently occupied by another application or process.'
      } else if (err.name === 'OverconstrainedError') {
        msg = 'Webcam does not support the requested resolution constraints.'
      }
      setErrorMessage(`Webcam access error: ${msg}`)
      setIsWebcamActive(false)
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop())
        mediaStreamRef.current = null
      }
    }
  }

  const stopWebcam = () => {
    // 1. Stop every MediaStream track
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }
    if (videoRef.current && videoRef.current.srcObject) {
      const s = videoRef.current.srcObject as MediaStream
      s.getTracks().forEach((track) => track.stop())
    }

    // 2. Clear video element srcObject and pause
    if (videoRef.current) {
      videoRef.current.srcObject = null
      videoRef.current.pause()
    }
    if (!selectedFile) {
      setMediaAspectRatio(16 / 9)
    }

    // 3. Cancel animation frames and timers
    if (streamingTimerRef.current) {
      clearInterval(streamingTimerRef.current)
      streamingTimerRef.current = null
    }

    // 4. Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setWsStatus('disconnected')
    }

    // 5. Release canvas resources
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height)
      }
      canvasRef.current.width = 0
      canvasRef.current.height = 0
    }

    // 6. Reset UI state
    setIsWebcamActive(false)
    setVideoMetadataLoaded(false)
    setDetectionResult(null)
    setTrackedPersons([])
    setActiveEvents([])
  }

  // Guarantee stream attachment if stream is acquired and video element mounts
  useEffect(() => {
    if (isWebcamActive && mediaStreamRef.current && videoRef.current) {
      attachStreamToVideo(videoRef.current, mediaStreamRef.current)
    }
  }, [isWebcamActive])

  // Component unmount safeguard: guarantee camera hardware release and interval cleanup
  useEffect(() => {
    const videoEl = videoRef.current
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop())
        mediaStreamRef.current = null
      }
      if (videoEl && videoEl.srcObject) {
        const stream = videoEl.srcObject as MediaStream
        stream.getTracks().forEach((track) => track.stop())
        videoEl.srcObject = null
      }
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current)
        streamingTimerRef.current = null
      }
      if (canvasRef.current) {
        canvasRef.current.width = 0
        canvasRef.current.height = 0
      }
    }
  }, [])

  // Periodic frame grabbing from webcam for WebSocket inference
  useEffect(() => {
    if (!isWebcamActive) {
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current)
        streamingTimerRef.current = null
      }
      return
    }

    streamingTimerRef.current = setInterval(() => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (
        !video ||
        !canvas ||
        video.readyState < 2 ||
        video.videoWidth === 0 ||
        video.videoHeight === 0
      ) {
        return
      }

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      let clientBlurApplied = false
      // Phase 2.8: Client-Side Pre-Transmission Privacy Blur
      if (clientSideBlurActive && detectionResultRef.current?.boxes && detectionResultRef.current.boxes.length > 0) {
        detectionResultRef.current.boxes.forEach((box) => {
          const x = (box.x / 100) * canvas.width
          const y = (box.y / 100) * canvas.height
          const w = (box.w / 100) * canvas.width
          const h = (box.h / 100) * canvas.height
          const headHeight = Math.max(12, h * 0.28)

          const rx = Math.max(0, Math.floor(x))
          const ry = Math.max(0, Math.floor(y))
          const rw = Math.min(Math.floor(w), canvas.width - rx)
          const rh = Math.min(Math.floor(headHeight), canvas.height - ry)

          if (rw > 4 && rh > 4) {
            ctx.save()
            ctx.beginPath()
            ctx.rect(rx, ry, rw, rh)
            ctx.clip()
            ctx.filter = 'blur(16px)'
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
            ctx.restore()
            clientBlurApplied = true
          }
        })
      }

      const base64Data = canvas.toDataURL('image/jpeg', 0.6)

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: 'frame',
            frame: base64Data,
            confidenceThreshold,
            detectPose,
            sessionId: 'sess_live',
            clientSideBlur: clientBlurApplied,
            serverSideBlur: serverSideBlurActive,
          })
        )
      }
    }, 200) // ~5 FPS inference streaming

    return () => {
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current)
        streamingTimerRef.current = null
      }
    }
  }, [isWebcamActive, confidenceThreshold, detectPose, clientSideBlurActive, serverSideBlurActive])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      stopWebcam()
      setSelectedFile(file)
      setErrorMessage(null)
      setDetectionResult(null)
      setVideoResult(null)
      setCurrentVideoTime(0)
      setActiveCategoryFilter(null)
      setMediaAspectRatio(16 / 9)

      if (isImageFile(file) || isVideoFile(file)) {
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        if (isVideoFile(file)) {
          setConfidenceThreshold(0.20)
          setDetectPose(true)
        }
      } else {
        setPreviewUrl(null)
      }
    }
  }

  const handleRunInference = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select an image or video file first.')
      return
    }

    // Client-side file size constraint (500 MB)
    if (selectedFile.size > 500 * 1024 * 1024) {
      setErrorMessage(`Selected file is too large (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB). Maximum allowed upload size is 500 MB.`)
      return
    }

    setIsProcessing(true)
    setErrorMessage(null)

    try {
      if (isVideoFile(selectedFile)) {
        const res = await api.processVideo(
          selectedFile,
          frameSkip,
          confidenceThreshold,
          640,
          detectPose,
          zoneFilteringEnabled ? instructorPolygon : null,
          zoneFilteringEnabled
        )
        setVideoResult(res)
        setDetectionResult(null)
        setPoseResult(null)
      } else if (inferenceMode === 'pose_estimation') {
        const poseRes = await api.estimatePose(
          selectedFile,
          confidenceThreshold,
          keypointThreshold,
          elevationMarginPx,
          640
        )
        setPoseResult(poseRes)
        setDetectionResult({
          totalPersons: poseRes.totalPersons,
          imageWidth: poseRes.imageWidth,
          imageHeight: poseRes.imageHeight,
          processingTimeMs: poseRes.processingTimeMs,
          processingFps: poseRes.processingFps,
          modelName: poseRes.modelName,
          inferenceDevice: poseRes.inferenceDevice,
          dataSource: poseRes.dataSource,
          detections: poseRes.persons.map((p) => p.bbox),
          boxes: poseRes.persons.map((p) => ({
            id: p.id,
            personId: parseInt(p.id.replace('anon_', ''), 10) || 1,
            classId: p.posture.includes('RAISED') ? 0 : (p.posture === 'NEEDS_REVIEW' ? 2 : 1),
            className: p.posture as any,
            confidence: p.confidence,
            x: (p.bbox.x / poseRes.imageWidth) * 100,
            y: (p.bbox.y / poseRes.imageHeight) * 100,
            w: (p.bbox.width / poseRes.imageWidth) * 100,
            h: (p.bbox.height / poseRes.imageHeight) * 100,
            width: p.bbox.width,
            height: p.bbox.height,
            handRaised: p.posture.includes('RAISED'),
            status: p.posture,
            keypoints: p.keypoints.map((kp) => ({
              name: kp.name,
              x: kp.x,
              y: kp.y,
              confidence: kp.confidence,
            })),
          })),
        })
        setVideoResult(null)
      } else {
        const res = await api.detectFrame(selectedFile, confidenceThreshold, 640, false)
        setDetectionResult(res)
        setPoseResult(null)
        setVideoResult(null)
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Detection failed. Ensure the FastAPI backend is running.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleRunSyntheticSample = async () => {
    stopWebcam()
    setIsProcessing(true)
    setErrorMessage(null)
    try {
      const res = await api.detectSyntheticFrame()
      setDetectionResult(res)
      setVideoResult(null)
      setPreviewUrl(null)
      setPoseResult(null)
      setMediaAspectRatio(16 / 9)
    } catch (err: any) {
      setErrorMessage(err.message || 'Synthetic detection request failed.')
    } finally {
      setIsProcessing(false)
    }
  }

  // Complete 17 COCO keypoint skeleton connections
  const skeletonPairs: [string, string][] = [
    // Head
    ['nose', 'left_eye'],
    ['nose', 'right_eye'],
    ['left_eye', 'left_ear'],
    ['right_eye', 'right_ear'],
    // Shoulders & Torso
    ['left_shoulder', 'right_shoulder'],
    ['left_shoulder', 'left_hip'],
    ['right_shoulder', 'right_hip'],
    ['left_hip', 'right_hip'],
    // Left Arm
    ['left_shoulder', 'left_elbow'],
    ['left_elbow', 'left_wrist'],
    // Right Arm
    ['right_shoulder', 'right_elbow'],
    ['right_elbow', 'right_wrist'],
    // Left Leg
    ['left_hip', 'left_knee'],
    ['left_knee', 'left_ankle'],
    // Right Leg
    ['right_hip', 'right_knee'],
    ['right_knee', 'right_ankle'],
  ]

  return (
    <div className="space-y-6">
      {/* Hidden offscreen canvas for webcam frame extraction */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Top Header & Tab Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl border border-slate-200 bg-white shadow-2xs">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Video className="h-5 w-5 text-blue-600" />
            <span>ClassVision AI — Live Classroom Studio</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {showDevTools ? 'Real-time YOLOv8n-pose 17-Keypoint Detection & Teacher ROI Tracking (Offline Edge Mode)' : 'Real-time YOLOv8n-pose 17-Keypoint Detection & Classroom Activity Analysis'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* WebSocket status pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-700">
            {wsStatus === 'connected' ? (
              <>
                <Radio className="h-3.5 w-3.5 text-emerald-600 animate-pulse" />
                <span className="text-emerald-700 font-semibold text-[11px]">{showDevTools ? 'WS Live' : 'Stream Connected'}</span>
              </>
            ) : wsStatus === 'connecting' ? (
              <>
                <Activity className="h-3.5 w-3.5 text-amber-600 animate-spin" />
                <span className="text-amber-700 font-semibold text-[11px]">{showDevTools ? 'WS Connecting' : 'Connecting Stream'}</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-slate-500 text-[11px]">{showDevTools ? 'WS Offline' : 'Stream Offline'}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('real_yolo')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                activeTab === 'real_yolo'
                  ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-2xs'
                  : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Live Classroom AI
            </button>
            {showDevTools && (
            <button
              onClick={() => setActiveTab('simulated_viewport')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                activeTab === 'simulated_viewport'
                  ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-2xs'
                  : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Simulated Viewport
            </button>
            )}
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-xs text-rose-600 hover:text-rose-800 font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {dbErrorMessage && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs text-amber-850 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong>SQLite Event Persistence Notice:</strong> {dbErrorMessage} (Live video streaming continues unaffected in volatile RAM).
            </span>
          </div>
          <button
            onClick={() => setDbErrorMessage(null)}
            className="text-xs text-amber-700 hover:text-amber-900 font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {activeTab === 'real_yolo' ? (
        /* REAL INFERENCE STUDIO */
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main Visualizer Area (3 Cols) */}
          <div className="xl:col-span-3 space-y-4">
            <div
              data-testid="video-panel-frame"
              className="relative rounded-2xl border border-slate-300 bg-black overflow-hidden shadow-md mx-auto flex items-center justify-center transition-all duration-300"
              style={{
                aspectRatio: mediaAspectRatio > 0 ? mediaAspectRatio : 16 / 9,
                maxHeight: 'calc(100vh - 280px)',
                width: `min(100%, calc((100vh - 280px) * ${mediaAspectRatio > 0 ? mediaAspectRatio : 16 / 9}))`,
              }}
            >
              {/* 1. Live Webcam Feed (Always in DOM for immediate media stream binding) */}
              <div className={`relative w-full h-full ${isWebcamActive ? '' : 'hidden'}`}>
                <video
                  ref={videoRef}
                  className="w-full h-full object-contain block"
                  autoPlay
                  playsInline
                  muted
                  onLoadedMetadata={(e) => {
                    setVideoMetadataLoaded(true)
                    const v = e.currentTarget
                    if (v.videoWidth > 0 && v.videoHeight > 0) {
                      setMediaAspectRatio(v.videoWidth / v.videoHeight)
                    }
                  }}
                />

                {/* Bounding Box & Skeleton Overlays on Webcam */}
                {isWebcamActive && detectionResult && detectionResult.boxes && (
                  <div className="absolute inset-0 pointer-events-none">
                    {detectionResult.boxes.map((det) => {
                      const cfg = getActivityBoxConfig(det)
                      if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                        return null
                      }
                      const isNearTop = det.y < 8
                      const chipPosClass = isNearTop ? 'top-1 left-1 rounded' : '-top-6 left-0 rounded-t'

                      return (
                        <div
                          key={det.id}
                          className={`absolute rounded transition-all ${cfg.border}`}
                          style={{
                            left: `${det.x}%`,
                            top: `${det.y}%`,
                            width: `${det.w}%`,
                            height: `${det.h}%`,
                          }}
                        >
                          <div className={`absolute ${chipPosClass} flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>
                            {cfg.isHand && <Hand className="h-3 w-3 text-blue-400 fill-current animate-bounce" />}
                            <span>{det.id.toLowerCase().replace('track_', 'anon_')}:</span>
                            <span className={cfg.text}>
                              {cfg.label}
                            </span>
                            <span className="text-slate-300">({(det.confidence * 100).toFixed(0)}%)</span>
                            {det.activityDurationSeconds !== undefined && det.activityDurationSeconds > 0 && (
                              <span className="text-cyan-300 font-semibold font-mono">{det.activityDurationSeconds.toFixed(1)}s</span>
                            )}
                          </div>

                          {blurFaces && (
                            <div
                              className="absolute rounded-xl bg-slate-950/85 backdrop-blur-xl border border-cyan-400/50 shadow-lg shadow-cyan-500/20 flex flex-col items-center justify-center pointer-events-none z-10"
                              style={{
                                top: '2%',
                                left: '12%',
                                width: '76%',
                                height: '36%',
                              }}
                            >
                              <span className="text-[8px] text-cyan-200 font-extrabold tracking-wider uppercase font-mono">
                                PRIVACY BLUR
                              </span>
                              <span className="text-[6px] text-cyan-400/80 font-mono">
                                FACE OBSCURED
                              </span>
                            </div>
                          )}
                        </div>
                      )
                    })}

                    {/* Pose Keypoint & Skeleton Overlay */}
                    {showKeypoints && (
                      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                        {detectionResult.boxes.map((b) => {
                          if (!b.keypoints || b.keypoints.length === 0) return null
                          if (activeCategoryFilter !== null && getActivityBoxConfig(b).category !== activeCategoryFilter) {
                            return null
                          }
                          const imgW = detectionResult.imageWidth || 640
                          const imgH = detectionResult.imageHeight || 480
                          const kpMap: Record<string, { x: number; y: number; confidence: number }> = {}

                          b.keypoints.forEach((kp) => {
                            kpMap[kp.name] = {
                              x: (kp.x / imgW) * 100,
                              y: (kp.y / imgH) * 100,
                              confidence: kp.confidence,
                            }
                          })

                          return (
                            <g key={`skel-${b.id}`}>
                              {/* Skeleton lines */}
                              {skeletonPairs.map(([p1, p2], idx) => {
                                const k1 = kpMap[p1]
                                const k2 = kpMap[p2]
                                if (!k1 || !k2 || k1.confidence < 0.25 || k2.confidence < 0.25) return null
                                const isArm = p1.includes('wrist') || p2.includes('wrist') || p1.includes('elbow') || p2.includes('elbow')
                                return (
                                  <line
                                    key={idx}
                                    x1={`${k1.x}%`}
                                    y1={`${k1.y}%`}
                                    x2={`${k2.x}%`}
                                    y2={`${k2.y}%`}
                                    stroke={b.handRaised && isArm ? '#38bdf8' : '#34d399'}
                                    strokeWidth="2.5"
                                    strokeLinecap="round"
                                    opacity="0.9"
                                  />
                                )
                              })}

                              {/* Keypoint dots */}
                              {b.keypoints.map((kp, kIdx) => {
                                if (kp.confidence < 0.25) return null
                                const kx = (kp.x / imgW) * 100
                                const ky = (kp.y / imgH) * 100
                                const isWrist = kp.name.includes('wrist')
                                return (
                                  <circle
                                    key={kIdx}
                                    cx={`${kx}%`}
                                    cy={`${ky}%`}
                                    r={isWrist ? '2.5' : '1.8'}
                                    fill={isWrist ? (b.handRaised ? '#38bdf8' : '#10b981') : '#818cf8'}
                                    stroke="#0f172a"
                                    strokeWidth="1"
                                  />
                                )
                              })}
                            </g>
                          )
                        })}
                      </svg>
                    )}
                  </div>
                )}
              </div>

              {/* 2. Uploaded Video Display */}
              {!isWebcamActive && previewUrl && isVideoFile(selectedFile) && (
                <div className="relative w-full h-full">
                  <video
                    ref={uploadedVideoRef}
                    src={previewUrl}
                    controls
                    playsInline
                    onTimeUpdate={handleVideoTimeUpdate}
                    onSeeked={handleVideoTimeUpdate}
                    onPause={handleVideoTimeUpdate}
                    onPlay={handleVideoTimeUpdate}
                    onLoadedMetadata={handleVideoLoadedMetadata}
                    className="w-full h-full object-contain block"
                  />

                  {/* Synchronized Person Bounding Boxes & Skeletons Over Uploaded Video */}
                  {activeVideoFrame && activeVideoFrame.boxes && activeVideoFrame.boxes.length > 0 && (
                    <div className="absolute inset-0 pointer-events-none">
                      {activeVideoFrame.boxes.map((det: BoundingBox) => {
                        const cfg = getActivityBoxConfig(det)
                        if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                          return null
                        }
                        const isTeacherZone = det.zoneClassification === 'INSTRUCTOR_ZONE'
                        const isNearTop = det.y < 8
                        const chipPosClass = isNearTop ? 'top-1 left-1 rounded' : '-top-6 left-0 rounded-t'

                        return (
                          <div
                            key={det.id}
                            className={`absolute rounded transition-all ${
                              isTeacherZone ? 'border-amber-500 border-2 md:border-[2.5px] shadow-amber-500/30' : cfg.border
                            }`}
                            style={{
                              left: `${det.x}%`,
                              top: `${det.y}%`,
                              width: `${det.w}%`,
                              height: `${det.h}%`,
                            }}
                          >
                            <div
                              className={`absolute ${chipPosClass} flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider ${
                                isTeacherZone ? 'bg-amber-600/90 border-amber-400' : cfg.badgeBg
                              } border text-white shadow whitespace-nowrap z-20`}
                            >
                              {cfg.isHand && <Hand className="h-3 w-3 text-blue-400 fill-current animate-bounce" />}
                              <span>{det.id.toLowerCase().replace('track_', 'anon_')}:</span>
                              <span className={isTeacherZone ? 'text-amber-200' : cfg.text}>
                                {isTeacherZone ? 'INSTRUCTOR' : cfg.label}
                              </span>
                              <span className="text-slate-300">({(det.confidence * 100).toFixed(0)}%)</span>
                              {det.activityDurationSeconds !== undefined && det.activityDurationSeconds > 0 && (
                                <span className="text-cyan-300 font-semibold font-mono">
                                  {det.activityDurationSeconds.toFixed(1)}s
                                </span>
                              )}
                            </div>

                            {blurFaces && (
                              <div
                                className="absolute rounded-xl bg-slate-950/85 backdrop-blur-xl border border-cyan-400/50 shadow-lg shadow-cyan-500/20 flex flex-col items-center justify-center pointer-events-none z-10"
                                style={{
                                  top: '2%',
                                  left: '12%',
                                  width: '76%',
                                  height: '36%',
                                }}
                              >
                                <span className="text-[8px] text-cyan-200 font-extrabold tracking-wider uppercase font-mono">
                                  PRIVACY BLUR
                                </span>
                                <span className="text-[6px] text-cyan-400/80 font-mono">
                                  FACE OBSCURED
                                </span>
                              </div>
                            )}
                          </div>
                        )
                      })}

                      {/* Synchronized 17-Keypoint Pose Skeletons Over Video */}
                      {showKeypoints && (
                        <svg
                          className="absolute inset-0 w-full h-full pointer-events-none"
                          viewBox="0 0 100 100"
                          preserveAspectRatio="none"
                        >
                          {activeVideoFrame.boxes.map((b: BoundingBox) => {
                            if (!b.keypoints || b.keypoints.length === 0) return null
                            if (activeCategoryFilter !== null && getActivityBoxConfig(b).category !== activeCategoryFilter) {
                              return null
                            }
                            const imgW = videoResult?.width || videoNativeDims.width || 960
                            const imgH = videoResult?.height || videoNativeDims.height || 540
                            const kpMap: Record<string, { x: number; y: number; confidence: number }> = {}

                            b.keypoints.forEach((kp: Keypoint) => {
                              kpMap[kp.name] = {
                                x: (kp.x / imgW) * 100,
                                y: (kp.y / imgH) * 100,
                                confidence: kp.confidence,
                              }
                            })

                            return (
                              <g key={`skel-vid-${b.id}`}>
                                {/* Skeleton lines */}
                                {skeletonPairs.map(([p1, p2], idx) => {
                                  const k1 = kpMap[p1]
                                  const k2 = kpMap[p2]
                                  if (!k1 || !k2 || k1.confidence < 0.20 || k2.confidence < 0.20) return null
                                  const isArm =
                                    p1.includes('wrist') ||
                                    p2.includes('wrist') ||
                                    p1.includes('elbow') ||
                                    p2.includes('elbow')
                                  return (
                                    <line
                                      key={idx}
                                      x1={`${k1.x}%`}
                                      y1={`${k1.y}%`}
                                      x2={`${k2.x}%`}
                                      y2={`${k2.y}%`}
                                      stroke={b.handRaised && isArm ? '#38bdf8' : '#34d399'}
                                      strokeWidth="2.5"
                                      strokeLinecap="round"
                                      opacity="0.9"
                                    />
                                  )
                                })}

                                {/* Keypoint dots */}
                                {b.keypoints.map((kp: Keypoint, kIdx: number) => {
                                  if (kp.confidence < 0.20) return null
                                  const kx = (kp.x / imgW) * 100
                                  const ky = (kp.y / imgH) * 100
                                  const isWrist = kp.name.includes('wrist')
                                  return (
                                    <circle
                                      key={kIdx}
                                      cx={`${kx}%`}
                                      cy={`${ky}%`}
                                      r={isWrist ? '2.5' : '1.8'}
                                      fill={isWrist ? (b.handRaised ? '#38bdf8' : '#10b981') : '#818cf8'}
                                      stroke="#0f172a"
                                      strokeWidth="1"
                                    />
                                  )
                                })}
                              </g>
                            )
                          })}
                        </svg>
                      )}
                    </div>
                  )}

                  {/* Teacher Zone Exclusion Polygon Preview */}
                  {showZoneOverlay && zoneFilteringEnabled && instructorPolygon && (
                    <svg
                      className="absolute inset-0 w-full h-full pointer-events-none rounded-lg"
                      viewBox="0 0 100 100"
                      preserveAspectRatio="none"
                    >
                      <polygon
                        points={instructorPolygon.map(([x, y]) => `${x * 100},${y * 100}`).join(' ')}
                        fill="none"
                        stroke="rgba(148, 163, 184, 0.45)"
                        strokeWidth="0.8"
                        strokeDasharray="3 3"
                      />
                    </svg>
                  )}
                </div>
              )}

              {/* 3. Uploaded Image Display */}
              {!isWebcamActive && previewUrl && !isVideoFile(selectedFile) && (
                <div className="relative w-full h-full">
                  <img
                    src={previewUrl}
                    alt="Uploaded frame"
                    className="w-full h-full object-contain block"
                    onLoad={handleImageLoad}
                  />

                  {/* Bounding Box Overlays */}
                  {detectionResult &&
                    detectionResult.boxes && (
                      <div className="absolute inset-0 pointer-events-none">
                        {detectionResult.boxes.map((det) => {
                          const cfg = getActivityBoxConfig(det)
                          if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                            return null
                          }
                          const isNearTop = det.y < 8
                          const chipPosClass = isNearTop ? 'top-1 left-1 rounded' : '-top-6 left-0 rounded-t'

                          return (
                            <div
                              key={det.id}
                              className={`absolute rounded transition-all ${cfg.border}`}
                              style={{
                                left: `${det.x}%`,
                                top: `${det.y}%`,
                                width: `${det.w}%`,
                                height: `${det.h}%`,
                              }}
                            >
                              <div className={`absolute ${chipPosClass} flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>
                                {cfg.isHand && <Hand className="h-3 w-3 text-blue-400 fill-current animate-bounce" />}
                                <span>{det.id.toLowerCase().replace('track_', 'anon_')}:</span>
                                <span className={cfg.text}>
                                  {cfg.label}
                                </span>
                                <span className="text-slate-300">({(det.confidence * 100).toFixed(0)}%)</span>
                                {det.activityDurationSeconds !== undefined && det.activityDurationSeconds > 0 && (
                                  <span className="text-cyan-300 font-semibold font-mono">{det.activityDurationSeconds.toFixed(1)}s</span>
                                )}
                              </div>

                              {blurFaces && (
                                <div
                                  className="absolute rounded-xl bg-slate-950/85 backdrop-blur-xl border border-cyan-400/50 shadow-lg shadow-cyan-500/20 flex flex-col items-center justify-center pointer-events-none z-10"
                                  style={{
                                    top: '2%',
                                    left: '12%',
                                    width: '76%',
                                    height: '36%',
                                  }}
                                >
                                  <span className="text-[8px] text-cyan-200 font-extrabold tracking-wider uppercase font-mono">
                                    PRIVACY BLUR
                                  </span>
                                  <span className="text-[6px] text-cyan-400/80 font-mono">
                                    FACE OBSCURED
                                  </span>
                                </div>
                              )}
                            </div>
                          )
                        })}

                        {/* Keypoint Overlay for Image */}
                        {showKeypoints && (
                          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                            {detectionResult.boxes.map((b) => {
                              if (!b.keypoints || b.keypoints.length === 0) return null
                              if (activeCategoryFilter !== null && getActivityBoxConfig(b).category !== activeCategoryFilter) {
                                return null
                              }
                              const imgW = detectionResult.imageWidth || 640
                              const imgH = detectionResult.imageHeight || 480
                              const kpMap: Record<string, { x: number; y: number; confidence: number }> = {}

                              b.keypoints.forEach((kp) => {
                                kpMap[kp.name] = {
                                  x: (kp.x / imgW) * 100,
                                  y: (kp.y / imgH) * 100,
                                  confidence: kp.confidence,
                                }
                              })

                              return (
                                <g key={`skel-${b.id}`}>
                                  {skeletonPairs.map(([p1, p2], idx) => {
                                    const k1 = kpMap[p1]
                                    const k2 = kpMap[p2]
                                    if (!k1 || !k2 || k1.confidence < 0.25 || k2.confidence < 0.25) return null
                                    const isArm = p1.includes('wrist') || p2.includes('wrist') || p1.includes('elbow') || p2.includes('elbow')
                                    return (
                                      <line
                                        key={idx}
                                        x1={`${k1.x}%`}
                                        y1={`${k1.y}%`}
                                        x2={`${k2.x}%`}
                                        y2={`${k2.y}%`}
                                        stroke={b.handRaised && isArm ? '#38bdf8' : '#34d399'}
                                        strokeWidth="2.5"
                                        strokeLinecap="round"
                                        opacity="0.9"
                                      />
                                    )
                                  })}

                                  {b.keypoints.map((kp, kIdx) => {
                                    if (kp.confidence < 0.25) return null
                                    const kx = (kp.x / imgW) * 100
                                    const ky = (kp.y / imgH) * 100
                                    const isWrist = kp.name.includes('wrist')
                                    return (
                                      <circle
                                        key={kIdx}
                                        cx={`${kx}%`}
                                        cy={`${ky}%`}
                                        r={isWrist ? '2.5' : '1.8'}
                                        fill={isWrist ? (b.handRaised ? '#38bdf8' : '#10b981') : '#818cf8'}
                                        stroke="#0f172a"
                                        strokeWidth="1"
                                      />
                                    )
                                  })}
                                </g>
                              )
                            })}
                          </svg>
                        )}
                      </div>
                    )}
                </div>
              )}

              {/* 4. Synthetic Result State */}
              {!isWebcamActive && !previewUrl && detectionResult && (
                <div className="w-full h-full flex flex-col items-center justify-center p-8 space-y-4 overflow-y-auto">
                  <div className="inline-flex p-3 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                    <CheckCircle2 className="h-8 w-8" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-white">Multimodal Inference Executed</h4>
                    <p className="text-xs text-slate-400 mt-1">
                      Processed {detectionResult.imageWidth}x{detectionResult.imageHeight} frame &bull; Model:{' '}
                      <strong className="text-cyan-300 font-mono">{detectionResult.modelName}</strong> &bull; Detected{' '}
                      <strong className="text-cyan-300">{detectionResult.totalPersons}</strong> persons
                    </p>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-lg mx-auto text-left">
                    {detectionResult.boxes.map((det) => (
                      <div
                        key={det.id}
                        className={`p-2.5 rounded-xl border text-xs ${
                          det.handRaised
                            ? 'border-blue-500/40 bg-blue-950/20 text-blue-300'
                            : det.status === 'NEEDS_REVIEW'
                            ? 'border-slate-500/40 bg-slate-900/20 text-slate-300'
                            : 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold block">{det.id}</span>
                          {det.handRaised && <Hand className="h-3 w-3 fill-current" />}
                        </div>
                        <span className="text-[11px] text-slate-300 block">
                          Status: <strong>{det.status || 'NORMAL'}</strong>
                        </span>
                        <span className="text-[10px] text-slate-400">
                          Confidence: {(det.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 5. Initial Empty State */}
              {!isWebcamActive && !previewUrl && !detectionResult && !videoResult && (
                <div className="w-full h-full flex flex-col items-center justify-center p-8 space-y-3">
                  <div className="inline-flex p-3 rounded-full bg-slate-800/60 text-slate-400 border border-slate-700/60">
                    <Camera className="h-7 w-7" />
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200">No Active Stream or Media Selected</h4>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto text-center">
                    Start your laptop webcam for real-time WebSocket inference, or upload an image/video file to run YOLOv8n-pose detection.
                  </p>
                </div>
              )}
            </div>

            {/* Video Playback & HUD Synchronization Strip or Run File Inference Hint */}
            {!isWebcamActive && previewUrl && isVideoFile(selectedFile) && (
              videoResult ? (
                <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-mono max-w-xl mx-auto shadow-2xs">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-slate-500">Timeline:</span>
                    <strong className="text-slate-900">
                      {currentVideoTime.toFixed(1)}s / {(videoResult.durationSeconds || 12).toFixed(1)}s
                    </strong>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-500">
                      Visible: <strong className="text-blue-700">{activeVideoFrame ? activeVideoFrame.personCount : 0}</strong>
                    </span>
                    <span className="text-slate-500">
                      Hand-Raises: <strong className="text-emerald-700">{activeVideoFrame ? activeVideoFrame.handRaisedCount : 0}</strong>
                    </span>
                    {activeVideoFrame && (
                      <span className="text-[10px] text-slate-400">
                        Frame #{activeVideoFrame.frameIndex}
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center text-xs text-slate-500 py-1">
                  Classroom video loaded &bull; Click <strong className="text-blue-600">Run File Inference</strong> to execute YOLOv8n-pose sequential analysis
                </div>
              )
            )}

            {/* Bottom HUD Bar (Telemetry Bar) */}
            <div className="relative p-3 bg-slate-900 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs shadow-xs">
              <div className="flex flex-wrap items-center gap-4">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <Cpu className="h-3.5 w-3.5 text-cyan-400" />
                  Device:{' '}
                  <strong className="text-white font-mono uppercase">
                    {hardwareStatus?.inference_device || 'CPU'}
                  </strong>
                </span>
                <span className="flex items-center gap-1.5 text-slate-300">
                  <Clock className="h-3.5 w-3.5 text-violet-400" />
                  Latency:{' '}
                  <strong className="text-white font-mono">
                    {detectionResult ? `${detectionResult.processingTimeMs} ms` : '--'}
                  </strong>
                </span>
                <span className="text-slate-300">
                  FPS:{' '}
                  <strong className="text-emerald-400 font-mono">
                    {detectionResult ? `${detectionResult.processingFps}` : '--'}
                  </strong>
                </span>
                <span className="text-slate-300">
                  Persons:{' '}
                  <strong className="text-cyan-300 font-mono">
                    {detectionResult ? detectionResult.totalPersons : videoResult ? videoResult.maxPersonsInFrame : 0}
                  </strong>
                </span>
                <span className="flex items-center gap-1 text-slate-300">
                  <Hand className="h-3.5 w-3.5 text-emerald-400" />
                  Hand-Raises:{' '}
                  <strong className="text-emerald-400 font-mono">
                    {detectionResult ? detectionResult.activeHandRaises ?? 0 : 0}
                  </strong>
                </span>
              </div>

              <div className="flex items-center gap-2">
                <DataStatusBadge
                  status={
                    detectionResult
                      ? detectionResult.dataSource === 'SYNTHETIC_DATA'
                        ? 'DEMO DATA'
                        : 'REAL'
                      : isWebcamActive
                      ? 'REAL'
                      : 'NOT CONNECTED'
                  }
                  size="sm"
                />
                <span className="text-[11px] text-slate-400 font-mono">
                  {detectPose ? 'YOLOv8n-pose' : 'YOLOv8n'}
                </span>
              </div>
            </div>

            {/* Category Visibility Toggle Filter Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5 mr-1">
                  <Filter className="h-3.5 w-3.5 text-blue-600" />
                  <span>Activity Filter:</span>
                </span>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter(null)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === null
                      ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  All ({activeDetections.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'facing_board' ? null : 'facing_board'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'facing_board'
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs ring-2 ring-emerald-500/20'
                      : 'bg-emerald-50/70 text-emerald-800 border-emerald-200 hover:bg-emerald-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span>Facing board ({categoryCounts.facing_board})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'hand_raised' ? null : 'hand_raised'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'hand_raised'
                      ? 'bg-blue-600 text-white border-blue-600 shadow-xs ring-2 ring-blue-500/20'
                      : 'bg-blue-50/70 text-blue-800 border-blue-200 hover:bg-blue-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-blue-500" />
                  <span>Hand raised ({categoryCounts.hand_raised})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'phone_visible' ? null : 'phone_visible'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'phone_visible'
                      ? 'bg-rose-600 text-white border-rose-600 shadow-xs ring-2 ring-rose-500/20'
                      : 'bg-rose-50/70 text-rose-800 border-rose-200 hover:bg-rose-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-rose-500" />
                  <span>Phone visible ({categoryCounts.phone_visible})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'head_down' ? null : 'head_down'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'head_down'
                      ? 'bg-yellow-500 text-slate-950 border-yellow-500 shadow-xs ring-2 ring-yellow-400/20 font-bold'
                      : 'bg-yellow-50/70 text-yellow-800 border-yellow-300 hover:bg-yellow-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-yellow-400" />
                  <span>Head down ({categoryCounts.head_down})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'turned_sideways' ? null : 'turned_sideways'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'turned_sideways'
                      ? 'bg-orange-600 text-white border-orange-600 shadow-xs ring-2 ring-orange-500/20'
                      : 'bg-orange-50/70 text-orange-800 border-orange-200 hover:bg-orange-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-orange-500" />
                  <span>Turned sideways ({categoryCounts.turned_sideways})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'needs_review' ? null : 'needs_review'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'needs_review'
                      ? 'bg-slate-700 text-white border-slate-700 shadow-xs ring-2 ring-slate-500/20'
                      : 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-slate-400" />
                  <span>Needs review ({categoryCounts.needs_review})</span>
                </button>
              </div>
            </div>

            {/* Viewport Control Toggles */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 bg-white shadow-2xs">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={blurFaces}
                    onChange={(e) => setBlurFaces(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <Shield className="h-3.5 w-3.5 text-blue-600" />
                  <span>Privacy Face-Blur</span>
                </label>

                <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showKeypoints}
                    onChange={(e) => setShowKeypoints(e.target.checked)}
                    className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <Activity className="h-3.5 w-3.5 text-emerald-600" />
                  <span>Show 17-Keypoint Skeletons</span>
                </label>
              </div>

              <span className="text-xs text-slate-500 font-mono">
                Model: <strong className="text-slate-800">{detectPose ? 'yolov8n-pose.pt' : 'yolov8n.pt'}</strong> &bull; Batch: 1 &bull; Local Edge
              </span>
            </div>

            {/* Sequential Classroom Video Processing Metrics & Teacher Zone Breakdown Card */}
            {!isWebcamActive && videoResult && (
              <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="p-2.5 rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
                      <Video className="h-5 w-5" />
                    </span>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">Sequential Classroom Video Processing Complete</h4>
                      <p className="text-xs text-slate-500">
                        File: <strong className="text-slate-800">{videoResult.videoFilename}</strong> &bull; Duration: {videoResult.durationSeconds}s &bull; Format: <strong className="text-blue-700 font-mono">{videoResult.width || '--'}x{videoResult.height || '--'} ({videoResult.aspectRatio || '16:9'} {videoResult.orientation || 'LANDSCAPE'})</strong>
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-left">
                  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold block">Total Frames</span>
                    <span className="text-base font-bold text-slate-900">{videoResult.totalFrames}</span>
                    <span className="text-[10px] text-slate-400 block">Sampled: {videoResult.processedFrames}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold block">Peak Persons</span>
                    <span className="text-base font-bold text-blue-700">{videoResult.maxPersonsInFrame}</span>
                    <span className="text-[10px] text-slate-400 block">Avg: {videoResult.avgPersonsPerFrame} / frame</span>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold block">Hand Raises</span>
                    <span className="text-base font-bold text-emerald-600">{videoResult.totalHandRaises ?? 0}</span>
                    <span className="text-[10px] text-amber-600 block">Review: {videoResult.totalNeedsReview ?? 0}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold block">Inference Throughput</span>
                    <span className="text-base font-bold text-teal-700">{videoResult.inferenceFps || videoResult.processingFps} FPS</span>
                    <span className="text-[10px] text-slate-400 block">Dec FPS: {videoResult.decodingFps || '--'}</span>
                  </div>
                </div>

                {/* Secondary Metrics Bar */}
                <div className="grid grid-cols-3 gap-2 text-left text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <div>
                    <span className="text-slate-500 text-[10px] block font-medium">Temporal Tracks</span>
                    <strong className="text-slate-900 font-mono">{videoResult.trackedPersonsCount ?? videoResult.maxPersonsInFrame} active</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block font-medium">Hand Raise Events</span>
                    <strong className="text-emerald-700 font-mono">{videoResult.handRaiseEventsCount ?? videoResult.totalHandRaises ?? 0} persisted</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block font-medium">Corrupt Frames Skipped</span>
                    <strong className={videoResult.corruptedFramesCount ? 'text-amber-700 font-mono' : 'text-slate-700 font-mono'}>
                      {videoResult.corruptedFramesCount ?? 0}
                    </strong>
                  </div>
                </div>

                {/* Teacher Zone Exclusion Analytics & Comparison Card */}
                <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 space-y-3 text-left">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-200 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px] font-mono border border-amber-300">
                        TEACHER ROI EXCLUSION
                      </span>
                      <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Zone Participation Breakdown
                      </h5>
                    </div>
                    {/* Comparison Toggle */}
                    <div className="flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-200 text-[10px] font-mono">
                      <button
                        type="button"
                        onClick={() => setZoneCompareMode('filtered')}
                        className={`px-2 py-0.5 rounded transition ${
                          zoneCompareMode === 'filtered'
                            ? 'bg-amber-600 text-white font-bold'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        Filtered (Students Only)
                      </button>
                      <button
                        type="button"
                        onClick={() => setZoneCompareMode('raw')}
                        className={`px-2 py-0.5 rounded transition ${
                          zoneCompareMode === 'raw'
                            ? 'bg-slate-700 text-white font-bold'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        Raw (Unfiltered)
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="p-2.5 rounded-lg bg-white border border-slate-200">
                      <span className="text-[10px] text-slate-500 block font-medium">Total Detected</span>
                      <span className="text-base font-bold text-slate-900 font-mono">
                        {videoResult.totalHandRaises ?? 0}
                      </span>
                      <span className="text-[10px] text-slate-400 block">All physical gestures</span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="text-[10px] text-emerald-800 block font-medium">Student-Zone Events</span>
                      <span className="text-base font-bold text-emerald-700 font-mono">
                        {zoneCompareMode === 'filtered'
                          ? (videoResult.studentZoneEventsCount ?? (videoResult.totalHandRaises ? Math.max(0, videoResult.totalHandRaises - (videoResult.instructorZoneEventsCount ?? 0)) : 0))
                          : (videoResult.totalHandRaises ?? 0)}
                      </span>
                      <span className="text-[10px] text-emerald-600 block">
                        {zoneCompareMode === 'filtered' ? 'Included in student totals' : 'Unfiltered raw total'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200">
                      <span className="text-[10px] text-amber-800 block font-medium">Instructor-Zone Events</span>
                      <span className="text-base font-bold text-amber-700 font-mono">
                        {videoResult.instructorZoneEventsCount ?? 0}
                      </span>
                      <span className="text-[10px] text-amber-600 block">
                        {zoneFilteringEnabled ? 'Excluded from student totals' : 'Preserved in database'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-[10px] text-slate-600 block font-medium">Uncertain Events</span>
                      <span className="text-base font-bold text-slate-800 font-mono">
                        {videoResult.uncertainZoneEventsCount ?? videoResult.totalNeedsReview ?? 0}
                      </span>
                      <span className="text-[10px] text-slate-500 block">Marked NEEDS_REVIEW</span>
                    </div>
                  </div>

                  <p className="text-[10px] text-slate-500 italic">
                    Spatial origin only. Polygon containment identifies events within the designated teaching perimeter and does not identify individuals or verify teacher identity.
                  </p>
                </div>
              </div>
            )}
            {poseResult && (
              <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                        YOLOv8n-pose
                      </span>
                      <span className="text-xs font-bold text-slate-900">Observable Human Posture Analysis</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      17 COCO Keypoints &bull; Arm Elevation &bull; Elbow Angles &bull; Strictly Anonymous IDs
                    </p>
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-slate-500">
                      Latency: <strong className="font-mono text-blue-700">{poseResult.processingTimeMs} ms</strong> ({poseResult.processingFps} FPS)
                    </span>
                    <span className="text-slate-500">
                      Device: <strong className="font-mono text-emerald-700 uppercase">{poseResult.inferenceDevice}</strong>
                    </span>
                  </div>
                </div>

                {/* Posture Counts Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-medium">Both Raised</span>
                    <span className="text-lg font-bold text-emerald-700 font-mono">
                      {poseResult.postureCounts['BOTH_ARMS_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-medium">Left Arm Raised</span>
                    <span className="text-lg font-bold text-blue-700 font-mono">
                      {poseResult.postureCounts['LEFT_ARM_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-medium">Right Arm Raised</span>
                    <span className="text-lg font-bold text-teal-700 font-mono">
                      {poseResult.postureCounts['RIGHT_ARM_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-medium">Not Raised</span>
                    <span className="text-lg font-bold text-slate-700 font-mono">
                      {poseResult.postureCounts['ARMS_NOT_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[10px] text-slate-500 block font-medium">Needs Review</span>
                    <span className="text-lg font-bold text-amber-700 font-mono">
                      {poseResult.postureCounts['NEEDS_REVIEW'] || 0}
                    </span>
                  </div>
                </div>

                {/* Person-by-Person Breakdown */}
                <div className="space-y-2.5 pt-2">
                  <span className="text-xs font-semibold text-slate-700 block">
                    Detected Persons ({poseResult.persons.length})
                  </span>
                  <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                    {poseResult.persons.map((person) => {
                      const postureColor =
                        person.posture === 'BOTH_ARMS_RAISED'
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                          : person.posture === 'LEFT_ARM_RAISED' || person.posture === 'RIGHT_ARM_RAISED'
                          ? 'bg-blue-50 text-blue-800 border-blue-300'
                          : person.posture === 'NEEDS_REVIEW'
                          ? 'bg-amber-50 text-amber-800 border-amber-300'
                          : 'bg-slate-100 text-slate-700 border-slate-200'

                      return (
                        <div
                          key={person.id}
                          className="p-3 rounded-xl bg-white border border-slate-200 text-xs space-y-2 shadow-2xs"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-blue-700 font-bold">{person.id}</span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${postureColor}`}>
                                {person.posture.replace(/_/g, ' ')}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                Pose Conf: {(person.confidence * 100).toFixed(0)}%
                              </span>
                            </div>

                            <div className="flex items-center gap-3 text-[11px] text-slate-500">
                              <span>
                                Left Elbow:{' '}
                                <strong className="text-slate-800">
                                  {person.geometry.leftArm.elbowAngleDeg != null ? `${person.geometry.leftArm.elbowAngleDeg}°` : 'N/A'}
                                </strong>
                              </span>
                              <span>
                                Right Elbow:{' '}
                                <strong className="text-slate-800">
                                  {person.geometry.rightArm.elbowAngleDeg != null ? `${person.geometry.rightArm.elbowAngleDeg}°` : 'N/A'}
                                </strong>
                              </span>
                            </div>
                          </div>

                          <p className="text-[11px] text-slate-600">
                            <span className="text-slate-500 font-medium">Observation: </span>
                            {person.postureReason}
                          </p>

                          <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                            <div>
                              <span>Elevation: </span>
                              <span className="text-slate-600">
                                Left: {person.geometry.leftArm.elevationPx != null ? `${person.geometry.leftArm.elevationPx}px` : 'N/A'} |{' '}
                                Right: {person.geometry.rightArm.elevationPx != null ? `${person.geometry.rightArm.elevationPx}px` : 'N/A'}
                              </span>
                            </div>

                            <div>
                              <span>Upper Body: </span>
                              <span className={person.geometry.upperBodyVisible ? 'text-emerald-400' : 'text-amber-400'}>
                                {person.geometry.upperBodyVisible ? 'Fully Visible' : `Occluded (${person.geometry.occludedKeypoints.join(', ')})`}
                              </span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Phase 2.2: Temporal Hand-Raising Tracking & Event Timeline Card */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-2xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
                      TEMPORAL TRACKER
                    </span>
                    <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      <Timer className="h-4 w-4 text-emerald-600" />
                      Temporal Hand-Raising Detection &amp; Anonymous Tracking
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {showDevTools ? 'IoU Trajectory Continuity • Gap Tolerance • Cooldown Protection • SQLite Persistence' : 'Continuous Motion Tracking & Session Analytics'}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={refreshTrackingData}
                    className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs flex items-center gap-1 transition shadow-2xs"
                    title="Refresh Tracking Events"
                  >
                    <RefreshCw className="h-3 w-3 text-blue-600" />
                    <span className="text-[10px] font-semibold">Sync</span>
                  </button>
                  <button
                    onClick={handleResetTracking}
                    className="px-2.5 py-1 rounded-lg border border-slate-300 bg-white hover:bg-rose-50 hover:border-rose-300 text-slate-700 hover:text-rose-700 text-[10px] font-semibold transition shadow-2xs"
                  >
                    Reset Tracks
                  </button>
                </div>
              </div>

              {/* Event Statistics Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-2.5 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Total Events</span>
                  <span className="text-lg font-bold text-emerald-700 font-mono">
                    {trackingStats?.totalEvents ?? recentEvents.length}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Active Raises</span>
                  <span className="text-lg font-bold text-blue-700 font-mono">
                    {activeEvents.length}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Completed</span>
                  <span className="text-lg font-bold text-slate-700 font-mono">
                    {trackingStats?.completedEvents ?? recentEvents.filter((e) => e.state === 'COMPLETED').length}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Avg Duration</span>
                  <span className="text-lg font-bold text-amber-700 font-mono">
                    {trackingStats?.avgDurationSeconds ? `${trackingStats.avgDurationSeconds}s` : '0.0s'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Left / Right / Both</span>
                  <span className="text-xs font-bold text-slate-800 font-mono block mt-1">
                    {trackingStats ? `${trackingStats.leftHandCount} / ${trackingStats.rightHandCount} / ${trackingStats.bothHandsCount}` : '0 / 0 / 0'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Needs Review</span>
                  <span className="text-lg font-bold text-amber-700 font-mono">
                    {trackingStats?.needsReviewCount ?? 0}
                  </span>
                </div>
              </div>

              {/* Active Tracks & Recent Events Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                {/* Active Tracks Panel */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-700 flex items-center gap-1.5 uppercase tracking-wider">
                    <UserCheck className="h-3.5 w-3.5 text-blue-600" />
                    <span>Active Tracked Persons ({trackedPersons.length})</span>
                  </h4>
                  {trackedPersons.length === 0 ? (
                    <div className="p-3.5 rounded-xl border border-dashed border-slate-300 text-center text-xs text-slate-500 bg-slate-50">
                      No active tracks. Start webcam or process a video sequence.
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {trackedPersons.map((tp) => {
                        const isRaised = tp.state === 'RAISED'
                        const isRaising = tp.state === 'RAISING'
                        const isLowering = tp.state === 'LOWERING'
                        const isReview = tp.state === 'NEEDS_REVIEW'

                        const badgeColor = isRaised
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                          : isRaising
                          ? 'bg-blue-50 text-blue-800 border-blue-300'
                          : isLowering
                          ? 'bg-teal-50 text-teal-800 border-teal-300'
                          : isReview
                          ? 'bg-amber-50 text-amber-800 border-amber-300'
                          : 'bg-slate-100 text-slate-700 border-slate-200'

                        return (
                          <div
                            key={tp.trackId}
                            className="p-2.5 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between gap-3 text-xs"
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-bold text-blue-700">{tp.trackId}</span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${badgeColor}`}>
                                {tp.state}
                              </span>
                              {tp.handSide !== 'NONE' && (
                                <span className="text-[10px] font-mono text-slate-500 uppercase">
                                  [{tp.handSide.replace('_HAND', '')}]
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono">
                              Frames: {tp.totalFramesTracked} &bull; Conf: {(tp.confidence * 100).toFixed(0)}%
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>

                {/* Hand-Raising Events Log */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-700 flex items-center gap-1.5 uppercase tracking-wider">
                    <Hand className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Recent Continuous Events ({recentEvents.length})</span>
                  </h4>
                  {recentEvents.length === 0 ? (
                    <div className="p-3.5 rounded-xl border border-dashed border-slate-300 text-center text-xs text-slate-500 bg-slate-50">
                      No hand-raising events recorded yet.
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {recentEvents.slice(0, 5).map((evt) => (
                        <div
                          key={evt.eventId}
                          className="p-2.5 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between gap-2 text-xs"
                        >
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono font-bold text-slate-900 text-[11px]">{evt.eventId}</span>
                              <span className="text-[10px] font-mono text-blue-700">({evt.trackId})</span>
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
                                {evt.handSide.replace('_HAND', '')}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-500">
                              Duration: <strong className="text-emerald-700 font-mono">{evt.durationSeconds}s</strong> ({evt.frameCount} frames)
                            </span>
                          </div>

                          <div className="text-right">
                            <span className="text-[10px] text-slate-400 block">
                              Peak: {(evt.maxConfidence * 100).toFixed(0)}%
                            </span>
                            <span className="text-[9px] text-slate-500 font-mono font-semibold">
                              {evt.state}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Controls & Information (~30% Col) */}
          <div className="space-y-4">
            {/* Live Information Panel */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span>Telemetry</span>
                </h3>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                    {isWebcamActive ? 'WEBCAM' : selectedFile ? 'VIDEO FILE' : 'IDLE'}
                  </span>
                  <button
                    type="button"
                    onClick={handleResetWebSocketSession}
                    className="p-1 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-100"
                    title="Reset session state"
                  >
                    <RefreshCw className="h-3 w-3" />
                  </button>
                </div>
              </div>

              {/* Observable Status Banner */}
              <div className="rounded-lg p-2.5 bg-slate-50 border border-slate-200 text-xs">
                {!isWebcamActive && !selectedFile && !detectionResult && !videoResult ? (
                  <span className="text-slate-500 block">
                    Inference not running — upload video/image or start webcam.
                  </span>
                ) : isProcessing ? (
                  <div className="flex items-center gap-2 text-blue-600 font-medium">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Inference running...</span>
                  </div>
                ) : activeDetections.length === 0 ? (
                  <div className="flex items-center gap-2 text-amber-700 font-medium">
                    <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
                    <span>Waiting for detections...</span>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <div className="text-slate-800 font-medium leading-snug">
                      People detected: <strong>{activeDetections.length}</strong>
                      {categoryCounts.facing_board > 0 && ` | Facing board: ${categoryCounts.facing_board}`}
                      {categoryCounts.hand_raised > 0 && ` | Hand raised: ${categoryCounts.hand_raised}`}
                      {categoryCounts.phone_visible > 0 && ` | Phone visible: ${categoryCounts.phone_visible}`}
                      {categoryCounts.head_down > 0 && ` | Head down: ${categoryCounts.head_down}`}
                      {categoryCounts.turned_sideways > 0 && ` | Turned sideways: ${categoryCounts.turned_sideways}`}
                      {categoryCounts.needs_review > 0 && ` | Needs review: ${categoryCounts.needs_review}`}
                    </div>
                    {lowConfidenceCount > 0 && (
                      <p className="text-[10px] text-slate-500 italic">
                        {lowConfidenceCount} low-confidence detection(s) included (rear-camera mode)
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500 font-medium">Processing State</span>
                  <span className="font-semibold text-slate-800">
                    {isWebcamActive && detectionResult ? 'Inference Running (Live)' : isProcessing ? 'Inference Running...' : videoResult ? 'Inference Completed' : 'Inference not running'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500 font-medium">People Detected</span>
                  <span className="font-bold text-blue-600 font-mono text-sm">
                    {isWebcamActive && detectionResult ? detectionResult.totalPersons : videoResult ? (activeVideoFrame ? activeVideoFrame.personCount : videoResult.maxPersonsInFrame) : '—'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500 font-medium">Hand-Raise Events</span>
                  <span className="font-bold text-emerald-600 font-mono text-sm">
                    {isWebcamActive && detectionResult ? (detectionResult.activeHandRaises ?? 0) : videoResult ? (activeVideoFrame ? activeVideoFrame.handRaisedCount : (videoResult.totalHandRaises ?? 0)) : '—'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500 font-medium">Inference Speed</span>
                  <span className="font-mono text-slate-700">
                    {isWebcamActive && detectionResult ? `${detectionResult.processingFps?.toFixed(1) || '--'} FPS` : videoResult ? `${videoResult.inferenceFps || videoResult.processingFps || '--'} FPS` : '—'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-500 font-medium">Anonymous IDs</span>
                  <span className="font-mono text-[11px] text-slate-600 truncate max-w-[150px]">
                    {isWebcamActive && detectionResult?.boxes?.length ? `${detectionResult.boxes.length} active` : videoResult ? `${videoResult.trackedPersonsCount || 0} tracked` : '—'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-t border-slate-50">
                  <span className="text-slate-500 font-medium">SQLite Persistence</span>
                  <span className="font-mono text-[11px] text-slate-700">
                    {dbPersistenceStatus} ({persistedEventsCount} events)
                  </span>
                </div>
              </div>
            </div>

            {/* Observable Activity Labels Legend Card */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center justify-between border-b border-slate-100 pb-2">
                <div className="flex items-center gap-2">
                  <Tag className="h-3.5 w-3.5 text-blue-600" />
                  <span>Activity Labels Legend</span>
                </div>
                <span className="text-[10px] font-normal text-slate-500">Rear Camera</span>
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex items-start gap-2 p-2 rounded-lg bg-emerald-50/60 border border-emerald-100">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-emerald-900 block text-[11px]">Facing board (Green)</span>
                    <span className="text-[10px] text-emerald-700">Upright posture, body oriented to board</span>
                  </div>
                </div>
                <div className="flex items-start gap-2 p-2 rounded-lg bg-blue-50/60 border border-blue-100">
                  <span className="h-2.5 w-2.5 rounded-full bg-blue-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-blue-900 block text-[11px]">Hand raised (Blue)</span>
                    <span className="text-[10px] text-blue-700">Left / Right / Both elevated above shoulder</span>
                  </div>
                </div>
                <div className="flex items-start gap-2 p-2 rounded-lg bg-rose-50/60 border border-rose-100">
                  <span className="h-2.5 w-2.5 rounded-full bg-rose-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-rose-900 block text-[11px]">Phone visible (Red)</span>
                    <span className="text-[10px] text-rose-700">Device overlapping hand/lap/desk region</span>
                  </div>
                </div>
                <div className="flex items-start gap-2 p-2 rounded-lg bg-amber-50/60 border border-amber-100">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-amber-900 block text-[11px]">Head down (Orange)</span>
                    <span className="text-[10px] text-amber-700">Head compression &gt; 20s (note-taking normal)</span>
                  </div>
                </div>
                <div className="flex items-start gap-2 p-2 rounded-lg bg-amber-50/60 border border-amber-100">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-amber-900 block text-[11px]">Turned sideways (Orange)</span>
                    <span className="text-[10px] text-amber-700">Sustained yaw toward neighbor/peer</span>
                  </div>
                </div>
                <div className="flex items-start gap-2 p-2 rounded-lg bg-yellow-50/70 border border-yellow-200">
                  <span className="h-2.5 w-2.5 rounded-full bg-yellow-400 border border-yellow-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-semibold text-yellow-900 block text-[11px]">Needs review (Yellow)</span>
                    <span className="text-[10px] text-yellow-800">Low confidence or occlusion boundary</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Source Group */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
                <Video className="h-3.5 w-3.5 text-blue-600" />
                <span>Source</span>
              </h3>

              <div>
                {!isWebcamActive ? (
                  <button
                    onClick={startWebcam}
                    className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-700 py-2.5 text-xs font-semibold text-white transition-colors shadow-xs"
                  >
                    <Camera className="h-4 w-4" />
                    <span>Start Webcam</span>
                  </button>
                ) : (
                  <button
                    onClick={stopWebcam}
                    className="w-full flex items-center justify-center gap-2 rounded-lg border border-rose-200 bg-rose-50 hover:bg-rose-100 py-2.5 text-xs font-semibold text-rose-700 transition-colors"
                  >
                    <CameraOff className="h-4 w-4" />
                    <span>Stop Webcam</span>
                  </button>
                )}
              </div>

              <div className="space-y-1.5">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/jpeg,image/png,image/webp,video/mp4,video/avi,video/quicktime"
                  className="hidden"
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border border-dashed border-slate-300 hover:border-blue-500 rounded-lg p-3 text-center cursor-pointer transition-colors bg-slate-50/60"
                >
                  <Upload className="h-4 w-4 text-slate-400 mx-auto mb-1" />
                  <span className="text-xs text-slate-800 font-medium block truncate">
                    {selectedFile ? selectedFile.name : 'Upload Classroom Video'}
                  </span>
                  <span className="text-[10px] text-slate-400">MP4, WEBP, AVI (Max 100MB)</span>
                </div>
              </div>

              {selectedFile && (
                <button
                  onClick={handleRunInference}
                  disabled={isProcessing}
                  className={`w-full flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-semibold transition-all ${
                    isProcessing
                      ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                      : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs'
                  }`}
                >
                  <Play className="h-3.5 w-3.5" />
                  <span>{isProcessing ? 'Processing Video...' : 'Run File Inference'}</span>
                </button>
              )}

              {showDevTools && (
              <button
                type="button"
                onClick={handleRunSyntheticSample}
                disabled={isProcessing}
                className="w-full flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 py-1.5 text-xs font-medium text-slate-700 transition-colors"
              >
                <Cpu className="h-3.5 w-3.5 text-slate-500" />
                <span>Test Sample Frame</span>
              </button>
              )}
            </div>

            {/* Detection Group */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
                <Sliders className="h-3.5 w-3.5 text-blue-600" />
                <span>Detection</span>
              </h3>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-slate-600 block">Model Pipeline</label>
                <div className="grid grid-cols-2 gap-1.5 p-1 bg-slate-100 rounded-lg">
                  <button
                    type="button"
                    onClick={() => {
                      setInferenceMode('person_detection')
                      setDetectPose(false)
                    }}
                    className={`py-1.5 px-2 rounded-md text-xs font-semibold transition text-center ${
                      inferenceMode === 'person_detection'
                        ? 'bg-white text-blue-700 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Person (YOLOv8)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setInferenceMode('pose_estimation')
                      setDetectPose(true)
                    }}
                    className={`py-1.5 px-2 rounded-md text-xs font-semibold transition text-center ${
                      inferenceMode === 'pose_estimation'
                        ? 'bg-white text-blue-700 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Pose (17-COCO)
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-600 font-medium">Confidence:</span>
                  <strong className="text-blue-600 font-mono font-bold">{(confidenceThreshold * 100).toFixed(0)}%</strong>
                </div>
                <input
                  type="range"
                  min={0.10}
                  max={0.50}
                  step={0.01}
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="w-full accent-blue-600 bg-slate-200 h-1.5 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>10%</span>
                  <span className="text-blue-600 font-medium">Default: 20%</span>
                  <span>50%</span>
                </div>
              </div>
            </div>

            {/* Display Group */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
                <Eye className="h-3.5 w-3.5 text-blue-600" />
                <span>Display</span>
              </h3>

              <div className="space-y-2 text-xs">
                <label className="flex items-center justify-between cursor-pointer py-0.5">
                  <span className="text-slate-700 font-medium">Bounding Boxes</span>
                  <input
                    type="checkbox"
                    checked={showBoxes}
                    onChange={(e) => setShowBoxes(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                </label>

                <label className="flex items-center justify-between cursor-pointer py-0.5">
                  <span className="text-slate-700 font-medium">17-Keypoint Skeletons</span>
                  <input
                    type="checkbox"
                    checked={showKeypoints}
                    onChange={(e) => setShowKeypoints(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                </label>

                <label className="flex items-center justify-between cursor-pointer py-0.5">
                  <span className="text-slate-700 font-medium">
                    Client Face Blur {clientSideBlurDetected ? '(Active)' : ''}
                  </span>
                  <input
                    type="checkbox"
                    checked={clientSideBlurActive}
                    onChange={(e) => setClientSideBlurActive(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                </label>

                <label className="flex items-center justify-between cursor-pointer py-0.5">
                  <span className="text-slate-700 font-medium">
                    Server In-Memory Blur {serverSideBlurApplied ? '(Active)' : ''}
                  </span>
                  <input
                    type="checkbox"
                    checked={serverSideBlurActive}
                    onChange={(e) => setServerSideBlurActive(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                </label>

                <label className="flex items-center justify-between cursor-pointer py-0.5">
                  <span className="text-slate-700 font-medium">Teacher Zone Outline</span>
                  <input
                    type="checkbox"
                    checked={zoneFilteringEnabled}
                    onChange={(e) => {
                      setZoneFilteringEnabled(e.target.checked)
                      setShowZoneOverlay(e.target.checked)
                    }}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                </label>
              </div>
            </div>

            {/* Collapsed Advanced Parameters Section */}
            <details className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs group">
              <summary className="p-3.5 text-xs font-bold text-slate-800 uppercase tracking-wider cursor-pointer bg-slate-50 flex items-center justify-between select-none">
                <div className="flex items-center gap-2">
                  <Settings className="h-3.5 w-3.5 text-slate-500" />
                  <span>Advanced Parameters</span>
                </div>
                <ChevronDown className="h-4 w-4 text-slate-400 group-open:rotate-180 transition-transform" />
              </summary>

              <div className="p-4 space-y-3.5 border-t border-slate-100">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600 font-medium">Frame Skipping:</span>
                    <strong className="text-blue-600 font-mono font-bold">Every {frameSkip} frames</strong>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    step="1"
                    value={frameSkip}
                    onChange={(e) => setFrameSkip(parseInt(e.target.value, 10))}
                    className="w-full accent-blue-600 bg-slate-200 h-1.5 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600 font-medium">Keypoint Threshold:</span>
                    <strong className="text-blue-600 font-mono font-bold">{(keypointThreshold * 100).toFixed(0)}%</strong>
                  </div>
                  <input
                    type="range"
                    min="0.10"
                    max="0.90"
                    step="0.05"
                    value={keypointThreshold}
                    onChange={(e) => setKeypointThreshold(parseFloat(e.target.value))}
                    className="w-full accent-blue-600 bg-slate-200 h-1.5 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600 font-medium">Elevation Margin:</span>
                    <strong className="text-emerald-600 font-mono font-bold">{elevationMarginPx} px</strong>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    step="5"
                    value={elevationMarginPx}
                    onChange={(e) => setElevationMarginPx(parseFloat(e.target.value))}
                    className="w-full accent-emerald-600 bg-slate-200 h-1.5 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5 pt-2 border-t border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-700 block">Teacher Zone Preset</span>
                  <div className="grid grid-cols-2 gap-1 text-xs">
                    {(['left', 'right', 'center', 'full'] as const).map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setZonePreset(preset)}
                        className={`p-1.5 rounded-md border text-left capitalize transition text-[11px] ${
                          activeZonePreset === preset
                            ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                            : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </details>

            {/* Privacy & Zero-Biometrics Summary */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-1.5 text-xs text-slate-600">
              <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                <Shield className="h-3.5 w-3.5 text-blue-600" />
                <span>Zero-Biometrics Safeguard</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Anonymous YOLOv8 bounding boxes and pose skeletons only. Facial recognition, emotion tracking, and student profiling are strictly absent.
              </p>
            </div>
          </div>

        </div>
      ) : (
        /* SIMULATED VIEWPORT CANVAS (LEGACY DEMO FALLBACK) */
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          <div className="xl:col-span-3 space-y-4">
            <div className="relative aspect-video w-full rounded-2xl border border-slate-800 bg-[#0a0c13] overflow-hidden shadow-2xl flex flex-col justify-between">
              <div className="absolute inset-0 bg-gradient-to-b from-slate-900/40 via-transparent to-slate-950/80 pointer-events-none" />

              <div className="absolute inset-0 opacity-15 pointer-events-none">
                <svg width="100%" height="100%">
                  <line x1="0" y1="30%" x2="100%" y2="30%" stroke="#94a3b8" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="0" y1="55%" x2="100%" y2="55%" stroke="#94a3b8" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="0" y1="80%" x2="100%" y2="80%" stroke="#94a3b8" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="15%" y1="0" x2="35%" y2="100%" stroke="#94a3b8" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="85%" y1="0" x2="65%" y2="100%" stroke="#94a3b8" strokeWidth="1" strokeDasharray="4 4" />
                </svg>
              </div>

              <div className="relative z-10 flex items-center justify-between p-4 bg-gradient-to-b from-black/80 to-transparent">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1.5 rounded-md bg-rose-500/20 px-2.5 py-1 text-xs font-bold text-rose-300 border border-rose-500/40">
                    <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
                    SIMULATED CAM 01
                  </span>
                  <span className="text-xs text-slate-300 font-mono">1080p @ 30 FPS &bull; Session: sess_01</span>
                </div>

                <div className="flex items-center gap-2">
                  <DataStatusBadge status="DEMO DATA" size="sm" />
                </div>
              </div>

              {/* Bounding Box Overlays */}
              {showBoxes && (
                <div className="absolute inset-0 z-10 pointer-events-none">
                  {demoBoxes
                    .filter((b) => {
                      if (filterClass === 'raised') return b.classId === 0
                      if (filterClass === 'ambiguous') return b.classId === 2
                      return true
                    })
                    .map((box) => (
                      <div
                        key={box.id}
                        className="absolute border-2 rounded border-cyan-500/60 shadow-cyan-500/20 shadow-lg"
                        style={{
                          left: `${box.x}%`,
                          top: `${box.y}%`,
                          width: `${box.w}%`,
                          height: `${box.h}%`,
                        }}
                      >
                        <div className="absolute -top-5 left-0 px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-t bg-cyan-600/90 text-white">
                          P{box.personId}: {box.className} ({(box.confidence * 100).toFixed(0)}%)
                        </div>
                      </div>
                    ))}
                </div>
              )}

              <div className="relative z-10 p-4 bg-gradient-to-t from-black/90 to-transparent flex items-center justify-between text-xs">
                <span className="text-slate-300">
                  Simulated Student Count: <strong className="text-white">{demoBoxes.length}</strong>
                </span>
                <span className="text-[11px] text-slate-400">Offline Demonstration Stream</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 bg-white shadow-2xs">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showBoxes}
                  onChange={(e) => setShowBoxes(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Show Bounding Boxes</span>
              </label>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500">Filter:</span>
                {(['all', 'raised', 'ambiguous'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setFilterClass(mode)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors ${
                      filterClass === mode
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-2xs">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sliders className="h-4 w-4 text-blue-600" />
                <span>Simulation Controls</span>
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Offline demonstration stream for evaluation without hardware cameras.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

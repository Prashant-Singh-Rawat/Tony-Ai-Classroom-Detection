// frontend/src/pages/MonitoringPage.tsx
import React, { useEffect, useRef, useState } from 'react'
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
  Sparkles,
  Info,
  Camera,
  CameraOff,
  Radio,
  Wifi,
  WifiOff,
  Hand,
  Activity,
  Timer,
  UserCheck,
  RefreshCw,
  Database,
  Lock,
  EyeOff,
} from 'lucide-react'
import { api } from '../services'
import type {
  BoundingBox,
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

export const MonitoringPage: React.FC = () => {
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

      if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        if (file.type.startsWith('video/')) {
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
      if (selectedFile.type.startsWith('video/')) {
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

  const getActivityBoxConfig = (det: BoundingBox) => {
    const rawLabel = det.activityLabel || (det.handRaised ? 'HAND_RAISED' : (det.status === 'NEEDS_REVIEW' ? 'NEEDS_REVIEW' : 'NO_FLAG_OBSERVED'))

    // RED: PHONE VISIBLE, HEAD-DOWN POSTURE
    if (rawLabel === 'PHONE_VISIBLE' || rawLabel === 'HEAD_DOWN_POSTURE') {
      return {
        border: 'border-rose-500 bg-rose-500/15 shadow-rose-500/30',
        text: 'text-rose-400 font-extrabold',
        badgeBg: 'border-rose-500/60 bg-rose-950/90',
        label: rawLabel === 'PHONE_VISIBLE' ? 'PHONE VISIBLE' : 'HEAD-DOWN POSTURE',
        isHand: false,
      }
    }

    // ORANGE: POSSIBLE PEER INTERACTION, POSSIBLE SPEAKING
    if (rawLabel === 'POSSIBLE_PEER_INTERACTION' || rawLabel === 'POSSIBLE_SPEAKING') {
      return {
        border: 'border-amber-500 bg-amber-500/15 shadow-amber-500/30',
        text: 'text-amber-400 font-bold',
        badgeBg: 'border-amber-500/60 bg-amber-950/90',
        label: rawLabel === 'POSSIBLE_PEER_INTERACTION' ? 'POSSIBLE PEER INTERACTION' : 'POSSIBLE SPEAKING',
        isHand: false,
      }
    }

    // BLUE: HAND RAISED (and LEFT, RIGHT, BOTH)
    if (rawLabel.includes('HAND') || det.handRaised) {
      let display = 'HAND RAISED'
      if (rawLabel === 'LEFT_HAND_RAISED') display = 'LEFT HAND RAISED'
      else if (rawLabel === 'RIGHT_HAND_RAISED') display = 'RIGHT HAND RAISED'
      else if (rawLabel === 'BOTH_HANDS_RAISED') display = 'BOTH HANDS RAISED'
      return {
        border: 'border-blue-500 bg-blue-500/15 shadow-blue-500/30',
        text: 'text-blue-400 font-extrabold',
        badgeBg: 'border-blue-500/60 bg-blue-950/90',
        label: display,
        isHand: true,
      }
    }

    // YELLOW: NEEDS REVIEW
    if (rawLabel === 'NEEDS_REVIEW' || det.status === 'NEEDS_REVIEW' || det.classId === 2) {
      return {
        border: 'border-yellow-400 bg-yellow-400/15 shadow-yellow-400/30',
        text: 'text-yellow-300 font-bold',
        badgeBg: 'border-yellow-500/60 bg-yellow-950/90',
        label: 'NEEDS REVIEW',
        isHand: false,
      }
    }

    // GREEN: NO FLAG OBSERVED (Default)
    return {
      border: 'border-emerald-500 bg-emerald-500/10 shadow-emerald-500/20',
      text: 'text-emerald-400 font-semibold',
      badgeBg: 'border-emerald-500/50 bg-slate-950/90',
      label: 'NO FLAG OBSERVED',
      isHand: false,
    }
  }

  return (
    <div className="space-y-6">
      {/* Hidden offscreen canvas for webcam frame extraction */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Top Header & Tab Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Video className="h-5 w-5 text-cyan-400" />
            <span>ClassVision AI — Live Classroom Studio</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Phase 2.5: Real YOLOv8n &amp; YOLOv8n-pose 17-Keypoint Hand-Raising Analysis (0% Real Classroom Footage &bull; Anonymous IDs)
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* WebSocket status pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl border border-slate-800 bg-slate-950/60 text-xs">
            {wsStatus === 'connected' ? (
              <>
                <Radio className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
                <span className="text-emerald-300 font-semibold text-[11px]">WS Live</span>
              </>
            ) : wsStatus === 'connecting' ? (
              <>
                <Activity className="h-3.5 w-3.5 text-amber-400 animate-spin" />
                <span className="text-amber-300 font-semibold text-[11px]">WS Connecting</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5 text-slate-500" />
                <span className="text-slate-400 text-[11px]">WS Offline</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('real_yolo')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                activeTab === 'real_yolo'
                  ? 'border-cyan-500 bg-cyan-500/20 text-cyan-300 shadow-lg shadow-cyan-500/10'
                  : 'border-slate-800 bg-slate-800/40 text-slate-400 hover:text-white'
              }`}
            >
              Live Classroom AI
            </button>
            <button
              onClick={() => setActiveTab('simulated_viewport')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                activeTab === 'simulated_viewport'
                  ? 'border-violet-500 bg-violet-500/20 text-violet-300 shadow-lg shadow-violet-500/10'
                  : 'border-slate-800 bg-slate-800/40 text-slate-400 hover:text-white'
              }`}
            >
              Simulated Viewport
            </button>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3.5 text-xs text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-400 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-xs text-rose-400 hover:text-rose-200"
          >
            Dismiss
          </button>
        </div>
      )}

      {dbErrorMessage && (
        <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3.5 text-xs text-amber-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0" />
            <span>
              <strong>SQLite Event Persistence Notice:</strong> {dbErrorMessage} (Live video streaming continues unaffected in volatile RAM).
            </span>
          </div>
          <button
            onClick={() => setDbErrorMessage(null)}
            className="text-xs text-amber-400 hover:text-amber-200"
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
            <div className="relative aspect-video w-full rounded-2xl border border-slate-800 bg-[#07090e] overflow-hidden shadow-2xl flex flex-col justify-between">
              {/* Visual Display */}
              <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
                {/* 1. Live Webcam Feed (Always in DOM for immediate media stream binding) */}
                <div
                  className={`relative inline-flex items-center justify-center max-h-full max-w-full ${
                    isWebcamActive ? '' : 'hidden'
                  }`}
                >
                  <video
                    ref={videoRef}
                    className="max-h-[500px] w-auto max-w-full object-contain mx-auto rounded shadow-lg block"
                    autoPlay
                    playsInline
                    muted
                    onLoadedMetadata={() => setVideoMetadataLoaded(true)}
                  />

                  {/* Bounding Box & Skeleton Overlays on Webcam */}
                  {isWebcamActive && detectionResult && detectionResult.boxes && (
                    <div className="absolute inset-0 pointer-events-none">
                        {detectionResult.boxes.map((det) => {
                          const cfg = getActivityBoxConfig(det)

                          return (
                            <div
                              key={det.id}
                              className={`absolute border-2 rounded shadow-lg transition-all ${cfg.border}`}
                              style={{
                                left: `${det.x}%`,
                                top: `${det.y}%`,
                                width: `${det.w}%`,
                                height: `${det.h}%`,
                              }}
                            >
                              <div className={`absolute -top-6 left-0 flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider rounded-t ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>
                                {cfg.isHand && <Hand className="h-3 w-3 text-blue-400 fill-current animate-bounce" />}
                                <span>{det.id}:</span>
                                <span className={cfg.text}>
                                  {cfg.label}
                                </span>
                                <span className="text-slate-300">({(det.confidence * 100).toFixed(0)}%)</span>
                                {det.activityDurationSeconds !== undefined && det.activityDurationSeconds > 0 && (
                                  <span className="text-cyan-300 font-semibold font-mono">{det.activityDurationSeconds.toFixed(1)}s</span>
                                )}
                              </div>

                              {blurFaces && (
                                <div className="absolute top-1 left-2 right-2 h-7 rounded bg-slate-900/70 backdrop-blur-md border border-cyan-300/30 flex items-center justify-center pointer-events-none">
                                  <span className="text-[7px] text-cyan-200 font-bold tracking-tight">PRIVACY BLUR</span>
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
                                        stroke={b.handRaised && isArm ? '#34d399' : '#38bdf8'}
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        opacity="0.85"
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
                                        fill={isWrist ? (b.handRaised ? '#10b981' : '#38bdf8') : '#818cf8'}
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

                {/* 2. Uploaded Image / Video Display */}
                {!isWebcamActive && previewUrl && (
                  <div className="relative inline-block max-h-full max-w-full">
                    {selectedFile?.type.startsWith('video/') ? (
                      videoResult ? (
                        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 text-center">
                          <CheckCircle2 className="h-10 w-10 text-cyan-400 mx-auto mb-3" />
                          <h4 className="text-base font-bold text-white mb-2">Video Processing Complete</h4>
                          <p className="text-xs text-slate-400">Classroom video analyzed using YOLOv8n</p>
                        </div>
                      ) : (
                        <div className="relative inline-block mx-auto max-w-full">
                          <video
                            src={previewUrl}
                            controls
                            playsInline
                            className="max-h-[460px] w-auto object-contain mx-auto rounded-lg shadow-xl border border-slate-800 block"
                          />

                          {/* Teacher Zone Exclusion Polygon Preview */}
                          {showZoneOverlay && zoneFilteringEnabled && instructorPolygon && (
                            <svg
                              className="absolute inset-0 w-full h-full pointer-events-none rounded-lg"
                              viewBox="0 0 100 100"
                              preserveAspectRatio="none"
                            >
                              <polygon
                                points={instructorPolygon.map(([x, y]) => `${x * 100},${y * 100}`).join(' ')}
                                fill="rgba(245, 158, 11, 0.18)"
                                stroke="#f59e0b"
                                strokeWidth="1.2"
                                strokeDasharray="3 2"
                              />
                              {instructorPolygon[0] && (
                                <text
                                  x={instructorPolygon[0][0] * 100 + 2}
                                  y={instructorPolygon[0][1] * 100 + 7}
                                  fill="#f59e0b"
                                  fontSize="3.8"
                                  fontWeight="bold"
                                  fontFamily="monospace"
                                  className="tracking-wider uppercase select-none"
                                >
                                  TEACHING ZONE (EXCLUDED)
                                </text>
                              )}
                            </svg>
                          )}
                        </div>
                      )
                    ) : (
                      <>
                        <img
                          src={previewUrl}
                          alt="Uploaded frame"
                          className="max-h-[500px] w-auto object-contain mx-auto rounded"
                        />

                        {/* Bounding Box Overlays */}
                        {detectionResult &&
                          detectionResult.boxes &&
                          detectionResult.boxes.map((det) => {
                            const cfg = getActivityBoxConfig(det)

                            return (
                              <div
                                key={det.id}
                                className={`absolute border-2 rounded shadow-lg transition-all ${cfg.border}`}
                                style={{
                                  left: `${det.x}%`,
                                  top: `${det.y}%`,
                                  width: `${det.w}%`,
                                  height: `${det.h}%`,
                                }}
                              >
                                <div className={`absolute -top-6 left-0 flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider rounded-t ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>
                                  {cfg.isHand && <Hand className="h-3 w-3 text-blue-400 fill-current animate-bounce" />}
                                  <span>{det.id}:</span>
                                  <span className={cfg.text}>
                                    {cfg.label}
                                  </span>
                                  <span className="text-slate-300">({(det.confidence * 100).toFixed(0)}%)</span>
                                  {det.activityDurationSeconds !== undefined && det.activityDurationSeconds > 0 && (
                                    <span className="text-cyan-300 font-semibold font-mono">{det.activityDurationSeconds.toFixed(1)}s</span>
                                  )}
                                </div>

                                {blurFaces && (
                                  <div className="absolute top-1 left-2 right-2 h-7 rounded bg-slate-900/70 backdrop-blur-md border border-cyan-300/30 flex items-center justify-center pointer-events-none">
                                    <span className="text-[7px] text-cyan-200 font-bold tracking-tight">PRIVACY BLUR</span>
                                  </div>
                                )}
                              </div>
                            )
                          })}

                        {/* Keypoint Overlay for Image */}
                        {showKeypoints && detectionResult && detectionResult.boxes && (
                          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                            {detectionResult.boxes.map((b) => {
                              if (!b.keypoints || b.keypoints.length === 0) return null
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
                                        stroke={b.handRaised && isArm ? '#34d399' : '#38bdf8'}
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        opacity="0.85"
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
                                        fill={isWrist ? (b.handRaised ? '#10b981' : '#38bdf8') : '#818cf8'}
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
                      </>
                    )}
                  </div>
                )}

                {/* 3. Synthetic Result State */}
                {!isWebcamActive && !previewUrl && detectionResult && (
                  <div className="text-center p-8 space-y-4">
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
                              ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-300'
                              : det.status === 'NEEDS_REVIEW'
                              ? 'border-amber-500/40 bg-amber-950/20 text-amber-300'
                              : 'border-cyan-500/30 bg-cyan-950/20 text-cyan-300'
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
                  <div className="text-center p-8 space-y-3">
                    <div className="inline-flex p-3 rounded-full bg-slate-800/60 text-slate-400 border border-slate-700/60">
                      <Camera className="h-7 w-7" />
                    </div>
                    <h4 className="text-sm font-semibold text-slate-200">No Active Stream or Media Selected</h4>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Start your laptop webcam for real-time WebSocket inference, or upload an image/video file to run YOLOv8n-pose detection.
                    </p>
                  </div>
                )}
              </div>

              {/* Bottom HUD Bar */}
              <div className="relative z-10 p-3 bg-gradient-to-t from-black/95 to-transparent flex flex-wrap items-center justify-between gap-3 text-xs border-t border-slate-800/60">
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
            </div>

            {/* Viewport Control Toggles */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-xs font-medium text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={blurFaces}
                    onChange={(e) => setBlurFaces(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-800 text-cyan-600 focus:ring-cyan-500"
                  />
                  <Shield className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Privacy Face-Blur</span>
                </label>

                <label className="flex items-center gap-2 text-xs font-medium text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showKeypoints}
                    onChange={(e) => setShowKeypoints(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-800 text-emerald-600 focus:ring-emerald-500"
                  />
                  <Activity className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Show 17-Keypoint Skeletons</span>
                </label>
              </div>

              <span className="text-xs text-slate-400 font-mono">
                Model: <strong>{detectPose ? 'yolov8n-pose.pt' : 'yolov8n.pt'}</strong> &bull; Batch: 1 &bull; 0% Real Classroom Footage
              </span>
            </div>

            {/* Sequential Classroom Video Processing Metrics & Teacher Zone Breakdown Card */}
            {!isWebcamActive && videoResult && (
              <div className="rounded-2xl border border-violet-500/30 bg-slate-900/80 p-5 space-y-4 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="p-2.5 rounded-xl bg-violet-500/20 text-violet-400 border border-violet-500/30">
                      <Video className="h-5 w-5" />
                    </span>
                    <div>
                      <h4 className="text-sm font-bold text-white">Sequential Classroom Video Processing Complete</h4>
                      <p className="text-xs text-slate-400">
                        File: <strong className="text-slate-200">{videoResult.videoFilename}</strong> &bull; Duration: {videoResult.durationSeconds}s &bull; Format: <strong className="text-cyan-300 font-mono">{videoResult.width || '--'}x{videoResult.height || '--'} ({videoResult.aspectRatio || '16:9'} {videoResult.orientation || 'LANDSCAPE'})</strong>
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-left">
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Total Frames</span>
                    <span className="text-base font-bold text-white">{videoResult.totalFrames}</span>
                    <span className="text-[10px] text-slate-500 block">Sampled: {videoResult.processedFrames}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Peak Persons</span>
                    <span className="text-base font-bold text-cyan-400">{videoResult.maxPersonsInFrame}</span>
                    <span className="text-[10px] text-slate-500 block">Avg: {videoResult.avgPersonsPerFrame} / frame</span>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Hand Raises</span>
                    <span className="text-base font-bold text-emerald-400">{videoResult.totalHandRaises ?? 0}</span>
                    <span className="text-[10px] text-amber-400 block">Review: {videoResult.totalNeedsReview ?? 0}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/60">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Inference Throughput</span>
                    <span className="text-base font-bold text-violet-400">{videoResult.inferenceFps || videoResult.processingFps} FPS</span>
                    <span className="text-[10px] text-slate-500 block">Dec FPS: {videoResult.decodingFps || '--'}</span>
                  </div>
                </div>

                {/* Secondary Metrics Bar */}
                <div className="grid grid-cols-3 gap-2 text-left text-xs bg-slate-950/40 p-3 rounded-xl border border-slate-800/60">
                  <div>
                    <span className="text-slate-500 text-[10px] block">Temporal Tracks</span>
                    <strong className="text-white font-mono">{videoResult.trackedPersonsCount ?? videoResult.maxPersonsInFrame} active</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">Hand Raise Events</span>
                    <strong className="text-emerald-300 font-mono">{videoResult.handRaiseEventsCount ?? videoResult.totalHandRaises ?? 0} persisted</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">Corrupt Frames Skipped</span>
                    <strong className={videoResult.corruptedFramesCount ? 'text-amber-400 font-mono' : 'text-slate-300 font-mono'}>
                      {videoResult.corruptedFramesCount ?? 0}
                    </strong>
                  </div>
                </div>

                {/* Teacher Zone Exclusion Analytics & Comparison Card */}
                <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 space-y-3 text-left">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-500/20 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold text-[10px] font-mono border border-amber-500/30">
                        TEACHER ROI EXCLUSION
                      </span>
                      <h5 className="text-xs font-bold text-white uppercase tracking-wider">
                        Zone Participation Breakdown
                      </h5>
                    </div>
                    {/* Comparison Toggle */}
                    <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[10px] font-mono">
                      <button
                        type="button"
                        onClick={() => setZoneCompareMode('filtered')}
                        className={`px-2 py-0.5 rounded transition ${
                          zoneCompareMode === 'filtered'
                            ? 'bg-amber-500 text-slate-950 font-bold'
                            : 'text-slate-400 hover:text-white'
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
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Raw (Unfiltered)
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block font-medium">Total Detected</span>
                      <span className="text-base font-bold text-white font-mono">
                        {videoResult.totalHandRaises ?? 0}
                      </span>
                      <span className="text-[10px] text-slate-500 block">All physical gestures</span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30">
                      <span className="text-[10px] text-emerald-300 block font-medium">Student-Zone Events</span>
                      <span className="text-base font-bold text-emerald-400 font-mono">
                        {zoneCompareMode === 'filtered'
                          ? (videoResult.studentZoneEventsCount ?? (videoResult.totalHandRaises ? Math.max(0, videoResult.totalHandRaises - (videoResult.instructorZoneEventsCount ?? 0)) : 0))
                          : (videoResult.totalHandRaises ?? 0)}
                      </span>
                      <span className="text-[10px] text-emerald-300/70 block">
                        {zoneCompareMode === 'filtered' ? 'Included in student totals' : 'Unfiltered raw total'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-500/30">
                      <span className="text-[10px] text-amber-300 block font-medium">Instructor-Zone Events</span>
                      <span className="text-base font-bold text-amber-400 font-mono">
                        {videoResult.instructorZoneEventsCount ?? 0}
                      </span>
                      <span className="text-[10px] text-amber-300/70 block">
                        {zoneFilteringEnabled ? 'Excluded from student totals' : 'Preserved in database'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-purple-950/30 border border-purple-500/30">
                      <span className="text-[10px] text-purple-300 block font-medium">Uncertain Events</span>
                      <span className="text-base font-bold text-purple-400 font-mono">
                        {videoResult.uncertainZoneEventsCount ?? videoResult.totalNeedsReview ?? 0}
                      </span>
                      <span className="text-[10px] text-purple-300/70 block">Marked NEEDS_REVIEW</span>
                    </div>
                  </div>

                  <p className="text-[10px] text-slate-400 italic">
                    Spatial origin only. Polygon containment identifies events within the designated teaching perimeter and does not identify individuals or verify teacher identity.
                  </p>
                </div>
              </div>
            )}
            {poseResult && (
              <div className="rounded-2xl border border-violet-500/30 bg-slate-900/80 p-5 space-y-4 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-violet-500/20 text-violet-300 border border-violet-500/30 font-mono">
                        YOLOv8n-pose
                      </span>
                      <span className="text-xs font-semibold text-white">Observable Human Posture Analysis</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      17 COCO Keypoints &bull; Arm Elevation &bull; Elbow Angles &bull; Strictly Anonymous IDs
                    </p>
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-slate-400">
                      Latency: <strong className="font-mono text-cyan-400">{poseResult.processingTimeMs} ms</strong> ({poseResult.processingFps} FPS)
                    </span>
                    <span className="text-slate-400">
                      Device: <strong className="font-mono text-emerald-400 uppercase">{poseResult.inferenceDevice}</strong>
                    </span>
                  </div>
                </div>

                {/* Posture Counts Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-medium">Both Raised</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono">
                      {poseResult.postureCounts['BOTH_ARMS_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-medium">Left Arm Raised</span>
                    <span className="text-lg font-bold text-cyan-400 font-mono">
                      {poseResult.postureCounts['LEFT_ARM_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-medium">Right Arm Raised</span>
                    <span className="text-lg font-bold text-cyan-400 font-mono">
                      {poseResult.postureCounts['RIGHT_ARM_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-medium">Not Raised</span>
                    <span className="text-lg font-bold text-slate-300 font-mono">
                      {poseResult.postureCounts['ARMS_NOT_RAISED'] || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block font-medium">Needs Review</span>
                    <span className="text-lg font-bold text-amber-400 font-mono">
                      {poseResult.postureCounts['NEEDS_REVIEW'] || 0}
                    </span>
                  </div>
                </div>

                {/* Person-by-Person Breakdown */}
                <div className="space-y-2.5 pt-2">
                  <span className="text-xs font-semibold text-slate-300 block">
                    Detected Persons ({poseResult.persons.length})
                  </span>
                  <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                    {poseResult.persons.map((person) => {
                      const postureColor =
                        person.posture === 'BOTH_ARMS_RAISED'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                          : person.posture === 'LEFT_ARM_RAISED' || person.posture === 'RIGHT_ARM_RAISED'
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                          : person.posture === 'NEEDS_REVIEW'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                          : 'bg-slate-800 text-slate-300 border-slate-700'

                      return (
                        <div
                          key={person.id}
                          className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 text-xs space-y-2"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-cyan-300 font-bold">{person.id}</span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${postureColor}`}>
                                {person.posture.replace(/_/g, ' ')}
                              </span>
                              <span className="text-[10px] text-slate-500">
                                Pose Conf: {(person.confidence * 100).toFixed(0)}%
                              </span>
                            </div>

                            <div className="flex items-center gap-3 text-[11px] text-slate-400">
                              <span>
                                Left Elbow:{' '}
                                <strong className="text-slate-200">
                                  {person.geometry.leftArm.elbowAngleDeg != null ? `${person.geometry.leftArm.elbowAngleDeg}°` : 'N/A'}
                                </strong>
                              </span>
                              <span>
                                Right Elbow:{' '}
                                <strong className="text-slate-200">
                                  {person.geometry.rightArm.elbowAngleDeg != null ? `${person.geometry.rightArm.elbowAngleDeg}°` : 'N/A'}
                                </strong>
                              </span>
                            </div>
                          </div>

                          <p className="text-[11px] text-slate-300">
                            <span className="text-slate-400 font-medium">Observation: </span>
                            {person.postureReason}
                          </p>

                          <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500 pt-1 border-t border-slate-800/60">
                            <div>
                              <span>Elevation: </span>
                              <span className="text-slate-300">
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
            <div className="rounded-2xl border border-emerald-500/30 bg-slate-900/80 p-5 space-y-4 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">
                      PHASE 2.2
                    </span>
                    <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                      <Timer className="h-4 w-4 text-emerald-400" />
                      Temporal Hand-Raising Detection &amp; Anonymous Tracking
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    IoU Trajectory Continuity &bull; Gap Tolerance &bull; Cooldown Protection &bull; SQLite Persistence
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={refreshTrackingData}
                    className="p-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1 transition"
                    title="Refresh Tracking Events"
                  >
                    <RefreshCw className="h-3 w-3" />
                    <span className="text-[10px]">Sync</span>
                  </button>
                  <button
                    onClick={handleResetTracking}
                    className="px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-rose-900/40 hover:border-rose-700 text-slate-300 hover:text-rose-200 text-[10px] transition"
                  >
                    Reset Tracks
                  </button>
                </div>
              </div>

              {/* Event Statistics Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-2.5 text-xs">
                <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Total Events</span>
                  <span className="text-lg font-bold text-emerald-400 font-mono">
                    {trackingStats?.totalEvents ?? recentEvents.length}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Active Raises</span>
                  <span className="text-lg font-bold text-cyan-400 font-mono">
                    {activeEvents.length}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Completed</span>
                  <span className="text-lg font-bold text-slate-300 font-mono">
                    {trackingStats?.completedEvents ?? recentEvents.filter((e) => e.state === 'COMPLETED').length}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Avg Duration</span>
                  <span className="text-lg font-bold text-amber-400 font-mono">
                    {trackingStats?.avgDurationSeconds ? `${trackingStats.avgDurationSeconds}s` : '0.0s'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Left / Right / Both</span>
                  <span className="text-xs font-bold text-slate-300 font-mono block mt-1">
                    {trackingStats ? `${trackingStats.leftHandCount} / ${trackingStats.rightHandCount} / ${trackingStats.bothHandsCount}` : '0 / 0 / 0'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-medium">Needs Review</span>
                  <span className="text-lg font-bold text-amber-400 font-mono">
                    {trackingStats?.needsReviewCount ?? 0}
                  </span>
                </div>
              </div>

              {/* Active Tracks & Recent Events Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                {/* Active Tracks Panel */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <UserCheck className="h-3.5 w-3.5 text-cyan-400" />
                    <span>Active Tracked Persons ({trackedPersons.length})</span>
                  </h4>
                  {trackedPersons.length === 0 ? (
                    <div className="p-3.5 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-500">
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
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          : isRaising
                          ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                          : isLowering
                          ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                          : isReview
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-slate-800 text-slate-400 border-slate-700'

                        return (
                          <div
                            key={tp.trackId}
                            className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/50 flex items-center justify-between gap-3 text-xs"
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-bold text-cyan-400">{tp.trackId}</span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${badgeColor}`}>
                                {tp.state}
                              </span>
                              {tp.handSide !== 'NONE' && (
                                <span className="text-[10px] font-mono text-slate-400 uppercase">
                                  [{tp.handSide.replace('_HAND', '')}]
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono">
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
                  <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Hand className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Recent Continuous Events ({recentEvents.length})</span>
                  </h4>
                  {recentEvents.length === 0 ? (
                    <div className="p-3.5 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-500">
                      No hand-raising events recorded yet.
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {recentEvents.slice(0, 5).map((evt) => (
                        <div
                          key={evt.eventId}
                          className="p-2.5 rounded-xl border border-slate-800 bg-slate-950/50 flex items-center justify-between gap-2 text-xs"
                        >
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono font-bold text-white text-[11px]">{evt.eventId}</span>
                              <span className="text-[10px] font-mono text-cyan-300">({evt.trackId})</span>
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                {evt.handSide.replace('_HAND', '')}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-400">
                              Duration: <strong className="text-emerald-400 font-mono">{evt.durationSeconds}s</strong> ({evt.frameCount} frames)
                            </span>
                          </div>

                          <div className="text-right">
                            <span className="text-[10px] text-slate-500 block">
                              Peak Conf: {(evt.maxConfidence * 100).toFixed(0)}%
                            </span>
                            <span className="text-[9px] text-slate-500 font-mono">
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

          {/* Right Column: Controls & Hardware Specs (1 Col) */}
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 backdrop-blur shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-cyan-400" />
                  <span>Live Controls</span>
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                  PHASE 2.5
                </span>
              </div>

              {/* Webcam Controls */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 block">Webcam Live Stream</label>
                {!isWebcamActive ? (
                  <button
                    onClick={startWebcam}
                    className="w-full flex items-center justify-center gap-2 rounded-xl border border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20 py-2.5 text-xs font-bold text-emerald-300 transition-colors shadow-lg shadow-emerald-500/10"
                  >
                    <Camera className="h-4 w-4" />
                    <span>Start Laptop Webcam</span>
                  </button>
                ) : (
                  <button
                    onClick={stopWebcam}
                    className="w-full flex items-center justify-center gap-2 rounded-xl border border-rose-500/40 bg-rose-500/10 hover:bg-rose-500/20 py-2.5 text-xs font-bold text-rose-300 transition-colors shadow-lg shadow-rose-500/10"
                  >
                    <CameraOff className="h-4 w-4" />
                    <span>Stop Webcam Stream</span>
                  </button>
                )}
              </div>

              {/* WebSocket Reconnect / Disconnect */}
              <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-center gap-2">
                  {wsStatus === 'connected' ? (
                    <Wifi className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <WifiOff className="h-3.5 w-3.5 text-slate-500" />
                  )}
                  <span className="text-slate-300">
                    WebSocket: <strong className="font-mono text-white">{wsStatus}</strong>
                  </span>
                </div>

                {wsStatus === 'connected' ? (
                  <button
                    onClick={disconnectWebSocket}
                    className="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800"
                  >
                    Disconnect
                  </button>
                ) : (
                  <button
                    onClick={reconnectWebSocket}
                    className="text-[10px] text-cyan-400 hover:text-cyan-200 px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800"
                  >
                    Reconnect
                  </button>
                )}
              </div>

              {/* Computer Vision Model Mode Toggle */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">Computer Vision Mode</label>
                <div className="grid grid-cols-2 gap-1 p-1 bg-slate-950 rounded-xl border border-slate-800">
                  <button
                    type="button"
                    onClick={() => {
                      setInferenceMode('person_detection')
                      setDetectPose(false)
                    }}
                    className={`py-2 px-2 rounded-lg text-xs font-semibold transition text-center ${
                      inferenceMode === 'person_detection'
                        ? 'bg-cyan-600 text-white shadow-md'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Person (YOLOv8n)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setInferenceMode('pose_estimation')
                      setDetectPose(true)
                    }}
                    className={`py-2 px-2 rounded-lg text-xs font-semibold transition text-center ${
                      inferenceMode === 'pose_estimation'
                        ? 'bg-violet-600 text-white shadow-md'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Pose (YOLOv8n-pose)
                  </button>
                </div>
              </div>

              {/* File Upload Selector */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 block">Select Input Media File</label>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/jpeg,image/png,image/webp,video/mp4,video/avi,video/quicktime"
                  className="hidden"
                />

                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700 hover:border-cyan-500/60 rounded-xl p-4 text-center cursor-pointer transition-colors bg-slate-950/40"
                >
                  <Upload className="h-5 w-5 text-slate-400 mx-auto mb-1.5" />
                  <span className="text-xs text-slate-200 font-medium block truncate">
                    {selectedFile ? selectedFile.name : 'Click to Upload Image or Video'}
                  </span>
                  <span className="text-[10px] text-slate-500">JPG, PNG, WEBP, MP4 (Max 100MB)</span>
                </div>
              </div>

              {/* Detection Confidence Threshold Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300">
                    {selectedFile?.type.startsWith('video/')
                      ? 'Classroom Video Confidence:'
                      : 'Detection Confidence:'}
                  </span>
                  <strong className="text-cyan-400 font-mono">{(confidenceThreshold * 100).toFixed(0)}%</strong>
                </div>
                <input
                  type="range"
                  min={selectedFile?.type.startsWith('video/') ? 0.15 : 0.10}
                  max={selectedFile?.type.startsWith('video/') ? 0.50 : 0.90}
                  step={selectedFile?.type.startsWith('video/') ? 0.01 : 0.05}
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
                />
                {selectedFile?.type.startsWith('video/') && (
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>Min: 15%</span>
                    <span className="text-cyan-400 font-bold">Default: 20%</span>
                    <span>Max: 50%</span>
                  </div>
                )}
              </div>

              {/* Keypoint and Elevation Sliders for Pose Estimation */}
              {inferenceMode === 'pose_estimation' && (
                <>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300">Keypoint Visibility Threshold:</span>
                      <strong className="text-violet-400 font-mono">{(keypointThreshold * 100).toFixed(0)}%</strong>
                    </div>
                    <input
                      type="range"
                      min="0.10"
                      max="0.90"
                      step="0.05"
                      value={keypointThreshold}
                      onChange={(e) => setKeypointThreshold(parseFloat(e.target.value))}
                      className="w-full accent-violet-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300">Elevation Margin:</span>
                      <strong className="text-emerald-400 font-mono">{elevationMarginPx} px</strong>
                    </div>
                    <input
                      type="range"
                      min="5"
                      max="50"
                      step="5"
                      value={elevationMarginPx}
                      onChange={(e) => setElevationMarginPx(parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-500 block">
                      Vertical distance wrist must be above shoulder for elevation classification.
                    </span>
                  </div>
                </>
              )}

              {/* Frame Skip Slider (if video selected) */}
              {selectedFile && selectedFile.type.startsWith('video/') && (
                <div className="space-y-1.5 p-2.5 rounded-xl border border-violet-500/30 bg-violet-950/15">
                  <div className="flex justify-between text-xs">
                    <span className="text-violet-300">Frame Skipping:</span>
                    <strong className="text-violet-400 font-mono">Every {frameSkip} frames</strong>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    step="1"
                    value={frameSkip}
                    onChange={(e) => setFrameSkip(parseInt(e.target.value, 10))}
                    className="w-full accent-violet-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
                  />
                  <span className="text-[10px] text-slate-400 block">
                    Optimizes processing for HP Victus 4GB VRAM.
                  </span>
                </div>
              )}

              {/* Teacher Zone Exclusion (Instructor ROI) Controls */}
              <div className="space-y-3 p-3 rounded-xl border border-amber-500/30 bg-amber-950/15">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-xs font-bold text-amber-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={zoneFilteringEnabled}
                      onChange={(e) => setZoneFilteringEnabled(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-800 text-amber-500 focus:ring-amber-400"
                    />
                    <span>Teacher Zone Exclusion</span>
                  </label>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300">
                    OPTIONAL ROI
                  </span>
                </div>

                {zoneFilteringEnabled && (
                  <>
                    <div className="flex items-center justify-between text-[11px] text-slate-300">
                      <span>Preview Overlay on Video:</span>
                      <label className="flex items-center gap-1.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={showZoneOverlay}
                          onChange={(e) => setShowZoneOverlay(e.target.checked)}
                          className="rounded border-slate-700 bg-slate-800 text-amber-500 focus:ring-amber-400"
                        />
                        <span className="text-slate-400 text-[10px]">Show</span>
                      </label>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">Zone Presets</span>
                      <div className="grid grid-cols-2 gap-1 text-[11px]">
                        <button
                          type="button"
                          onClick={() => setZonePreset('left')}
                          className={`p-1.5 rounded text-left border transition ${
                            activeZonePreset === 'left'
                              ? 'border-amber-500/60 bg-amber-500/20 text-amber-300 font-bold'
                              : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          Left Blackboard
                        </button>
                        <button
                          type="button"
                          onClick={() => setZonePreset('right')}
                          className={`p-1.5 rounded text-left border transition ${
                            activeZonePreset === 'right'
                              ? 'border-amber-500/60 bg-amber-500/20 text-amber-300 font-bold'
                              : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          Right Whiteboard
                        </button>
                        <button
                          type="button"
                          onClick={() => setZonePreset('center')}
                          className={`p-1.5 rounded text-left border transition ${
                            activeZonePreset === 'center'
                              ? 'border-amber-500/60 bg-amber-500/20 text-amber-300 font-bold'
                              : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          Front Center
                        </button>
                        <button
                          type="button"
                          onClick={() => setZonePreset('full')}
                          className={`p-1.5 rounded text-left border transition ${
                            activeZonePreset === 'full'
                              ? 'border-amber-500/60 bg-amber-500/20 text-amber-300 font-bold'
                              : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white'
                          }`}
                        >
                          Full Front Width
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[10px] text-slate-500 font-mono">
                        {instructorPolygon ? `${instructorPolygon.length} normalized vertices` : 'Polygon disabled'}
                      </span>
                      <button
                        type="button"
                        onClick={() => setZonePreset('disabled')}
                        className="text-[10px] text-rose-400 hover:text-rose-300 underline font-mono"
                      >
                        Reset / Disable
                      </button>
                    </div>
                  </>
                )}
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-2">
                <button
                  onClick={handleRunInference}
                  disabled={isProcessing || !selectedFile}
                  className={`w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition-all shadow-lg ${
                    isProcessing || !selectedFile
                      ? 'border border-slate-800 bg-slate-800/40 text-slate-500 cursor-not-allowed'
                      : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-cyan-500/20'
                  }`}
                >
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>{isProcessing ? 'Processing Model...' : 'Run File Inference'}</span>
                </button>

                <button
                  onClick={handleRunSyntheticSample}
                  disabled={isProcessing}
                  className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 hover:bg-slate-800 py-2 text-xs font-semibold text-slate-300 transition-colors"
                >
                  <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Test with Synthetic Frame</span>
                </button>
              </div>

              <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-3 text-[11px] text-slate-400 flex items-start gap-2">
                <Info className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Privacy First:</strong> Person detection uses anonymous IDs (`anon_001`...). Face recognition, student identity profiling, and emotional inference are disabled.
                </span>
              </div>
            </div>

            {/* Phase 2.8: Privacy-Chained Live Pipeline & SQLite Persistence Safeguards Card */}
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/15 p-5 space-y-4 backdrop-blur shadow-xl">
              <div className="flex items-center justify-between border-b border-emerald-500/20 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Shield className="h-4 w-4 text-emerald-400" />
                  <span>Privacy &amp; Persistence Safeguards</span>
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 font-bold">
                  PHASE 2.8
                </span>
              </div>

              {/* Client-Side Face Blur Toggle */}
              <div className="space-y-1.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <EyeOff className="h-4 w-4 text-emerald-400" />
                    <span className="text-xs font-semibold text-white">Client-Side Face Blur</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setClientSideBlurActive(!clientSideBlurActive)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                      clientSideBlurActive
                        ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-300'
                        : 'bg-slate-800 border border-slate-700 text-slate-400'
                    }`}
                  >
                    {clientSideBlurActive ? (clientSideBlurDetected ? 'ACTIVE (PRE-TX)' : 'ARMED') : 'OFF'}
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  HTML5 canvas Gaussian filter before Base64 encoding. Face pixels never leave browser unblurred.
                </p>
              </div>

              {/* Server-Side Face Blur Toggle */}
              <div className="space-y-1.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Lock className="h-4 w-4 text-cyan-400" />
                    <span className="text-xs font-semibold text-white">Server-Side In-Memory Blur</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setServerSideBlurActive(!serverSideBlurActive)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                      serverSideBlurActive
                        ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300'
                        : 'bg-slate-800 border border-slate-700 text-slate-400'
                    }`}
                  >
                    {serverSideBlurActive ? (serverSideBlurApplied ? 'ACTIVE (IN-RAM)' : 'ARMED') : 'OFF'}
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  OpenCV Gaussian blur on face ROI in volatile memory. 0 bytes saved to disk or database.
                </p>
              </div>

              {/* SQLite Event Persistence Status & Live Counter */}
              <div className="space-y-2 p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-violet-400" />
                    <span className="text-xs font-semibold text-white">SQLite Persistence</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                      dbPersistenceStatus === 'SAVED' || dbPersistenceStatus === 'CONNECTED'
                        ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300'
                        : dbPersistenceStatus === 'ERROR'
                        ? 'bg-rose-950/80 border-rose-500/40 text-rose-300'
                        : 'bg-slate-900 border-slate-700 text-slate-400'
                    }`}
                  >
                    {dbPersistenceStatus}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Persisted Events:</span>
                  <strong className="text-white font-mono bg-violet-950/60 border border-violet-800/40 px-2 py-0.5 rounded">
                    {persistedEventsCount} in SQLite
                  </strong>
                </div>
              </div>

              {/* Volatile RAM Guarantee */}
              <div className="flex items-center justify-between text-[11px] p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/20 text-emerald-300 font-medium">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Volatile RAM Guarantee</span>
                </div>
                <span className="font-mono text-[10px] text-emerald-400">0 Disk Writes</span>
              </div>

              {/* Reset Active Session Button */}
              <button
                type="button"
                onClick={handleResetWebSocketSession}
                className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 py-2 text-xs font-semibold text-slate-200 transition-colors"
              >
                <RefreshCw className="h-3.5 w-3.5 text-cyan-400" />
                <span>Reset Live Tracker (Preserve History)</span>
              </button>
            </div>

            {/* Hardware & Policy Safeguards Card */}
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-950/15 p-5 space-y-3 backdrop-blur shadow-xl">
              <h3 className="text-sm font-bold text-cyan-300 flex items-center gap-2">
                <Shield className="h-4 w-4" />
                <span>Hardware &amp; Ethics Compliance</span>
              </h3>

              <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 font-bold">&bull;</span>
                  <span><strong>Hardware</strong>: HP Victus ({hardwareStatus?.inference_device?.toUpperCase() || 'CPU'} fallback).</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 font-bold">&bull;</span>
                  <span><strong>Models</strong>: Pretrained YOLOv8n &amp; YOLOv8n-pose.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 font-bold">&bull;</span>
                  <span><strong>Dataset Policy</strong>: 0% real classroom footage.</span>
                </li>
              </ul>
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
                  <line x1="0" y1="30%" x2="100%" y2="30%" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="0" y1="55%" x2="100%" y2="55%" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="0" y1="80%" x2="100%" y2="80%" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="15%" y1="0" x2="35%" y2="100%" stroke="#06b6d4" strokeWidth="1" strokeDasharray="4 4" />
                  <line x1="85%" y1="0" x2="65%" y2="100%" stroke="#06b6d4" strokeWidth="1" strokeDasharray="4 4" />
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

            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur">
              <label className="flex items-center gap-2 text-xs font-medium text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showBoxes}
                  onChange={(e) => setShowBoxes(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-violet-600 focus:ring-violet-500"
                />
                <span>Show Bounding Boxes</span>
              </label>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Filter:</span>
                {(['all', 'raised', 'ambiguous'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setFilterClass(mode)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                      filterClass === mode
                        ? 'bg-violet-600 text-white'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 backdrop-blur">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sliders className="h-4 w-4 text-violet-400" />
                <span>Simulation Controls</span>
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Offline demonstration stream for Phase 0.9 evaluation without hardware cameras.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

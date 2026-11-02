import re

with open("frontend/src/pages/MonitoringPage.tsx", "r", encoding="utf-8") as f:
    code = f.read()

# Replace CRLF with LF for consistent string replacement, we will write back properly
is_crlf = "\r\n" in code
code = code.replace("\r\n", "\n")

# 1. Update ActivityBoxConfig and getActivityBoxConfig
old_color_logic = """function getActivityBoxConfig(det: BoundingBox): ActivityBoxConfig {
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
      border: 'border-rose-500 bg-rose-500/15 shadow-rose-500/30',
      text: 'text-rose-400 font-extrabold',
      badgeBg: 'border-rose-500/70 bg-slate-900/90 text-rose-300',
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
      border: 'border-blue-500 bg-blue-500/15 shadow-blue-500/30',
      text: 'text-blue-400 font-extrabold',
      badgeBg: 'border-blue-500/70 bg-slate-900/90 text-blue-300',
      label: display,
      isHand: true,
    }
  }

  // 3. ORANGE: Head down (N s)
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
      colorName: 'ORANGE',
      border: 'border-amber-500 bg-amber-500/15 shadow-amber-500/30',
      text: 'text-amber-400 font-bold',
      badgeBg: 'border-amber-500/70 bg-slate-900/90 text-amber-300',
      label: display,
      isHand: false,
    }
  }

  // 4. ORANGE: Turned sideways (possible interaction)
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
      border: 'border-amber-500 bg-amber-500/15 shadow-amber-500/30',
      text: 'text-amber-400 font-bold',
      badgeBg: 'border-amber-500/70 bg-slate-900/90 text-amber-300',
      label: 'Turned sideways (possible interaction)',
      isHand: false,
    }
  }

  // 5. YELLOW: Needs review
  if (
    rawLabel === 'Needs review' ||
    rawLabel === 'NEEDS_REVIEW' ||
    det.status === 'NEEDS_REVIEW' ||
    det.classId === 2
  ) {
    return {
      category: 'needs_review',
      colorName: 'YELLOW',
      border: 'border-yellow-400 bg-yellow-400/15 shadow-yellow-400/30',
      text: 'text-yellow-300 font-bold',
      badgeBg: 'border-yellow-400/70 bg-slate-900/90 text-yellow-300',
      label: 'Needs review',
      isHand: false,
    }
  }

  // 6. GREEN: Facing board (Default upright posture)
  return {
    category: 'facing_board',
    colorName: 'GREEN',
    border: 'border-emerald-500 bg-emerald-500/15 shadow-emerald-500/20',
    text: 'text-emerald-400 font-semibold',
    badgeBg: 'border-emerald-500/70 bg-slate-900/90 text-emerald-300',
    label: 'Facing board',
    isHand: false,
  }
}"""

new_color_logic = """function getActivityBoxConfig(det: BoundingBox): ActivityBoxConfig {
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
}"""

assert old_color_logic in code, "old_color_logic not found!"
code = code.replace(old_color_logic, new_color_logic)
code = code.replace(
    "colorName: 'GREEN' | 'BLUE' | 'RED' | 'ORANGE' | 'YELLOW'",
    "colorName: 'GREEN' | 'BLUE' | 'RED' | 'ORANGE' | 'YELLOW' | 'GREY'"
)

# 2. Update video metadata and dimension states
old_dims = """  const [videoNativeDims, setVideoNativeDims] = useState<{ width: number; height: number }>({ width: 960, height: 540 })

  const handleVideoLoadedMetadata = () => {
    if (uploadedVideoRef.current) {
      const nw = uploadedVideoRef.current.videoWidth || 960
      const nh = uploadedVideoRef.current.videoHeight || 540
      setVideoNativeDims({ width: nw, height: nh })
    }
  }"""

new_dims = """  const [videoNativeDims, setVideoNativeDims] = useState<{ width: number; height: number }>({ width: 960, height: 540 })
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
  }"""

assert old_dims in code, "old_dims not found!"
code = code.replace(old_dims, new_dims)

# 3. Update activeVideoFrame to never drop boxes when seeking/pausing
old_avf = """    // Max tolerance: 0.40s to avoid stale detections
    if (minDiff > 0.40) {
      return null
    }
    return closest"""

new_avf = """    // Keep the closest sampled frame active when paused or seeking so boxes remain synchronized
    return closest"""

assert old_avf in code, "old_avf not found!"
code = code.replace(old_avf, new_avf)

# 4. Update attachStreamToVideo for webcam aspect ratio
old_attach = """    video.onloadedmetadata = () => {
      setVideoMetadataLoaded(true)
    }"""

new_attach = """    video.onloadedmetadata = () => {
      setVideoMetadataLoaded(true)
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        setMediaAspectRatio(video.videoWidth / video.videoHeight)
      }
    }"""

assert old_attach in code, "old_attach not found!"
code = code.replace(old_attach, new_attach)

# 5. Update stopWebcam to reset aspect ratio if no file
old_stop = """    // 2. Clear video element srcObject and pause
    if (videoRef.current) {
      videoRef.current.srcObject = null
      videoRef.current.pause()
    }"""

new_stop = """    // 2. Clear video element srcObject and pause
    if (videoRef.current) {
      videoRef.current.srcObject = null
      videoRef.current.pause()
    }
    if (!selectedFile) {
      setMediaAspectRatio(16 / 9)
    }"""

assert old_stop in code, "old_stop not found!"
code = code.replace(old_stop, new_stop)

# 6. Update handleFileSelect to reset detections, timeline, time, aspect ratio
old_select = """      setSelectedFile(file)
      setErrorMessage(null)
      setDetectionResult(null)
      setVideoResult(null)"""

new_select = """      setSelectedFile(file)
      setErrorMessage(null)
      setDetectionResult(null)
      setVideoResult(null)
      setCurrentVideoTime(0)
      setActiveCategoryFilter(null)
      setMediaAspectRatio(16 / 9)"""

assert old_select in code, "old_select not found!"
code = code.replace(old_select, new_select)

# 7. Update handleRunSynthetic to reset aspect ratio
old_synth = """      const res = await api.detectSyntheticFrame()
      setDetectionResult(res)
      setVideoResult(null)
      setPreviewUrl(null)
      setPoseResult(null)"""

new_synth = """      const res = await api.detectSyntheticFrame()
      setDetectionResult(res)
      setVideoResult(null)
      setPreviewUrl(null)
      setPoseResult(null)
      setMediaAspectRatio(16 / 9)"""

assert old_synth in code, "old_synth not found!"
code = code.replace(old_synth, new_synth)

# 8. Locate and replace the entire Visualizer area
start_marker = '<div className="relative aspect-video w-full rounded-2xl border border-slate-300 bg-slate-950 overflow-hidden shadow-md flex flex-col justify-between">'
end_marker = '{/* Category Visibility Toggle Filter Bar */}'

pos1 = code.find(start_marker)
pos2 = code.find(end_marker)
assert pos1 != -1 and pos2 != -1, f"Visualizer markers not found: pos1={pos1}, pos2={pos2}"

new_visualizer = """<div
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

            """

code = code[:pos1] + new_visualizer + code[pos2:]

# 9. Update the Activity Filter buttons colors to match Section 3 specification
old_buttons = """                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'head_down' ? null : 'head_down'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'head_down'
                      ? 'bg-amber-600 text-white border-amber-600 shadow-xs ring-2 ring-amber-500/20'
                      : 'bg-amber-50/70 text-amber-800 border-amber-200 hover:bg-amber-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-amber-500" />
                  <span>Head down ({categoryCounts.head_down})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'turned_sideways' ? null : 'turned_sideways'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'turned_sideways'
                      ? 'bg-amber-600 text-white border-amber-600 shadow-xs ring-2 ring-amber-500/20'
                      : 'bg-amber-50/70 text-amber-800 border-amber-200 hover:bg-amber-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-amber-500" />
                  <span>Turned sideways ({categoryCounts.turned_sideways})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategoryFilter((prev) => (prev === 'needs_review' ? null : 'needs_review'))}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    activeCategoryFilter === 'needs_review'
                      ? 'bg-yellow-500 text-slate-900 border-yellow-500 shadow-xs ring-2 ring-yellow-400/20 font-bold'
                      : 'bg-yellow-50/70 text-yellow-800 border-yellow-300 hover:bg-yellow-100/80'
                  }`}
                >
                  <span className="h-2 w-2 rounded-full bg-yellow-400 border border-yellow-500" />
                  <span>Needs review ({categoryCounts.needs_review})</span>
                </button>"""

new_buttons = """                <button
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
                </button>"""

assert old_buttons in code, "old_buttons not found!"
code = code.replace(old_buttons, new_buttons)

if is_crlf:
    code = code.replace("\n", "\r\n")

with open("frontend/src/pages/MonitoringPage.tsx", "w", encoding="utf-8") as f:
    f.write(code)

print("MonitoringPage.tsx successfully patched and saved!")


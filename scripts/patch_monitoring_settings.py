import sys

with open("frontend/src/pages/MonitoringPage.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update initial confidence threshold default from 0.35 to 0.20
content = content.replace(
    "const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.35)",
    "const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.20)"
)

# 2. Update initial serverSideBlurApplied default to false (only active when live)
content = content.replace(
    "const [serverSideBlurApplied, setServerSideBlurApplied] = useState(true)",
    "const [serverSideBlurApplied, setServerSideBlurApplied] = useState(false)"
)

# 3. Do not overwrite user-chosen confidenceThreshold in handleFileChange
content = content.replace(
    "          setConfidenceThreshold(0.20)\n          setDetectPose(true)",
    "          setDetectPose(true)"
)

# 4. In handleRunInference, pass keypointThreshold and elevationMarginPx
old_infer = """        const res = await api.processVideo(
          selectedFile,
          frameSkip,
          confidenceThreshold,
          640,
          detectPose,
          zoneFilteringEnabled ? instructorPolygon : null,
          zoneFilteringEnabled
        )"""

new_infer = """        const res = await api.processVideo(
          selectedFile,
          frameSkip,
          confidenceThreshold,
          640,
          detectPose,
          zoneFilteringEnabled ? instructorPolygon : null,
          zoneFilteringEnabled,
          keypointThreshold,
          elevationMarginPx
        )"""

content = content.replace(old_infer, new_infer)

# 5. In webcam streaming timer: compute interval from frameSkip, send all settings
old_timer = """    const timer = setInterval(async () => {
      if (!isWebcamActive || !videoRef.current || !canvasRef.current) return
      const video = videoRef.current
      const canvas = canvasRef.current

      if (video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) return

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      let clientBlurApplied = false
      if (clientSideBlurActive && detectionResultRef.current?.boxes && detectionResultRef.current.boxes.length > 0) {
        detectionResultRef.current.boxes.forEach((box) => {
          const x = (box.x / 100) * canvas.width
          const y = (box.y / 100) * canvas.height
          const w = (box.width / 100) * canvas.width
          const h = (box.height / 100) * canvas.height

          const rx = Math.max(0, x - w * 0.05)
          const ry = Math.max(0, y - h * 0.02)
          const rw = Math.min(canvas.width - rx, w * 1.1)
          const rh = Math.min(canvas.height - ry, h * 0.28)

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
  }, [isWebcamActive, confidenceThreshold, detectPose, clientSideBlurActive, serverSideBlurActive])"""

new_timer = """    const streamIntervalMs = Math.max(50, Math.min(1000, frameSkip * 33))
    const timer = setInterval(async () => {
      if (!isWebcamActive || !videoRef.current || !canvasRef.current) return
      const video = videoRef.current
      const canvas = canvasRef.current

      if (video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) return

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      let clientBlurApplied = false
      if (clientSideBlurActive && detectionResultRef.current?.boxes && detectionResultRef.current.boxes.length > 0) {
        detectionResultRef.current.boxes.forEach((box) => {
          const x = (box.x / 100) * canvas.width
          const y = (box.y / 100) * canvas.height
          const w = (box.width / 100) * canvas.width
          const h = (box.height / 100) * canvas.height

          const rx = Math.max(0, x - w * 0.05)
          const ry = Math.max(0, y - h * 0.02)
          const rw = Math.min(canvas.width - rx, w * 1.1)
          const rh = Math.min(canvas.height - ry, h * 0.28)

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
            keypointThreshold,
            elevationMarginPx,
            instructorRoiPolygon: zoneFilteringEnabled ? instructorPolygon : null,
            zoneFilteringEnabled,
          })
        )
      }
    }, streamIntervalMs)

    return () => {
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current)
        streamingTimerRef.current = null
      }
    }
  }, [isWebcamActive, confidenceThreshold, detectPose, clientSideBlurActive, serverSideBlurActive, frameSkip, keypointThreshold, elevationMarginPx, instructorPolygon, zoneFilteringEnabled])"""

content = content.replace(old_timer, new_timer)

# 6. Replace hardcoded keypoint confidence thresholds (0.20 and 0.25) with keypointThreshold
content = content.replace("k1.confidence < 0.20 || k2.confidence < 0.20", "k1.confidence < keypointThreshold || k2.confidence < keypointThreshold")
content = content.replace("kp.confidence < 0.20", "kp.confidence < keypointThreshold")
content = content.replace("k1.confidence < 0.25 || k2.confidence < 0.25", "k1.confidence < keypointThreshold || k2.confidence < keypointThreshold")
content = content.replace("kp.confidence < 0.25", "kp.confidence < keypointThreshold")

# 7. Replace blurFaces with (clientSideBlurActive || serverSideBlurActive)
content = content.replace("{blurFaces && (", "{(clientSideBlurActive || serverSideBlurActive) && (")

# 8. In settings checkboxes:
# Teacher Zone Outline should control showZoneOverlay (not zoneFilteringEnabled!)
old_zone_chk = """                <label className="flex items-center justify-between cursor-pointer py-0.5">
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
                </label>"""

new_zone_chk = """                <label className="flex items-center justify-between cursor-pointer py-0.5">
                  <span className="text-slate-700 font-medium">Teacher Zone Outline</span>
                  <input
                    type="checkbox"
                    checked={showZoneOverlay}
                    onChange={(e) => setShowZoneOverlay(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                </label>"""

content = content.replace(old_zone_chk, new_zone_chk)

# 9. Server in-memory blur label: only show (Active) if webcam is streaming and server blur applied
old_server_blur_lbl = """                  <span className="text-slate-700 font-medium">
                    Server In-Memory Blur {serverSideBlurApplied ? '(Active)' : ''}
                  </span>"""

new_server_blur_lbl = """                  <span className="text-slate-700 font-medium">
                    Server In-Memory Blur {isWebcamActive && serverSideBlurActive && serverSideBlurApplied ? '(Active)' : ''}
                  </span>"""

content = content.replace(old_server_blur_lbl, new_server_blur_lbl)

# Client blur label: only show (Active) if webcam is streaming and client blur detected
old_client_blur_lbl = """                  <span className="text-slate-700 font-medium">
                    Client Face Blur {clientSideBlurDetected ? '(Active)' : ''}
                  </span>"""

new_client_blur_lbl = """                  <span className="text-slate-700 font-medium">
                    Client Face Blur {isWebcamActive && clientSideBlurActive && clientSideBlurDetected ? '(Active)' : ''}
                  </span>"""

content = content.replace(old_client_blur_lbl, new_client_blur_lbl)

# Server in-memory blur onChange: if unchecked, clear serverSideBlurApplied immediately
old_server_chk = """                  <input
                    type="checkbox"
                    checked={serverSideBlurActive}
                    onChange={(e) => setServerSideBlurActive(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />"""

new_server_chk = """                  <input
                    type="checkbox"
                    checked={serverSideBlurActive}
                    onChange={(e) => {
                      setServerSideBlurActive(e.target.checked)
                      if (!e.target.checked) setServerSideBlurApplied(false)
                    }}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />"""

content = content.replace(old_server_chk, new_server_chk)

with open("frontend/src/pages/MonitoringPage.tsx", "w", encoding="utf-8") as f:
    f.write(content)

print("MonitoringPage.tsx patched successfully!")


import re

with open("frontend/src/pages/MonitoringPage.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update videoNativeDims and add mediaAspectRatio + handleImageLoad
target1 = """  const [videoNativeDims, setVideoNativeDims] = useState<{ width: number; height: number }>({ width: 960, height: 540 })

  const handleVideoLoadedMetadata = () => {
    if (uploadedVideoRef.current) {
      const nw = uploadedVideoRef.current.videoWidth || 960
      const nh = uploadedVideoRef.current.videoHeight || 540
      setVideoNativeDims({ width: nw, height: nh })
    }
  }"""

replacement1 = """  const [videoNativeDims, setVideoNativeDims] = useState<{ width: number; height: number }>({ width: 960, height: 540 })
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

assert target1 in content.replace("\r\n", "\n"), "Target 1 not found"

# 2. Update attachStreamToVideo to set mediaAspectRatio
target2 = """    video.onloadedmetadata = () => {
      setVideoMetadataLoaded(true)
    }"""

replacement2 = """    video.onloadedmetadata = () => {
      setVideoMetadataLoaded(true)
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        setMediaAspectRatio(video.videoWidth / video.videoHeight)
      }
    }"""

assert target2 in content.replace("\r\n", "\n"), "Target 2 not found"

# 3. Update stopWebcam to reset mediaAspectRatio
target3 = """    // 2. Clear video element srcObject and pause
    if (videoRef.current) {
      videoRef.current.srcObject = null
      videoRef.current.pause()
    }"""

replacement3 = """    // 2. Clear video element srcObject and pause
    if (videoRef.current) {
      videoRef.current.srcObject = null
      videoRef.current.pause()
    }
    if (!selectedFile) {
      setMediaAspectRatio(16 / 9)
    }"""

assert target3 in content.replace("\r\n", "\n"), "Target 3 not found"

# 4. Update handleFileSelect to reset mediaAspectRatio
target4 = """      setSelectedFile(file)
      setErrorMessage(null)
      setDetectionResult(null)
      setVideoResult(null)"""

replacement4 = """      setSelectedFile(file)
      setErrorMessage(null)
      setDetectionResult(null)
      setVideoResult(null)
      setMediaAspectRatio(16 / 9)"""

assert target4 in content.replace("\r\n", "\n"), "Target 4 not found"

# 5. Update handleRunSynthetic to reset mediaAspectRatio
target5 = """      const res = await api.detectSyntheticFrame()
      setDetectionResult(res)
      setVideoResult(null)
      setPreviewUrl(null)
      setPoseResult(null)"""

replacement5 = """      const res = await api.detectSyntheticFrame()
      setDetectionResult(res)
      setVideoResult(null)
      setPreviewUrl(null)
      setPoseResult(null)
      setMediaAspectRatio(16 / 9)"""

assert target5 in content.replace("\r\n", "\n"), "Target 5 not found"

print("All targets 1-5 verified!")

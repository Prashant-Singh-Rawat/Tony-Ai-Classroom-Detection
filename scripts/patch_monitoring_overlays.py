with open("frontend/src/pages/MonitoringPage.tsx", "r", encoding="utf-8") as f:
    src = f.read()

# 1. Uploaded video: gate boxes with showBoxes and filter by confidenceThreshold
old_up_boxes = """                  {/* Synchronized Person Bounding Boxes & Skeletons Over Uploaded Video */}
                  {activeVideoFrame && activeVideoFrame.boxes && activeVideoFrame.boxes.length > 0 && (
                    <div className="absolute inset-0 pointer-events-none">
                      {activeVideoFrame.boxes.map((det: BoundingBox) => {
                        const cfg = getActivityBoxConfig(det)
                        if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                          return null
                        }"""

new_up_boxes = """                  {/* Synchronized Person Bounding Boxes & Skeletons Over Uploaded Video */}
                  {activeVideoFrame && activeVideoFrame.boxes && activeVideoFrame.boxes.length > 0 && (
                    <div className="absolute inset-0 pointer-events-none">
                      {showBoxes && activeVideoFrame.boxes.map((det: BoundingBox) => {
                        if (det.confidence < confidenceThreshold) {
                          return null
                        }
                        const cfg = getActivityBoxConfig(det)
                        if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                          return null
                        }"""

src = src.replace(old_up_boxes, new_up_boxes)

# 2. Uploaded video: Teacher Zone outline should depend on showZoneOverlay
old_up_zone = "{showZoneOverlay && zoneFilteringEnabled && instructorPolygon && ("
new_up_zone = "{showZoneOverlay && instructorPolygon && ("
src = src.replace(old_up_zone, new_up_zone)

# 3. Webcam: gate boxes with showBoxes and filter by confidenceThreshold
old_cam_boxes = """                {/* Bounding Box & Skeleton Overlays on Webcam */}
                {isWebcamActive && detectionResult && detectionResult.boxes && (
                  <div className="absolute inset-0 pointer-events-none">
                    {detectionResult.boxes.map((det) => {
                      const cfg = getActivityBoxConfig(det)
                      if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                        return null
                      }"""

new_cam_boxes = """                {/* Bounding Box & Skeleton Overlays on Webcam */}
                {isWebcamActive && detectionResult && detectionResult.boxes && (
                  <div className="absolute inset-0 pointer-events-none">
                    {showBoxes && detectionResult.boxes.map((det) => {
                      if (det.confidence < confidenceThreshold) {
                        return null
                      }
                      const cfg = getActivityBoxConfig(det)
                      if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                        return null
                      }"""

src = src.replace(old_cam_boxes, new_cam_boxes)

# 4. Add Teacher Zone outline to Webcam container if missing
webcam_zone_snippet = """                {/* Teacher Zone Exclusion Polygon Preview (Webcam) */}
                {isWebcamActive && showZoneOverlay && instructorPolygon && (
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none rounded-lg z-10"
                    viewBox="0 0 100 100"
                    preserveAspectRatio="none"
                  >
                    <polygon
                      points={instructorPolygon.map(([x, y]) => `${x * 100},${y * 100}`).join(' ')}
                      fill="rgba(59, 130, 246, 0.05)"
                      stroke="rgba(59, 130, 246, 0.7)"
                      strokeWidth="1.2"
                      strokeDasharray="4 4"
                    />
                  </svg>
                )}"""

if "{/* Teacher Zone Exclusion Polygon Preview (Webcam) */}" not in src:
    # insert before </div> of webcam container
    marker = "              </div>\n\n              {/* 2. Uploaded Video Display */}"
    src = src.replace(marker, webcam_zone_snippet + "\n              </div>\n\n              {/* 2. Uploaded Video Display */}")

# 5. Image container: gate boxes with showBoxes and filter by confidenceThreshold
old_img_boxes = """                  {detectionResult &&
                    detectionResult.boxes && (
                      <div className="absolute inset-0 pointer-events-none">
                        {detectionResult.boxes.map((det) => {
                          const cfg = getActivityBoxConfig(det)
                          if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                            return null
                          }"""

new_img_boxes = """                  {detectionResult &&
                    detectionResult.boxes && (
                      <div className="absolute inset-0 pointer-events-none">
                        {showBoxes && detectionResult.boxes.map((det) => {
                          if (det.confidence < confidenceThreshold) {
                            return null
                          }
                          const cfg = getActivityBoxConfig(det)
                          if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                            return null
                          }"""

src = src.replace(old_img_boxes, new_img_boxes)

with open("frontend/src/pages/MonitoringPage.tsx", "w", encoding="utf-8") as f:
    f.write(src)

print("MonitoringPage.tsx overlay gating patched successfully!")

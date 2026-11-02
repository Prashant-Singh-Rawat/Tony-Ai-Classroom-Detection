"""
scripts/update_phase_3_frontend_step2.py — Completes Phase 3 UI integration in MonitoringPage.tsx
"""
import re
import sys

target_path = "frontend/src/pages/MonitoringPage.tsx"
with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update webcam box loop
old_webcam_box = """                        {detectionResult.boxes.map((det) => {
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
                              <div className={`absolute -top-6 left-0 flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider rounded-t ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>"""

new_webcam_box = """                        {detectionResult.boxes.map((det) => {
                          const cfg = getActivityBoxConfig(det)
                          if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                            return null
                          }
                          const isNearTop = det.y < 8
                          const chipPosClass = isNearTop ? 'top-1 left-1 rounded' : '-top-6 left-0 rounded-t'

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
                              <div className={`absolute ${chipPosClass} flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>"""

if old_webcam_box in content:
    content = content.replace(old_webcam_box, new_webcam_box, 1)
    print("Updated webcam box loop")
else:
    print("Could not find old_webcam_box")
    sys.exit(1)

# 2. Update webcam skeleton loop
old_webcam_skel = """                        {/* Pose Keypoint & Skeleton Overlay */}
                        {showKeypoints && (
                          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                            {detectionResult.boxes.map((b) => {
                              if (!b.keypoints || b.keypoints.length === 0) return null"""

new_webcam_skel = """                        {/* Pose Keypoint & Skeleton Overlay */}
                        {showKeypoints && (
                          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                            {detectionResult.boxes.map((b) => {
                              if (!b.keypoints || b.keypoints.length === 0) return null
                              if (activeCategoryFilter !== null && getActivityBoxConfig(b).category !== activeCategoryFilter) {
                                return null
                              }"""

if old_webcam_skel in content:
    content = content.replace(old_webcam_skel, new_webcam_skel, 1)
    print("Updated webcam skeleton loop")
else:
    print("Could not find old_webcam_skel")
    sys.exit(1)

# 3. Update uploaded video box loop
old_video_box = """                              {activeVideoFrame.boxes.map((det: BoundingBox) => {
                                const cfg = getActivityBoxConfig(det)
                                const isTeacherZone = det.zoneClassification === 'INSTRUCTOR_ZONE'

                                return (
                                  <div
                                    key={det.id}
                                    className={`absolute border-2 rounded shadow-lg transition-all ${
                                      isTeacherZone ? 'border-amber-500 shadow-amber-500/30' : cfg.border
                                    }`}
                                    style={{
                                      left: `${det.x}%`,
                                      top: `${det.y}%`,
                                      width: `${det.w}%`,
                                      height: `${det.h}%`,
                                    }}
                                  >
                                    <div
                                      className={`absolute -top-6 left-0 flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider rounded-t ${
                                        isTeacherZone ? 'bg-amber-600/90 border-amber-400' : cfg.badgeBg
                                      } border text-white shadow whitespace-nowrap z-20`}
                                    >"""

new_video_box = """                              {activeVideoFrame.boxes.map((det: BoundingBox) => {
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
                                    className={`absolute border-2 rounded shadow-lg transition-all ${
                                      isTeacherZone ? 'border-amber-500 shadow-amber-500/30' : cfg.border
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
                                    >"""

if old_video_box in content:
    content = content.replace(old_video_box, new_video_box, 1)
    print("Updated uploaded video box loop")
else:
    print("Could not find old_video_box")
    sys.exit(1)

# 4. Update uploaded video skeleton loop
old_video_skel = """                                  {activeVideoFrame.boxes.map((b: BoundingBox) => {
                                    if (!b.keypoints || b.keypoints.length === 0) return null"""

new_video_skel = """                                  {activeVideoFrame.boxes.map((b: BoundingBox) => {
                                    if (!b.keypoints || b.keypoints.length === 0) return null
                                    if (activeCategoryFilter !== null && getActivityBoxConfig(b).category !== activeCategoryFilter) {
                                      return null
                                    }"""

if old_video_skel in content:
    content = content.replace(old_video_skel, new_video_skel, 1)
    print("Updated uploaded video skeleton loop")
else:
    print("Could not find old_video_skel")
    sys.exit(1)

# 5. Update uploaded image box loop
old_image_box = """                        {detectionResult &&
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
                                <div className={`absolute -top-6 left-0 flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider rounded-t ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>"""

new_image_box = """                        {detectionResult &&
                          detectionResult.boxes &&
                          detectionResult.boxes.map((det) => {
                            const cfg = getActivityBoxConfig(det)
                            if (activeCategoryFilter !== null && cfg.category !== activeCategoryFilter) {
                              return null
                            }
                            const isNearTop = det.y < 8
                            const chipPosClass = isNearTop ? 'top-1 left-1 rounded' : '-top-6 left-0 rounded-t'

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
                                <div className={`absolute ${chipPosClass} flex items-center gap-1.5 px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider ${cfg.badgeBg} border text-white shadow whitespace-nowrap z-20`}>"""

if old_image_box in content:
    content = content.replace(old_image_box, new_image_box, 1)
    print("Updated uploaded image box loop")
else:
    print("Could not find old_image_box")
    sys.exit(1)

# 6. Update uploaded image skeleton loop
old_image_skel = """                        {showKeypoints && detectionResult && detectionResult.boxes && (
                          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                            {detectionResult.boxes.map((b) => {
                              if (!b.keypoints || b.keypoints.length === 0) return null"""

new_image_skel = """                        {showKeypoints && detectionResult && detectionResult.boxes && (
                          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                            {detectionResult.boxes.map((b) => {
                              if (!b.keypoints || b.keypoints.length === 0) return null
                              if (activeCategoryFilter !== null && getActivityBoxConfig(b).category !== activeCategoryFilter) {
                                return null
                              }"""

if old_image_skel in content:
    content = content.replace(old_image_skel, new_image_skel, 1)
    print("Updated uploaded image skeleton loop")
else:
    print("Could not find old_image_skel")
    sys.exit(1)

# 7. Add Category Visibility Toggle Filter Bar
filter_bar_markup = """            {/* Category Visibility Toggle Filter Bar */}
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
                </button>
              </div>
            </div>\n\n"""

toggles_anchor = "            {/* Viewport Control Toggles */}"
if toggles_anchor in content:
    content = content.replace(toggles_anchor, filter_bar_markup + toggles_anchor, 1)
    print("Added filter_bar_markup")
else:
    print("Could not find toggles_anchor")
    sys.exit(1)

# 8. Update Telemetry Panel with Honest Status Banner
telemetry_anchor = """                <div className="flex items-center gap-1.5">
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

              <div className="space-y-2 text-xs">"""

status_banner_replacement = """                <div className="flex items-center gap-1.5">
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

              <div className="space-y-2 text-xs">"""

if telemetry_anchor in content:
    content = content.replace(telemetry_anchor, status_banner_replacement, 1)
    print("Added status banner in Telemetry")
else:
    print("Could not find telemetry_anchor")
    sys.exit(1)

# 9. Add Observable Activity Labels Legend Card right under Telemetry Card
legend_card = """            {/* Observable Activity Labels Legend Card */}
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
            </div>\n\n"""

source_group_anchor = "            {/* Source Group */}"
if source_group_anchor in content:
    content = content.replace(source_group_anchor, legend_card + source_group_anchor, 1)
    print("Added legend_card before Source Group")
else:
    print("Could not find source_group_anchor")
    sys.exit(1)

with open(target_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("Step 2 completed successfully!")


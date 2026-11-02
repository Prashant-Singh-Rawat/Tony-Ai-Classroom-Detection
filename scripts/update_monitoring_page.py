with open('frontend/src/pages/MonitoringPage.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '/* Right Column: Controls & Hardware Specs (1 Col) */' in line:
        start_idx = i
    if '/* SIMULATED VIEWPORT CANVAS (LEGACY DEMO FALLBACK) */' in line:
        end_idx = i

if start_idx is None or end_idx is None:
    raise ValueError(f"Could not find markers: start={start_idx}, end={end_idx}")

# Line before end_idx - 1 is the </div> closing the grid
# Let's inspect
replacement = """          {/* Right Column: Controls & Information (~30% Col) */}
          <div className="space-y-4">
            {/* Live Information Panel */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span>Telemetry</span>
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                  {isWebcamActive ? 'WEBCAM' : selectedFile ? 'VIDEO FILE' : 'IDLE'}
                </span>
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
                    {isWebcamActive && detectionResult ? detectionResult.count : videoResult ? (activeVideoFrame ? activeVideoFrame.personCount : videoResult.maxPersonsInFrame) : '—'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500 font-medium">Hand-Raise Events</span>
                  <span className="font-bold text-emerald-600 font-mono text-sm">
                    {isWebcamActive && detectionResult ? (detectionResult.handRaisedCount ?? 0) : videoResult ? (activeVideoFrame ? activeVideoFrame.handRaisedCount : (videoResult.totalHandRaises ?? 0)) : '—'}
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
                  <span className="text-slate-700 font-medium">Privacy Face Blur</span>
                  <input
                    type="checkbox"
                    checked={clientSideBlurActive}
                    onChange={(e) => setClientSideBlurActive(e.target.checked)}
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
"""

# start_idx is line index for "/* Right Column: Controls & Hardware Specs (1 Col) */"
# end_idx - 2 is line index for "</div>" closing the grid
new_lines = lines[:start_idx] + [replacement + "\n"] + lines[end_idx-2:]

with open('frontend/src/pages/MonitoringPage.tsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("MonitoringPage updated successfully")


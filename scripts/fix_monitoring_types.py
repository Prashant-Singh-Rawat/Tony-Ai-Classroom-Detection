with open('frontend/src/pages/MonitoringPage.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix icons import
old_icons = """  Sparkles,
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
  Eye,
  ChevronDown,
  Settings,"""

new_icons = """  Camera,
  CameraOff,
  Radio,
  Wifi,
  WifiOff,
  Hand,
  Activity,
  Timer,
  UserCheck,
  RefreshCw,
  Eye,
  ChevronDown,
  Settings,"""

content = content.replace(old_icons, new_icons)

# 2. Fix detectionResult.count -> totalPersons
content = content.replace(
    "isWebcamActive && detectionResult ? detectionResult.count :",
    "isWebcamActive && detectionResult ? detectionResult.totalPersons :"
)

# 3. Fix detectionResult.handRaisedCount -> activeHandRaises
content = content.replace(
    "isWebcamActive && detectionResult ? (detectionResult.handRaisedCount ?? 0) :",
    "isWebcamActive && detectionResult ? (detectionResult.activeHandRaises ?? 0) :"
)

# 4. Integrate persistedEventsCount and dbPersistenceStatus into Telemetry
old_anon = """                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-500 font-medium">Anonymous IDs</span>
                  <span className="font-mono text-[11px] text-slate-600 truncate max-w-[150px]">
                    {isWebcamActive && detectionResult?.boxes?.length ? `${detectionResult.boxes.length} active` : videoResult ? `${videoResult.trackedPersonsCount || 0} tracked` : '—'}
                  </span>
                </div>"""

new_anon = """                <div className="flex items-center justify-between py-1">
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
                </div>"""

content = content.replace(old_anon, new_anon)

# 5. Add synthetic frame button & reset button into Source & Telemetry
old_telemetry_header = """                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                  {isWebcamActive ? 'WEBCAM' : selectedFile ? 'VIDEO FILE' : 'IDLE'}
                </span>"""

new_telemetry_header = """                <div className="flex items-center gap-1.5">
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
                </div>"""

content = content.replace(old_telemetry_header, new_telemetry_header)

old_source_upload = """              {selectedFile && (
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
              )}"""

new_source_upload = """              {selectedFile && (
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

              <button
                type="button"
                onClick={handleRunSyntheticSample}
                disabled={isProcessing}
                className="w-full flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 py-1.5 text-xs font-medium text-slate-700 transition-colors"
              >
                <Cpu className="h-3.5 w-3.5 text-slate-500" />
                <span>Test Sample Frame</span>
              </button>"""

content = content.replace(old_source_upload, new_source_upload)

# 6. Add clientSideBlurDetected and serverSideBlurActive in Display
old_blur_display = """                <label className="flex items-center justify-between cursor-pointer py-0.5">
                  <span className="text-slate-700 font-medium">Privacy Face Blur</span>
                  <input
                    type="checkbox"
                    checked={clientSideBlurActive}
                    onChange={(e) => setClientSideBlurActive(e.target.checked)}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
                  />
                </label>"""

new_blur_display = """                <label className="flex items-center justify-between cursor-pointer py-0.5">
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
                </label>"""

content = content.replace(old_blur_display, new_blur_display)

with open('frontend/src/pages/MonitoringPage.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("MonitoringPage fixes applied.")


// frontend/src/pages/SettingsPage.tsx
import React, { useEffect, useState } from 'react'
import {
  Camera,
  Shield,
  Cpu,
  Server,
  FolderLock,
  EyeOff,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Sliders,
  Radio,
} from 'lucide-react'
import { api } from '../services'
import type { SettingsData, SystemStatus } from '../types'
import { DataStatusBadge } from '../components/DataStatusBadge'

export const SettingsPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [faceBlurSim, setFaceBlurSim] = useState(true)
  const [fpsSetting, setFpsSetting] = useState('15')
  const [resolutionSetting, setResolutionSetting] = useState('1080p')
  const [classroomPreset, setClassroomPreset] = useState('Lecture Hall 302')
  const [lectureDuration, setLectureDuration] = useState('50')
  const [saveToast, setSaveToast] = useState(false)

  useEffect(() => {
    let mounted = true
    Promise.all([api.getSystemStatus(), api.getSettings()]).then(([statusData, settingsData]) => {
      if (mounted) {
        setStatus(statusData)
        setSettings(settingsData)
        setLoading(false)
      }
    })
    return () => {
      mounted = false
    }
  }, [])

  const handleSaveSimulated = (e: React.FormEvent) => {
    e.preventDefault()
    setSaveToast(true)
    setTimeout(() => setSaveToast(false), 4000)
  }

  if (loading || !status || !settings) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <span className="font-mono text-sm">Loading system settings...</span>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Toast Notification */}
      {saveToast && (
        <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3.5 shadow-lg backdrop-blur-md flex items-center justify-between text-xs text-emerald-200">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-400" />
            <span>Settings updated locally (Simulated demonstration state).</span>
          </div>
          <button
            onClick={() => setSaveToast(false)}
            className="text-emerald-400 hover:text-emerald-200 font-bold px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* SECTION 1: CAMERA CONFIGURATION */}
      <section className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <Camera className="h-5 w-5 text-cyan-400" />
            <div>
              <h2 className="text-base font-semibold text-slate-100">Camera & Ingestion Configuration</h2>
              <p className="text-xs text-slate-400">Classroom capture resolution and input pipeline</p>
            </div>
          </div>
          <DataStatusBadge status="NOT CONNECTED" size="sm" tooltip="No physical camera device connected" />
        </div>

        <form onSubmit={handleSaveSimulated} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Video Input Source
              </label>
              <select
                disabled
                value="demo_canvas"
                className="w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2.5 text-xs text-slate-300 opacity-80 cursor-not-allowed"
              >
                <option value="demo_canvas">Simulated Demo Canvas Stream (No hardware camera)</option>
                <option value="rtsp_1">RTSP Stream — Classroom Front Wall (Future Phase)</option>
                <option value="rtsp_2">RTSP Stream — Rear Ceiling Mount (Future Phase)</option>
              </select>
              <p className="mt-1 text-[11px] text-slate-500">
                Hardware camera access is strictly disabled in Phase 0.9.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Target Frame Rate (FPS)
              </label>
              <select
                value={fpsSetting}
                onChange={(e) => setFpsSetting(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
              >
                <option value="10">10 FPS (Low CPU Edge mode)</option>
                <option value="15">15 FPS (Recommended for Hand Gesture Pose)</option>
                <option value="30">30 FPS (Full motion analysis)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Capture Resolution
              </label>
              <select
                value={resolutionSetting}
                onChange={(e) => setResolutionSetting(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
              >
                <option value="720p">1280 x 720 (720p - Lightweight)</option>
                <option value="1080p">1920 x 1080 (1080p - Standard Classroom)</option>
                <option value="1440p">2560 x 1440 (1440p - Deep Lecture Hall)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Hardware Connection State
              </label>
              <div className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-700 bg-slate-900 text-xs text-slate-400">
                <Radio className="h-4 w-4 text-slate-500" />
                <span>Camera Stream Offline / Not Connected</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 px-4 py-2 text-xs font-medium text-slate-200 transition-colors"
            >
              <Sliders className="h-3.5 w-3.5 text-cyan-400" />
              <span>Save Stream Preferences (Demo)</span>
            </button>
          </div>
        </form>
      </section>

      {/* SECTION 2: CLASSROOM & SESSION SETTINGS */}
      <section className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <Sliders className="h-5 w-5 text-violet-400" />
            <div>
              <h2 className="text-base font-semibold text-slate-100">Classroom & Session Presets</h2>
              <p className="text-xs text-slate-400">Default hall identifiers and lecture scheduling parameters</p>
            </div>
          </div>
          <DataStatusBadge status="DEMO DATA" size="xs" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Default Classroom Location
            </label>
            <input
              type="text"
              value={classroomPreset}
              onChange={(e) => setClassroomPreset(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2 text-xs text-slate-200 focus:border-violet-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Default Session Duration (Minutes)
            </label>
            <input
              type="number"
              value={lectureDuration}
              onChange={(e) => setLectureDuration(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2 text-xs text-slate-200 focus:border-violet-500 focus:outline-none"
            />
          </div>
        </div>
      </section>

      {/* SECTION 3: PRIVACY & DATA ISOLATION SETTINGS */}
      <section className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <Shield className="h-5 w-5 text-emerald-400" />
            <div>
              <h2 className="text-base font-semibold text-slate-100">Privacy & Data Isolation Controls</h2>
              <p className="text-xs text-slate-400">Strict offline compliance and student privacy safeguards</p>
            </div>
          </div>
          <DataStatusBadge status="REAL" size="sm" />
        </div>

        {/* OneDrive Isolation Warning */}
        <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <h3 className="text-xs font-semibold text-amber-200">
                MANDATORY DATA STORAGE ISOLATION (ONEDRIVE WARNING)
              </h3>
              <p className="text-xs text-amber-300/80 leading-relaxed">
                The repository is located within an active OneDrive folder. To prevent unauthorized cloud
                synchronization of student faces or classroom footage, all raw footage MUST be stored in
                an external directory configured via <code className="font-mono text-amber-200">CLASSVISION_REAL_DATA_ROOT</code> (e.g.{' '}
                <code className="font-mono text-amber-200">{settings.privacy.storageRoot}</code>).
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center gap-3">
              <EyeOff className="h-5 w-5 text-emerald-400" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">
                  Simulated Face-Blurring Filter
                </h4>
                <p className="text-[11px] text-slate-400">
                  Gaussian blur overlay applied to facial regions prior to gesture classification.
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={faceBlurSim}
                onChange={(e) => setFaceBlurSim(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-10 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600"></div>
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 mb-1">
                <FolderLock className="h-4 w-4 text-violet-400" />
                <span className="text-xs font-semibold text-slate-200">Configured Data Root</span>
              </div>
              <p className="text-xs font-mono text-slate-300 break-all">{settings.privacy.storageRoot}</p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 mb-1">
                <HelpCircle className="h-4 w-4 text-cyan-400" />
                <span className="text-xs font-semibold text-slate-200">Biometric Safeguard</span>
              </div>
              <p className="text-xs text-slate-300">
                Zero facial embeddings, biometric hashes, or student identifiers stored.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: AI MODULE STATUS */}
      <section className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <Cpu className="h-5 w-5 text-violet-400" />
            <div>
              <h2 className="text-base font-semibold text-slate-100">AI Module & Inference Pipeline Status</h2>
              <p className="text-xs text-slate-400">Readiness of multimodal neural networks and speech engines</p>
            </div>
          </div>
          <DataStatusBadge status="NOT CONNECTED" size="sm" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">Person & Hand-Raise Detection</span>
              <span className="text-[11px] text-slate-400">{settings.aiModules.visionInference}</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">Whisper Speech Audio</span>
              <span className="text-[11px] text-slate-400">{settings.aiModules.whisperTranscription}</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">Blackboard OCR Engine</span>
              <span className="text-[11px] text-slate-400">{settings.aiModules.easyOcr}</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">RAG Query Assistant</span>
              <span className="text-[11px] text-slate-400">{settings.aiModules.ragAssistant}</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>
        </div>
      </section>

      {/* SECTION 5: APPLICATION INFORMATION */}
      <section className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <Server className="h-5 w-5 text-slate-400" />
            <div>
              <h2 className="text-base font-semibold text-slate-100">Application Information</h2>
              <p className="text-xs text-slate-400">Runtime environment, build version and offline verification</p>
            </div>
          </div>
          <span className="font-mono text-xs text-slate-400">v{settings.system.version}</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase">Frontend</span>
            <div className="text-slate-200 font-semibold">React 19 + Vite</div>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase">Styling</span>
            <div className="text-slate-200 font-semibold">Tailwind CSS v4</div>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase">API Layer</span>
            <div className="text-amber-400 font-semibold">Demo Layer Active</div>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase">Telemetry</span>
            <div className="text-emerald-400 font-semibold">0 External Calls (Offline)</div>
          </div>
        </div>
      </section>
    </div>
  )
}

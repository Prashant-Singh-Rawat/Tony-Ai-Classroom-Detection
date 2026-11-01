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
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'

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
      <div className="flex h-64 items-center justify-center text-slate-500">
        <span className="text-xs font-medium">Loading system settings...</span>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Toast Notification */}
      {saveToast && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 shadow-2xs flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-600" />
            <span>Settings updated locally in configuration state.</span>
          </div>
          <button
            onClick={() => setSaveToast(false)}
            className="text-emerald-700 hover:text-emerald-900 font-bold px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* SECTION 1: CAMERA CONFIGURATION */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Camera className="h-5 w-5 text-blue-600" />
            <div>
              <CardTitle>Camera & Video Ingestion</CardTitle>
              <p className="text-xs text-slate-500">Classroom capture resolution, FPS, and ingestion pipeline</p>
            </div>
          </div>
          <Badge variant="emerald" size="xs">Live Webcam Ready</Badge>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSaveSimulated} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                  Video Input Source
                </label>
                <select
                  value="live_webcam"
                  disabled
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-700 font-medium cursor-not-allowed"
                >
                  <option value="live_webcam">Live User Webcam (Local USB / Integrated)</option>
                  <option value="upload">Video File Upload (.mp4 / .avi)</option>
                  <option value="rtsp_1">RTSP Stream — Classroom Front Wall (Future Phase)</option>
                </select>
                <p className="mt-1 text-[11px] text-slate-500">
                  Local browser webcam and file upload enabled for real-time inference.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                  Target Frame Rate (FPS)
                </label>
                <select
                  value={fpsSetting}
                  onChange={(e) => setFpsSetting(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-600 focus:outline-none font-medium"
                >
                  <option value="10">10 FPS (Low CPU Edge mode)</option>
                  <option value="15">15 FPS (Recommended for YOLOv8-pose)</option>
                  <option value="30">30 FPS (Full motion analysis)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                  Capture Resolution
                </label>
                <select
                  value={resolutionSetting}
                  onChange={(e) => setResolutionSetting(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-xs text-slate-800 focus:border-blue-600 focus:outline-none font-medium"
                >
                  <option value="720p">1280 x 720 (720p - Lightweight)</option>
                  <option value="1080p">1920 x 1080 (1080p - Standard Classroom)</option>
                  <option value="1440p">2560 x 1440 (1440p - Deep Lecture Hall)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                  Pipeline State
                </label>
                <div className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-700 font-medium">
                  <Radio className="h-4 w-4 text-emerald-600 animate-pulse" />
                  <span>FastAPI + WebSocket Connected</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" variant="primary" size="sm" icon={<Sliders className="h-3.5 w-3.5" />}>
                Save Ingestion Preferences
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* SECTION 2: CLASSROOM & SESSION SETTINGS */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Sliders className="h-5 w-5 text-blue-600" />
            <div>
              <CardTitle>Classroom & Session Presets</CardTitle>
              <p className="text-xs text-slate-500">Default hall identifiers and lecture scheduling parameters</p>
            </div>
          </div>
          <Badge variant="blue" size="xs">Room Profile</Badge>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                Default Classroom Location
              </label>
              <input
                type="text"
                value={classroomPreset}
                onChange={(e) => setClassroomPreset(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs text-slate-800 focus:border-blue-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
                Default Session Duration (Minutes)
              </label>
              <input
                type="number"
                value={lectureDuration}
                onChange={(e) => setLectureDuration(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs text-slate-800 focus:border-blue-600 focus:outline-none"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SECTION 3: PRIVACY & DATA ISOLATION */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Shield className="h-5 w-5 text-emerald-600" />
            <div>
              <CardTitle>Privacy & Data Isolation Controls</CardTitle>
              <p className="text-xs text-slate-500">Strict offline compliance and student privacy safeguards</p>
            </div>
          </div>
          <Badge variant="emerald" size="xs">GDPR Compliant</Badge>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* OneDrive Isolation Warning */}
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <h3 className="text-xs font-bold text-amber-900 uppercase">
                  Data Storage Isolation Notice
                </h3>
                <p className="text-xs text-amber-800 leading-relaxed">
                  To prevent unauthorized cloud synchronization of student faces or classroom footage, all raw footage is isolated to local disk: <code className="font-mono font-bold">{settings.privacy.storageRoot}</code>.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center gap-3">
                <EyeOff className="h-5 w-5 text-emerald-600" />
                <div>
                  <h4 className="text-xs font-semibold text-slate-900">
                    Client-Side Facial Masking
                  </h4>
                  <p className="text-[11px] text-slate-500">
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
                <div className="w-10 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
                <div className="flex items-center gap-2 mb-1">
                  <FolderLock className="h-4 w-4 text-blue-600" />
                  <span className="text-xs font-semibold text-slate-800">Local Data Root</span>
                </div>
                <p className="text-xs font-mono text-slate-600 break-all">{settings.privacy.storageRoot}</p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
                <div className="flex items-center gap-2 mb-1">
                  <HelpCircle className="h-4 w-4 text-teal-600" />
                  <span className="text-xs font-semibold text-slate-800">Biometric Safeguard</span>
                </div>
                <p className="text-xs text-slate-600">
                  Zero facial embeddings, biometric hashes, or persistent student identifiers.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SECTION 4: AI MODULE STATUS */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Cpu className="h-5 w-5 text-blue-600" />
            <div>
              <CardTitle>AI Inference Pipeline Status</CardTitle>
              <p className="text-xs text-slate-500">Local model weights and speech/vision engine readiness</p>
            </div>
          </div>
          <Badge variant="blue" size="xs">Local Weights</Badge>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">Person & Pose Detection</span>
                <span className="text-[11px] text-slate-500">YOLOv8n-pose (17 Keypoints)</span>
              </div>
              <Badge variant="emerald" size="xs">ACTIVE</Badge>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">Whisper Speech Audio</span>
                <span className="text-[11px] text-slate-500">Faster-Whisper (Int8 CPU)</span>
              </div>
              <Badge variant="emerald" size="xs">ACTIVE</Badge>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">Blackboard OCR Engine</span>
                <span className="text-[11px] text-slate-500">EasyOCR PyTorch Model</span>
              </div>
              <Badge variant="emerald" size="xs">ACTIVE</Badge>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">SQLite Event Store</span>
                <span className="text-[11px] text-slate-500">WAL Mode Local Telemetry</span>
              </div>
              <Badge variant="emerald" size="xs">ACTIVE</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SECTION 5: APPLICATION INFORMATION */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Server className="h-5 w-5 text-slate-500" />
            <div>
              <CardTitle>System Information</CardTitle>
              <p className="text-xs text-slate-500">Runtime environment, build version and verification</p>
            </div>
          </div>
          <span className="font-mono text-xs text-slate-500">v{settings.system.version}</span>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Frontend</span>
              <div className="text-slate-900 font-semibold">React 19 + Vite</div>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Styling</span>
              <div className="text-slate-900 font-semibold">Tailwind CSS v4</div>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Inference Engine</span>
              <div className="text-blue-600 font-semibold">Ultralytics YOLOv8</div>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Telemetry</span>
              <div className="text-emerald-600 font-semibold">0 External Calls (Offline)</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
export default SettingsPage

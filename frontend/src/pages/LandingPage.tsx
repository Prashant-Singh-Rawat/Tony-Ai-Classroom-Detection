// frontend/src/pages/LandingPage.tsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  GraduationCap,
  ShieldCheck,
  ArrowRight,
  Video,
  FileSpreadsheet,
  Brain,
  CheckCircle2,
  Sparkles,
  BookOpen,
  Activity,
} from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'

export const LandingPage: React.FC = () => {
  const navigate = useNavigate()
  const [role, setRole] = useState<'instructor' | 'admin' | 'observer'>('instructor')

  const handleEnter = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen w-screen bg-slate-50 text-slate-800 flex flex-col justify-between font-sans antialiased">
      {/* Top Navigation */}
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur px-8 py-3.5 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-slate-900">ClassVision AI</span>
              <Badge variant="blue" size="xs">Institutional</Badge>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Multimodal Classroom Intelligence Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="emerald" size="sm" dot>System Online</Badge>
          <Button variant="primary" size="sm" onClick={() => navigate('/dashboard')}>
            Launch App
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-6 lg:px-12 py-16 flex flex-col gap-16">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-16">
          {/* Left: Value Proposition */}
          <div className="flex-1 space-y-6 text-left max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50/80 px-3 py-1 text-xs text-blue-700 font-medium">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Next-Generation Lecture Telemetry &amp; Video Intelligence</span>
            </div>

            <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
              Understand Every Classroom,{' '}
              <span className="text-blue-600">
                Intelligently &amp; Privately.
              </span>
            </h1>

            <p className="text-slate-600 text-base lg:text-lg leading-relaxed">
              ClassVision AI bridges computer vision and classroom pedagogy. Powered by local{' '}
              <strong> YOLOv8-pose</strong> estimation, <strong>Faster-Whisper</strong> transcription, and <strong>EasyOCR</strong> blackboard analysis — strictly engineered with offline-edge privacy and zero biometric facial recognition.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 w-fit">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900">Privacy-First Architecture</h3>
                <p className="text-xs text-slate-500 leading-normal">
                  Anonymized body-pose keypoints. No facial biometrics stored, transmitted, or inferred.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-2">
                <div className="p-2 rounded-lg bg-blue-50 text-blue-600 w-fit">
                  <Brain className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900">Multimodal Analytics</h3>
                <p className="text-xs text-slate-500 leading-normal">
                  Correlate student engagement and hand-raises with spoken lecture concepts and slide notes.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6 pt-4 text-xs text-slate-500 font-medium">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                <span>Edge GPU / CPU Ready</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                <span>Full Offline Execution</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                <span>Open Evaluation Datasets</span>
              </div>
            </div>
          </div>

          {/* Right: Portal Access Card */}
          <div className="w-full max-w-md">
            <Card className="shadow-lg border-slate-200 overflow-hidden">
              <div className="p-6 border-b border-slate-100 bg-slate-50/50">
                <h2 className="text-base font-bold text-slate-900">Institutional Access</h2>
                <p className="text-xs text-slate-500 mt-0.5">Select session role to enter the intelligence console</p>
              </div>

              <div className="p-6 space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Session Role
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: 'instructor', label: 'Instructor' },
                      { id: 'admin', label: 'Academic Lead' },
                      { id: 'observer', label: 'Evaluator' },
                    ].map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setRole(item.id as any)}
                        className={`py-2 px-2 text-xs font-medium rounded-lg border text-center transition-all ${
                          role === item.id
                            ? 'bg-blue-50 border-blue-600 text-blue-700 shadow-2xs font-semibold'
                            : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Observer Account
                  </label>
                  <input
                    type="email"
                    disabled
                    value="academic.evaluator@institution.edu"
                    aria-label="Observer Account"
                    className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-600 font-mono"
                  />
                  <p className="text-[11px] text-slate-400">Pre-authenticated local session</p>
                </div>

                <form onSubmit={handleEnter} className="pt-2">
                  <Button variant="primary" size="lg" className="w-full" icon={<ArrowRight className="h-4 w-4" />}>
                    Enter Classroom Console
                  </Button>
                </form>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="flex items-center gap-1">
                    <Video className="h-3.5 w-3.5 text-blue-600" />
                    YOLOv8 Pose Active
                  </span>
                  <span className="flex items-center gap-1">
                    <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />
                    SQLite Session DB
                  </span>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* ── Two Workflow Cards ───────────────────────────────────────────── */}
        <div>
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Choose Your Analysis Mode</h2>
            <p className="text-sm text-slate-500 mt-1">
              Two independent video analysis workflows tailored for your classroom needs.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1 — Classroom Activity Detection */}
            <div className="group relative flex flex-col rounded-2xl border border-slate-200 bg-white shadow-xs hover:shadow-md hover:border-blue-200 transition-all overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-1 bg-blue-600 rounded-t-2xl" />
              <div className="p-6 flex flex-col flex-1 gap-4">
                <div className="flex items-start justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                    <Activity className="h-6 w-6" />
                  </div>
                  <Badge variant="blue" size="xs">Live</Badge>
                </div>

                <div className="space-y-2">
                  <h3 className="text-base font-bold text-slate-900">
                    Classroom Activity &amp; Gesture Detection
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Analyze classroom videos to detect individual people, body poses, hand raises and
                    observable classroom activities. Powered by YOLOv8 pose estimation with real-time
                    bounding boxes, 17-keypoint skeleton tracking, and activity classification.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 mt-1">
                  {['Person Detection', 'Pose Estimation', 'Hand Raises', 'Activity Labels', 'Privacy Blur'].map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-blue-50 border border-blue-100 px-2.5 py-0.5 text-[11px] font-medium text-blue-700"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="mt-auto pt-4">
                  <Button
                    variant="primary"
                    size="md"
                    className="w-full"
                    icon={<ArrowRight className="h-4 w-4" />}
                    onClick={() => navigate('/live')}
                  >
                    Upload Video &amp; Analyze Activity
                  </Button>
                </div>
              </div>
            </div>

            {/* Card 2 — AI Lecture Notes */}
            <div className="group relative flex flex-col rounded-2xl border border-slate-200 bg-white shadow-xs hover:shadow-md hover:border-violet-200 transition-all overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-1 bg-violet-500 rounded-t-2xl" />
              <div className="p-6 flex flex-col flex-1 gap-4">
                <div className="flex items-start justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
                    <BookOpen className="h-6 w-6" />
                  </div>
                  <Badge variant="blue" size="xs">Phase 2</Badge>
                </div>

                <div className="space-y-2">
                  <h3 className="text-base font-bold text-slate-900">
                    AI Lecture Notes &amp; Summary
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Upload a classroom lecture video to extract teacher explanations, presentation slides,
                    board content, topics and important concepts. Automatically generate organized study
                    notes and summaries using Faster-Whisper and EasyOCR.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 mt-1">
                  {['Audio Transcription', 'Slide OCR', 'Topic Extraction', 'Study Notes', 'PDF Export'].map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-violet-50 border border-violet-100 px-2.5 py-0.5 text-[11px] font-medium text-violet-700"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="mt-auto pt-4">
                  <Button
                    variant="outline"
                    size="md"
                    className="w-full border-violet-200 text-violet-700 hover:bg-violet-50"
                    icon={<ArrowRight className="h-4 w-4" />}
                    onClick={() => navigate('/lecture-notes')}
                  >
                    Upload Lecture Video &amp; Generate Notes
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white px-8 py-5 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>ClassVision AI • Multimodal Classroom Perception &amp; Telemetry System</span>
          <span className="font-mono text-[11px]">Edge Inference • No Cloud Uploads • GDPR Compliant Design</span>
        </div>
      </footer>
    </div>
  )
}
export default LandingPage

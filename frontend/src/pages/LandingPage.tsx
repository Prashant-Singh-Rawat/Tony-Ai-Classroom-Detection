// frontend/src/pages/LandingPage.tsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GraduationCap, ShieldCheck, ArrowRight, Lock, EyeOff, Cpu, BookOpen } from 'lucide-react'
import { DataStatusBadge } from '../components/DataStatusBadge'

export const LandingPage: React.FC = () => {
  const navigate = useNavigate()
  const [role, setRole] = useState<'instructor' | 'admin' | 'observer'>('instructor')
  const [email, setEmail] = useState('demo.instructor@college.edu')

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    // Simulated authentication bypass for Phase 0.8 demo
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen w-screen bg-[#07090e] text-slate-100 flex flex-col justify-between font-sans">
      {/* Top Banner */}
      <header className="border-b border-slate-800/80 bg-[#0d101a]/80 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-violet-600 to-cyan-500 text-white shadow-lg shadow-violet-950/40">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white">ClassVision AI</span>
              <span className="rounded bg-violet-500/20 px-2 py-0.5 text-xs font-semibold text-violet-300 border border-violet-500/30">
                Phase 0.9 Foundation
              </span>
            </div>
            <p className="text-xs text-slate-400">AI-Powered Classroom Intelligence</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <DataStatusBadge status="DEMO DATA" size="sm" />
          <span className="text-xs text-slate-400 hidden sm:inline-block">Offline Architecture Prototype</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:flex-row items-center justify-center px-6 lg:px-16 py-12 gap-12 max-w-7xl mx-auto">
        {/* Left: Product summary & highlights */}
        <div className="flex-1 space-y-6 text-left max-w-xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-3.5 py-1 text-xs text-violet-300 font-medium">
            <Cpu className="h-3.5 w-3.5" />
            <span>Final-Year B.Tech Capstone Project • Phase 0.9</span>
          </div>

          <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
            AI-Powered Classroom Intelligence with{' '}
            <span className="bg-gradient-to-r from-violet-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
              Privacy by Design
            </span>
          </h1>

          <p className="text-slate-300 text-sm lg:text-base leading-relaxed">
            Multimodal architecture integrating <strong>Computer Vision</strong> (planned pose & hand-raise detection), <strong>Speech</strong> (planned offline Whisper transcription), <strong>OCR</strong> (planned blackboard extraction), and <strong>RAG</strong> (grounded query answering) — designed strictly with zero biometric tracking and local offline execution.
          </p>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <ShieldCheck className="h-5 w-5 text-cyan-400 mb-2" />
              <h4 className="text-sm font-semibold text-white">100% Privacy Guard</h4>
              <p className="text-xs text-slate-400 mt-1">Edge blurring, no facial recognition, zero cloud synchronization.</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <BookOpen className="h-5 w-5 text-violet-400 mb-2" />
              <h4 className="text-sm font-semibold text-white">Multimodal Fusion (Planned)</h4>
              <p className="text-xs text-slate-400 mt-1">Correlates raised hands directly with spoken lectures and slide notes.</p>
            </div>
          </div>
        </div>

        {/* Right: Demo Login Card */}
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0e121d]/90 p-8 shadow-2xl backdrop-blur relative overflow-hidden">
          <div className="absolute top-0 right-0 left-0 h-1 bg-gradient-to-r from-violet-500 via-cyan-500 to-emerald-500" />

          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-lg font-bold text-white">Access Dashboard</h3>
              <p className="text-xs text-slate-400">Interactive Phase 0.8 prototype</p>
            </div>
            <DataStatusBadge status="DEMO DATA" size="sm" />
          </div>

          {/* Explicit Demo Login Note */}
          <div className="my-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
            <p className="font-semibold flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5" />
              Demo login only — no real accounts or credentials stored.
            </p>
            <p className="text-[11px] text-amber-300/80 mt-1">
              Select any role below to explore the dashboard with verified demo telemetry.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Simulated User Role
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'instructor', label: 'Lecturer' },
                  { id: 'admin', label: 'Admin' },
                  { id: 'observer', label: 'Observer' },
                ].map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setRole(r.id as any)}
                    className={`px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
                      role === r.id
                        ? 'border-violet-500 bg-violet-600/20 text-violet-300'
                        : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:bg-slate-800'
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Institutional Email (Preset)
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                placeholder="instructor@institution.edu"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Session Access Token (Placeholder)
              </label>
              <div className="relative">
                <input
                  type="password"
                  value="demo-token-phase-0.8"
                  readOnly
                  className="w-full rounded-lg border border-slate-800 bg-slate-900/80 px-3.5 py-2.5 text-sm text-slate-400 focus:outline-none cursor-not-allowed"
                />
                <EyeOff className="h-4 w-4 absolute right-3 top-3 text-slate-500" />
              </div>
            </div>

            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-600 py-3 text-sm font-bold text-white shadow-lg shadow-violet-950/50 hover:brightness-110 active:brightness-95 transition-all mt-4"
            >
              <span>Enter ClassVision Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#07090e] px-6 py-4 text-center text-xs text-slate-500">
        ClassVision AI — Real-Time Multimodal Classroom Intelligence System &bull; B.Tech Capstone Project &bull; Offline Architecture
      </footer>
    </div>
  )
}

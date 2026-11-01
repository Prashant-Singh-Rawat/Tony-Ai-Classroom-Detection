// frontend/src/pages/DashboardPage.tsx
import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Users,
  Hand,
  TrendingUp,
  ShieldCheck,
  Video,
  ChevronRight,
  Clock,
  Calendar,
  Sparkles,
} from 'lucide-react'
import { api } from '../services'
import type { DashboardSummary } from '../types'
import { MetricCard } from '../components/MetricCard'
import { DemoBadge } from '../components/DemoBadge'
import { DataStatusBadge } from '../components/DataStatusBadge'
import { TrendLineChart } from '../components/Charts'

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch data strictly via service layer
    // TODO(backend): Real backend integration will connect via WebSocket or REST polling
    api.getDashboardSummary().then((summary) => {
      setData(summary)
      setLoading(false)
    })
  }, [])

  if (loading || !data) {
    return <div className="text-slate-400 p-8">Loading dashboard telemetry...</div>
  }

  const { currentSession, stats, recentSessions, activityTimeline } = data

  return (
    <div className="space-y-6">
      {/* Top Session Spotlight Banner */}
      {currentSession && (
        <div className="relative overflow-hidden rounded-2xl border border-violet-500/30 bg-gradient-to-r from-violet-950/40 via-slate-900/60 to-cyan-950/40 p-6 backdrop-blur shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2.5">
                <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping" />
                <span className="rounded-md bg-emerald-500/20 px-2.5 py-0.5 text-xs font-semibold text-emerald-300 border border-emerald-500/30">
                  LIVE SESSION ACTIVE
                </span>
                <DemoBadge size="sm" />
              </div>
              <h2 className="text-xl lg:text-2xl font-bold text-white tracking-tight">
                {currentSession.title}
              </h2>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-1">
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-violet-400" />
                  {currentSession.date}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-cyan-400" />
                  Started {currentSession.startTime} ({currentSession.durationMinutes} min)
                </span>
                <span>Room: <strong className="text-white">{currentSession.classroom}</strong></span>
                <span>Instructor: <strong className="text-white">{currentSession.instructor}</strong></span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link
                to="/monitoring"
                className="flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-violet-950/50 hover:bg-violet-500 transition-colors"
              >
                <Video className="h-4 w-4" />
                <span>Open Video Feed</span>
              </Link>
              <Link
                to="/intelligence"
                className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-xs font-bold text-slate-200 hover:bg-slate-700 transition-colors"
              >
                <Sparkles className="h-4 w-4 text-cyan-400" />
                <span>Lecture Notes</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total People Detected"
          value={stats.totalPeopleDetected}
          subtext="Person-level upper body boxes"
          icon={Users}
          trend="+3"
          trendType="positive"
          accentColor="cyan"
        />
        <MetricCard
          label="Active Hand Raises"
          value={stats.activeHandRaises}
          subtext="Current students signaling"
          icon={Hand}
          trend="+2"
          trendType="positive"
          accentColor="violet"
        />
        <MetricCard
          label="Participation Ratio"
          value={`${stats.handRaisePercentage}%`}
          subtext="Students raising hands"
          icon={TrendingUp}
          trend="Above Avg"
          trendType="positive"
          accentColor="emerald"
        />
        <MetricCard
          label="Privacy Status"
          value="Edge Blurring"
          subtext="No facial identity data"
          icon={ShieldCheck}
          trend="Strict Offline"
          trendType="neutral"
          accentColor="amber"
        />
      </div>

      {/* System & Model Status Quick Strip */}
      <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-4 backdrop-blur shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-600/10 text-violet-400 border border-violet-500/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-200">Repository & Model Status:</span>
              <span className="font-mono text-xs text-amber-300 font-bold">0 Checkpoints (No Model Trained)</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Verified Kaggle dataset (24,000 images, 20 classes) • Real classroom collection starts post 12 October 2026.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <DataStatusBadge status="REAL" size="sm" />
          <DataStatusBadge status="NOT CONNECTED" size="sm" tooltip="ML Inference backend not connected" />
          <Link
            to="/model-status"
            className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 ml-1 inline-flex items-center gap-1"
          >
            <span>Full Audit</span>
            <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
      </div>
      <div className="rounded-2xl border border-slate-800/90 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Hand-Raise Gesture Timeline</h3>
              <DemoBadge size="sm" />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Cumulative and concurrent hand raises over lecture duration
            </p>
          </div>
          <Link
            to="/analytics"
            className="flex items-center gap-1 text-xs font-medium text-violet-400 hover:text-violet-300"
          >
            <span>Full Analytics</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="pt-2">
          <TrendLineChart data={activityTimeline} height={200} />
        </div>
      </div>

      {/* Recent Sessions Table */}
      <div className="rounded-2xl border border-slate-800/90 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Recorded Class Sessions</h3>
              <DemoBadge size="sm" />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Historical lecture recordings and aggregated engagement statistics
            </p>
          </div>
          <Link
            to="/reports"
            className="flex items-center gap-1 text-xs font-medium text-cyan-400 hover:text-cyan-300"
          >
            <span>View Reports</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/60 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Session ID</th>
                <th className="py-3 px-4">Course & Title</th>
                <th className="py-3 px-4">Classroom</th>
                <th className="py-3 px-4">Date & Time</th>
                <th className="py-3 px-4">Students</th>
                <th className="py-3 px-4">Hand Raises</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {recentSessions.map((s) => (
                <tr key={s.sessionId} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-violet-400">{s.sessionId}</td>
                  <td className="py-3 px-4">
                    <span className="font-semibold text-white">{s.courseCode}:</span> {s.title.split(': ')[1] || s.title}
                  </td>
                  <td className="py-3 px-4 text-slate-400">{s.classroom}</td>
                  <td className="py-3 px-4 text-slate-400">
                    {s.date} <span className="text-[10px] text-slate-500">({s.startTime})</span>
                  </td>
                  <td className="py-3 px-4 font-bold text-white">{s.totalStudents}</td>
                  <td className="py-3 px-4">
                    <span className="rounded bg-violet-500/20 px-2 py-0.5 font-bold text-violet-300 border border-violet-500/30">
                      {s.totalHandRaiseEvents} events
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold border ${
                        s.status === 'active'
                          ? 'border-emerald-500/30 bg-emerald-500/20 text-emerald-300'
                          : 'border-slate-700 bg-slate-800 text-slate-300'
                      }`}
                    >
                      {s.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <Link
                      to="/intelligence"
                      className="text-violet-400 hover:text-violet-300 font-semibold"
                    >
                      Intel &rarr;
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

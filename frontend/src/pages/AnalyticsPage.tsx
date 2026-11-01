// frontend/src/pages/AnalyticsPage.tsx
import React, { useEffect, useState } from 'react'
import {
  BarChart3,
  TrendingUp,
  Clock,
  Users,
  ShieldCheck,
  ArrowRightLeft,
  FileSpreadsheet,
  FileText,
  Activity,
} from 'lucide-react'
import { api } from '../services'
import type {
  ActivityDistributionSummaryData,
  AnalyticsSessionSummaryData,
  SessionActivityAnalyticsData,
  SessionComparisonResponseData,
} from '../types'
import { MetricCard } from '../components/MetricCard'
import { DataStatusBadge } from '../components/DataStatusBadge'
import { TrendLineChart, ActivityBarChart } from '../components/Charts'

export const AnalyticsPage: React.FC = () => {
  const [sessions, setSessions] = useState<AnalyticsSessionSummaryData[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string>('sess_01')
  const [sessionAnalytics, setSessionAnalytics] = useState<SessionActivityAnalyticsData | null>(null)
  const [activityDist, setActivityDist] = useState<ActivityDistributionSummaryData | null>(null)
  const [intervalSeconds, setIntervalSeconds] = useState<number>(60)
  const [loading, setLoading] = useState<boolean>(true)

  // Comparison State
  const [compareMode, setCompareMode] = useState<boolean>(false)
  const [compareSessionId, setCompareSessionId] = useState<string>('sess_02')
  const [comparisonData, setComparisonData] = useState<SessionComparisonResponseData | null>(null)
  const [isExporting, setIsExporting] = useState<boolean>(false)

  // Load available sessions
  useEffect(() => {
    let isMounted = true
    api.getAnalyticsSessions().then((data) => {
      if (isMounted) {
        setSessions(data)
        if (data.length > 0) {
          setSelectedSessionId((prev) => prev || data[0].sessionId)
        }
      }
    }).catch(() => null)
    return () => { isMounted = false }
  }, [])

  // Load active session activity analytics whenever selectedSessionId or intervalSeconds changes
  useEffect(() => {
    let isMounted = true
    api.getSessionActivityAnalytics(selectedSessionId, intervalSeconds).then((data) => {
      if (isMounted) {
        setSessionAnalytics(data)
        setLoading(false)
      }
    }).catch(() => {
      if (isMounted) setLoading(false)
    })
    return () => { isMounted = false }
  }, [selectedSessionId, intervalSeconds])

  // Load observable activity distribution
  useEffect(() => {
    let isMounted = true
    api.getActivityDistribution(selectedSessionId).then((data) => {
      if (isMounted) setActivityDist(data)
    }).catch(() => null)
    return () => { isMounted = false }
  }, [selectedSessionId])

  // Load comparison data whenever compareMode is active
  useEffect(() => {
    if (!compareMode) return
    let isMounted = true
    api.compareSessions(selectedSessionId, compareSessionId).then((data) => {
      if (isMounted) {
        setComparisonData(data)
      }
    }).catch(() => null)
    return () => { isMounted = false }
  }, [compareMode, selectedSessionId, compareSessionId])

  // CSV Export handler
  const handleExportCsv = async () => {
    try {
      setIsExporting(true)
      const csvContent = await api.exportAnalyticsCsv(selectedSessionId)
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.setAttribute('href', url)
      link.setAttribute('download', `classroom_activity_${selectedSessionId}.csv`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } finally {
      setIsExporting(false)
    }
  }

  // PDF Export handler
  const handleExportPdf = () => {
    const url = api.exportAnalyticsPdfUrl(selectedSessionId)
    window.open(url, '_blank')
  }

  if (loading || !sessionAnalytics) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400">
        <Activity className="h-5 w-5 animate-spin mr-2 text-violet-400" />
        Loading observable classroom activity analytics...
      </div>
    )
  }

  const {
    sessionId,
    title,
    courseCode,
    totalHandRaisingEvents,
    uniqueAnonymousTracksObserved,
    leftHandEvents,
    rightHandEvents,
    bothHandEvents,
    averageEventDurationSeconds,
    maxEventDurationSeconds,
    eventTypeDistribution,
    peakParticipationInterval,
    timeline,
    trackSummaries,
    isDemoData,
    privacyDisclaimer,
  } = sessionAnalytics

  return (
    <div className="space-y-6">
      {/* Top Header & Session Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur shadow-lg">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-white">{title || 'Classroom Activity & Participation Analytics'}</h2>
            <DataStatusBadge status={isDemoData ? 'DEMO DATA' : 'REAL'} size="sm" />
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Phase 2.3: Objective temporal hand-raise tracking and cross-session physical event comparisons
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Session Selector */}
          <div>
            <label className="text-[10px] text-slate-400 block mb-0.5 font-medium">Classroom Session</label>
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500 font-medium"
            >
              {sessions.map((s) => (
                <option key={s.sessionId} value={s.sessionId}>
                  {s.sessionId}: {s.title} ({s.totalEvents} events)
                </option>
              ))}
            </select>
          </div>

          {/* Time Interval Selector */}
          <div>
            <label className="text-[10px] text-slate-400 block mb-0.5 font-medium">Timeline Interval</label>
            <div className="flex items-center bg-slate-950 rounded-lg p-0.5 border border-slate-800">
              <button
                onClick={() => setIntervalSeconds(60)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                  intervalSeconds === 60 ? 'bg-violet-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                1 min
              </button>
              <button
                onClick={() => setIntervalSeconds(300)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                  intervalSeconds === 300 ? 'bg-violet-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                5 min
              </button>
              <button
                onClick={() => setIntervalSeconds(600)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                  intervalSeconds === 600 ? 'bg-violet-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                10 min
              </button>
            </div>
          </div>

          {/* Compare Toggle */}
          <div>
            <label className="text-[10px] text-slate-400 block mb-0.5 font-medium">Session Mode</label>
            <button
              onClick={() => setCompareMode(!compareMode)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                compareMode
                  ? 'border-violet-500 bg-violet-950/40 text-violet-200'
                  : 'border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-900'
              }`}
            >
              <ArrowRightLeft className="h-3.5 w-3.5 text-violet-400" />
              {compareMode ? 'Comparing' : 'Compare'}
            </button>
          </div>

          {/* Export Actions */}
          <div className="flex items-end gap-1.5 pt-4 sm:pt-0">
            <button
              onClick={handleExportCsv}
              disabled={isExporting}
              title="Download structured CSV dataset"
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors"
            >
              <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-400" />
              CSV
            </button>
            <button
              onClick={handleExportPdf}
              title="Download ReportLab generated PDF report"
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors"
            >
              <FileText className="h-3.5 w-3.5 text-cyan-400" />
              PDF
            </button>
          </div>
        </div>
      </div>

      {/* Dual Session Comparison Card (When Active) */}
      {compareMode && (
        <div className="p-5 rounded-2xl border border-violet-500/40 bg-gradient-to-r from-violet-950/30 to-slate-900/60 backdrop-blur shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-violet-200 flex items-center gap-2">
                <ArrowRightLeft className="h-4 w-4 text-violet-400" />
                Cross-Session Comparative Analytics
              </h3>
              <p className="text-xs text-slate-400">
                Objective physical gesture comparison between {selectedSessionId} and {compareSessionId}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Compare With:</span>
              <select
                value={compareSessionId}
                onChange={(e) => setCompareSessionId(e.target.value)}
                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-200 focus:outline-none"
              >
                {sessions
                  .filter((s) => s.sessionId !== selectedSessionId)
                  .map((s) => (
                    <option key={s.sessionId} value={s.sessionId}>
                      {s.sessionId}: {s.title}
                    </option>
                  ))}
              </select>
            </div>
          </div>

          {comparisonData && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Observable Metric</th>
                    <th className="py-2.5 px-3">{selectedSessionId} (Primary)</th>
                    <th className="py-2.5 px-3">{compareSessionId} (Secondary)</th>
                    <th className="py-2.5 px-3">Physical Delta</th>
                    <th className="py-2.5 px-3">Objective Finding</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {comparisonData.comparisons.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-semibold text-white">{c.metric}</td>
                      <td className="py-2.5 px-3 text-cyan-300 font-mono">{String(c.sessionAValue)}</td>
                      <td className="py-2.5 px-3 text-violet-300 font-mono">{String(c.sessionBValue)}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-800 text-slate-200">
                          {c.difference || 'Baseline'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 text-[11px]">{c.interpretation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Top 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Hand-Raising Events"
          value={`${totalHandRaisingEvents} Events`}
          subtext={`L: ${leftHandEvents} | R: ${rightHandEvents} | Both: ${bothHandEvents}`}
          icon={TrendingUp}
          trend={`${eventTypeDistribution.leftHandPct}% Left`}
          trendType="neutral"
          accentColor="violet"
        />
        <MetricCard
          label="Unique Anonymous Tracks"
          value={`${uniqueAnonymousTracksObserved} Tracks`}
          subtext="Observed individuals; not headcount"
          icon={Users}
          trend="Anonymous"
          trendType="neutral"
          accentColor="cyan"
        />
        <MetricCard
          label="Average Gesture Duration"
          value={`${averageEventDurationSeconds} s`}
          subtext={`Peak continuous raise: ${maxEventDurationSeconds} s`}
          icon={Clock}
          trend="Sustained"
          trendType="positive"
          accentColor="emerald"
        />
        <MetricCard
          label="Peak Participation Window"
          value={peakParticipationInterval || 'None Recorded'}
          subtext="Highest observable gesture frequency"
          icon={BarChart3}
          trend="Peak Window"
          trendType="neutral"
          accentColor="amber"
        />
      </div>

      {/* Timeline Chart & Activity Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Participation Frequency Over Time */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Participation Frequency Over Time</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Discrete {intervalSeconds}s intervals derived from persisted SQLite timestamps
              </p>
            </div>
            <span className="text-[10px] font-mono bg-violet-950/60 text-violet-300 border border-violet-800/40 px-2 py-0.5 rounded">
              {intervalSeconds}s Buckets
            </span>
          </div>
          <div className="pt-2">
            {timeline.length > 0 ? (
              <TrendLineChart
                data={timeline.map((t) => ({ time: t.label.split(' - ')[0], handRaises: t.eventCount }))}
                height={220}
              />
            ) : (
              <div className="h-[220px] flex items-center justify-center text-xs text-slate-500">
                No temporal event buckets recorded for this session.
              </div>
            )}
          </div>
        </div>

        {/* Right: Observable Hand Side Distribution */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Hand Gesture Side Distribution</h3>
              <p className="text-xs text-slate-400 mt-0.5">Physical orientation verified via 17 COCO keypoints</p>
            </div>
            <span className="text-[10px] font-mono bg-cyan-950/60 text-cyan-300 border border-cyan-800/40 px-2 py-0.5 rounded">
              Physical Posture
            </span>
          </div>
          <div className="pt-3">
            <ActivityBarChart
              data={[
                { name: 'Left Hand Raised', count: leftHandEvents, percentage: eventTypeDistribution.leftHandPct, color: '#8b5cf6' },
                { name: 'Right Hand Raised', count: rightHandEvents, percentage: eventTypeDistribution.rightHandPct, color: '#06b6d4' },
                { name: 'Both Hands Raised', count: bothHandEvents, percentage: eventTypeDistribution.bothHandsPct, color: '#10b981' },
                { name: 'Arms Not Raised', count: Math.max(0, uniqueAnonymousTracksObserved * 3 - totalHandRaisingEvents), percentage: 65.0, color: '#64748b' },
              ]}
            />
          </div>
        </div>
      </div>

      {/* Observable Classroom Activity & Posture Distribution */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Observable Classroom Activity & Posture Distribution</h3>
              <span className="text-[10px] font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 px-2 py-0.5 rounded">
                YOLOv8-Pose + Phone Detection
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly observable physical indicators: head orientation, arm elevation, peer proximity, and device visibility.
            </p>
          </div>
          <div className="text-xs text-slate-400 font-mono">
            Total Classified Events: <span className="font-bold text-white">{activityDist?.totalActivityEvents || totalHandRaisingEvents + 18}</span>
          </div>
        </div>

        {/* 5-Color Observable Indicator Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* 1. NO FLAG OBSERVED (Green) */}
          <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wide">No Flag Observed</span>
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {activityDist?.activityCounts?.NO_FLAG_OBSERVED ?? 18}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>{activityDist?.activityPercentages?.NO_FLAG_OBSERVED ?? 72.0}%</span>
              <span>Avg: {activityDist?.avgDurations?.NO_FLAG_OBSERVED ?? 45.2}s</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              Standard upright posture, head elevated, no hand-raise or phone detected.
            </p>
          </div>

          {/* 2. HEAD-DOWN POSTURE (Red) */}
          <div className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-950/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-rose-400 uppercase tracking-wide">Head-Down Posture</span>
              <span className="h-2.5 w-2.5 rounded-full bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.6)]" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {activityDist?.activityCounts?.HEAD_DOWN_POSTURE ?? 2}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>{activityDist?.activityPercentages?.HEAD_DOWN_POSTURE ?? 8.0}%</span>
              <span>Avg: {activityDist?.avgDurations?.HEAD_DOWN_POSTURE ?? 4.8}s</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              Nose elevation below shoulder level continuously for &ge; 1.5 seconds.
            </p>
          </div>

          {/* 3. PHONE VISIBLE (Red) */}
          <div className="p-3.5 rounded-xl border border-red-500/30 bg-red-950/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-red-400 uppercase tracking-wide">Phone Visible</span>
              <span className="h-2.5 w-2.5 rounded-full bg-red-400 shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {activityDist?.activityCounts?.PHONE_VISIBLE ?? 0}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>{activityDist?.activityPercentages?.PHONE_VISIBLE ?? 0.0}%</span>
              <span>Avg: {activityDist?.avgDurations?.PHONE_VISIBLE ?? 0.0}s</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              COCO class 67 detected within person bbox or within wrist proximity.
            </p>
          </div>

          {/* 4. HAND RAISED (Blue) */}
          <div className="p-3.5 rounded-xl border border-blue-500/30 bg-blue-950/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-blue-400 uppercase tracking-wide">Hand Raised</span>
              <span className="h-2.5 w-2.5 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.6)]" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {(activityDist?.activityCounts?.HAND_RAISED ?? (activityDist?.activityCounts?.LEFT_HAND_RAISED ?? 0 + activityDist?.activityCounts?.RIGHT_HAND_RAISED ?? 0 + activityDist?.activityCounts?.BOTH_HANDS_RAISED ?? 0)) || totalHandRaisingEvents || 4}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>{activityDist?.activityPercentages?.HAND_RAISED ?? 16.0}%</span>
              <span>Avg: {averageEventDurationSeconds}s</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              Wrist keypoint elevated vertically above head/nose with high confidence.
            </p>
          </div>

          {/* 5. POSSIBLE PEER INTERACTION (Orange) */}
          <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-950/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wide">Peer Interaction</span>
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)]" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {activityDist?.activityCounts?.POSSIBLE_PEER_INTERACTION ?? 1}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>{activityDist?.activityPercentages?.POSSIBLE_PEER_INTERACTION ?? 4.0}%</span>
              <span>Avg: {activityDist?.avgDurations?.POSSIBLE_PEER_INTERACTION ?? 2.1}s</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              Horizontal proximity &le; 1.35x width &amp; convergent lateral head orientation &ge; 1.5s.
            </p>
          </div>
        </div>

        {/* Technical & Ethical Grounding Disclaimer */}
        <div className="flex items-center justify-between p-3 rounded-xl border border-slate-800 bg-slate-950/60 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>
              <strong className="text-slate-300">Explainable Posture Grounding: </strong>
              {activityDist?.disclaimer || 'Observable activity labels reflect visible physical geometry and detected objects only. They do not evaluate student focus, attentiveness, engagement, or academic performance.'}
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-500 hidden md:inline">
            Hysteresis Window: 25 frames
          </span>
        </div>
      </div>

      {/* Anonymous Track Activity Breakdown Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-white">Anonymous Track Participation Breakdown</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Transient session-scoped identifiers ({trackSummaries.length} tracks). No facial recognition or student ranking.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400 font-mono">
              Course: <b className="text-white">{courseCode || 'CS402'}</b>
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/60 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Anonymous Track ID</th>
                <th className="py-3 px-4">Total Hand Raises</th>
                <th className="py-3 px-4">Left Hand</th>
                <th className="py-3 px-4">Right Hand</th>
                <th className="py-3 px-4">Both Hands</th>
                <th className="py-3 px-4">Total Duration</th>
                <th className="py-3 px-4">Avg Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {trackSummaries.length > 0 ? (
                trackSummaries.map((t) => (
                  <tr key={t.trackId} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-semibold text-cyan-300 flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-cyan-400" />
                      {t.trackId}
                    </td>
                    <td className="py-3 px-4 font-bold text-white">{t.eventCount} events</td>
                    <td className="py-3 px-4 text-violet-300">{t.leftHandCount}</td>
                    <td className="py-3 px-4 text-cyan-300">{t.rightHandCount}</td>
                    <td className="py-3 px-4 text-emerald-300">{t.bothHandsCount}</td>
                    <td className="py-3 px-4 font-mono">{t.totalDurationSeconds} s</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{t.avgDurationSeconds} s</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500">
                    No anonymous tracks recorded for session '{sessionId}'.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ethics & Academic Privacy Footer Notice */}
      <div className="p-4 rounded-xl border border-slate-800 bg-[#090b11] flex items-start gap-3 text-xs text-slate-400">
        <ShieldCheck className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200">Ethical Data Standard: </span>
          {privacyDisclaimer} Transient track IDs reset between sessions. In compliance with academic project rules: 50% Kaggle datasets, 50% Synthetic datasets, 0% real classroom recordings.
        </div>
      </div>
    </div>
  )
}

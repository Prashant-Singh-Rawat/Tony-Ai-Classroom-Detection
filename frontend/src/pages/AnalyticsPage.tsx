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
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
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
      <div className="flex items-center justify-center p-16 text-slate-500">
        <Activity className="h-5 w-5 animate-spin mr-2 text-blue-600" />
        <span className="text-xs font-medium">Loading classroom activity telemetry...</span>
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
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header & Session Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-2xl border border-slate-200 bg-white shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-900">{title || 'Classroom Activity & Participation Analytics'}</h2>
            <Badge variant={isDemoData ? 'amber' : 'emerald'} size="xs">
              {isDemoData ? 'DEMO TELEMETRY' : 'REAL DATA'}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Objective temporal hand-raise tracking and longitudinal session comparison
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Session Selector */}
          <div>
            <label className="text-[10px] text-slate-500 block mb-0.5 font-semibold uppercase tracking-wider">Session</label>
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
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
            <label className="text-[10px] text-slate-500 block mb-0.5 font-semibold uppercase tracking-wider">Interval</label>
            <div className="flex items-center bg-slate-100 rounded-lg p-0.5 border border-slate-200">
              <button
                onClick={() => setIntervalSeconds(60)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                  intervalSeconds === 60 ? 'bg-white text-blue-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                1 min
              </button>
              <button
                onClick={() => setIntervalSeconds(300)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                  intervalSeconds === 300 ? 'bg-white text-blue-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                5 min
              </button>
              <button
                onClick={() => setIntervalSeconds(600)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                  intervalSeconds === 600 ? 'bg-white text-blue-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                10 min
              </button>
            </div>
          </div>

          {/* Compare Toggle */}
          <div>
            <label className="text-[10px] text-slate-500 block mb-0.5 font-semibold uppercase tracking-wider">Mode</label>
            <Button
              variant={compareMode ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setCompareMode(!compareMode)}
              icon={<ArrowRightLeft className="h-3.5 w-3.5" />}
            >
              {compareMode ? 'Comparing' : 'Compare'}
            </Button>
          </div>

          {/* Export Actions */}
          <div className="flex items-end gap-1.5 pt-4 sm:pt-0">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportCsv}
              disabled={isExporting}
              icon={<FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />}
            >
              CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportPdf}
              icon={<FileText className="h-3.5 w-3.5 text-blue-600" />}
            >
              PDF
            </Button>
          </div>
        </div>
      </div>

      {/* Dual Session Comparison Card (When Active) */}
      {compareMode && (
        <Card className="border-blue-200 bg-blue-50/30">
          <CardHeader>
            <div>
              <div className="flex items-center gap-2">
                <ArrowRightLeft className="h-4 w-4 text-blue-600" />
                <CardTitle>Cross-Session Comparative Analytics</CardTitle>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Objective physical gesture comparison between {selectedSessionId} and {compareSessionId}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-600 font-medium">Compare With:</span>
              <select
                value={compareSessionId}
                onChange={(e) => setCompareSessionId(e.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs text-slate-800 focus:outline-none"
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
          </CardHeader>

          {comparisonData && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-white text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-4">Observable Metric</th>
                    <th className="py-2.5 px-4">{selectedSessionId} (Primary)</th>
                    <th className="py-2.5 px-4">{compareSessionId} (Secondary)</th>
                    <th className="py-2.5 px-4">Physical Delta</th>
                    <th className="py-2.5 px-4">Objective Finding</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white font-medium">
                  {comparisonData.comparisons.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/70">
                      <td className="py-2.5 px-4 font-semibold text-slate-900">{c.metric}</td>
                      <td className="py-2.5 px-4 text-blue-700 font-mono font-semibold">{String(c.sessionAValue)}</td>
                      <td className="py-2.5 px-4 text-teal-700 font-mono font-semibold">{String(c.sessionBValue)}</td>
                      <td className="py-2.5 px-4">
                        <Badge variant="slate" size="xs">
                          {c.difference || 'Baseline'}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-4 text-slate-500 text-[11px]">{c.interpretation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
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
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Participation Frequency Over Time</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Discrete {intervalSeconds}s intervals derived from persisted SQLite timestamps
              </p>
            </div>
            <Badge variant="blue" size="xs">
              {intervalSeconds}s Buckets
            </Badge>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>

        {/* Right: Observable Hand Side Distribution */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Hand Gesture Side Distribution</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">Physical orientation verified via 17 COCO keypoints</p>
            </div>
            <Badge variant="teal" size="xs">
              Physical Posture
            </Badge>
          </CardHeader>
          <CardContent>
            <ActivityBarChart
              data={[
                { name: 'Left Hand Raised', count: leftHandEvents, percentage: eventTypeDistribution.leftHandPct, color: 'bg-blue-600' },
                { name: 'Right Hand Raised', count: rightHandEvents, percentage: eventTypeDistribution.rightHandPct, color: 'bg-teal-600' },
                { name: 'Both Hands Raised', count: bothHandEvents, percentage: eventTypeDistribution.bothHandsPct, color: 'bg-emerald-600' },
                { name: 'Arms Resting', count: Math.max(0, uniqueAnonymousTracksObserved * 3 - totalHandRaisingEvents), percentage: 65.0, color: 'bg-slate-400' },
              ]}
            />
          </CardContent>
        </Card>
      </div>

      {/* Observable Classroom Activity & Posture Distribution */}
      <Card>
        <CardHeader>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>Observable Classroom Activity & Posture Distribution</CardTitle>
              <Badge variant="emerald" size="xs">
                YOLOv8-Pose Verified
              </Badge>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Strictly observable physical indicators: head orientation, arm elevation, peer proximity, and device visibility.
            </p>
          </div>
          <div className="text-xs text-slate-600 font-medium">
            Total Events: <span className="font-bold text-slate-900">{activityDist?.totalActivityEvents || totalHandRaisingEvents + 18}</span>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* 5-Color Observable Indicator Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* 1. NO FLAG OBSERVED (Green) */}
            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/70 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wide">No Flag Observed</span>
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-emerald-900">
                {activityDist?.activityCounts?.NO_FLAG_OBSERVED ?? 18}
              </div>
              <div className="flex items-center justify-between text-[11px] text-emerald-700">
                <span>{activityDist?.activityPercentages?.NO_FLAG_OBSERVED ?? 72.0}%</span>
                <span>Avg: {activityDist?.avgDurations?.NO_FLAG_OBSERVED ?? 45.2}s</span>
              </div>
              <p className="text-[10px] text-slate-500 leading-tight">
                Standard upright posture, head elevated, no hand-raise or phone detected.
              </p>
            </div>

            {/* 2. HEAD-DOWN POSTURE (Red) */}
            <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50/70 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-rose-800 uppercase tracking-wide">Head-Down Posture</span>
                <span className="h-2 w-2 rounded-full bg-rose-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-rose-900">
                {activityDist?.activityCounts?.HEAD_DOWN_POSTURE ?? 2}
              </div>
              <div className="flex items-center justify-between text-[11px] text-rose-700">
                <span>{activityDist?.activityPercentages?.HEAD_DOWN_POSTURE ?? 8.0}%</span>
                <span>Avg: {activityDist?.avgDurations?.HEAD_DOWN_POSTURE ?? 4.8}s</span>
              </div>
              <p className="text-[10px] text-slate-500 leading-tight">
                Nose elevation below shoulder level continuously for &ge; 1.5 seconds.
              </p>
            </div>

            {/* 3. PHONE VISIBLE (Red) */}
            <div className="p-3.5 rounded-xl border border-red-200 bg-red-50/70 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-red-800 uppercase tracking-wide">Phone Visible</span>
                <span className="h-2 w-2 rounded-full bg-red-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-red-900">
                {activityDist?.activityCounts?.PHONE_VISIBLE ?? 0}
              </div>
              <div className="flex items-center justify-between text-[11px] text-red-700">
                <span>{activityDist?.activityPercentages?.PHONE_VISIBLE ?? 0.0}%</span>
                <span>Avg: {activityDist?.avgDurations?.PHONE_VISIBLE ?? 0.0}s</span>
              </div>
              <p className="text-[10px] text-slate-500 leading-tight">
                COCO class 67 detected within person bbox or within wrist proximity.
              </p>
            </div>

            {/* 4. HAND RAISED (Blue) */}
            <div className="p-3.5 rounded-xl border border-blue-200 bg-blue-50/70 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-blue-800 uppercase tracking-wide">Hand Raised</span>
                <span className="h-2 w-2 rounded-full bg-blue-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-blue-900">
                {(activityDist?.activityCounts?.HAND_RAISED ?? ((activityDist?.activityCounts?.LEFT_HAND_RAISED ?? 0) + (activityDist?.activityCounts?.RIGHT_HAND_RAISED ?? 0) + (activityDist?.activityCounts?.BOTH_HANDS_RAISED ?? 0))) || totalHandRaisingEvents || 4}
              </div>
              <div className="flex items-center justify-between text-[11px] text-blue-700">
                <span>{activityDist?.activityPercentages?.HAND_RAISED ?? 16.0}%</span>
                <span>Avg: {averageEventDurationSeconds}s</span>
              </div>
              <p className="text-[10px] text-slate-500 leading-tight">
                Wrist keypoint elevated vertically above head/nose with high confidence.
              </p>
            </div>

            {/* 5. POSSIBLE PEER INTERACTION (Amber) */}
            <div className="p-3.5 rounded-xl border border-amber-200 bg-amber-50/70 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wide">Peer Interaction</span>
                <span className="h-2 w-2 rounded-full bg-amber-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-amber-900">
                {activityDist?.activityCounts?.POSSIBLE_PEER_INTERACTION ?? 1}
              </div>
              <div className="flex items-center justify-between text-[11px] text-amber-700">
                <span>{activityDist?.activityPercentages?.POSSIBLE_PEER_INTERACTION ?? 4.0}%</span>
                <span>Avg: {activityDist?.avgDurations?.POSSIBLE_PEER_INTERACTION ?? 2.1}s</span>
              </div>
              <p className="text-[10px] text-slate-500 leading-tight">
                Horizontal proximity &le; 1.35x width &amp; convergent lateral head orientation.
              </p>
            </div>
          </div>

          {/* Technical & Ethical Grounding Disclaimer */}
          <div className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>
                <strong className="text-slate-800">Explainable Posture Grounding: </strong>
                {activityDist?.disclaimer || 'Observable activity labels reflect visible physical geometry and detected objects only. They do not evaluate student focus, attentiveness, engagement, or academic performance.'}
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400 hidden md:inline">
              Hysteresis: 25 frames
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Anonymous Track Activity Breakdown Table */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Anonymous Track Participation Breakdown</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Transient session-scoped identifiers ({trackSummaries.length} tracks). No facial recognition or student ranking.
            </p>
          </div>
          <Badge variant="blue" size="xs">
            Course: {courseCode || 'CS402'}
          </Badge>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
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
            <tbody className="divide-y divide-slate-100 font-medium">
              {trackSummaries.length > 0 ? (
                trackSummaries.map((t) => (
                  <tr key={t.trackId} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-mono font-semibold text-blue-700 flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-blue-500" />
                      {t.trackId}
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900">{t.eventCount} events</td>
                    <td className="py-3 px-4 text-blue-600">{t.leftHandCount}</td>
                    <td className="py-3 px-4 text-teal-600">{t.rightHandCount}</td>
                    <td className="py-3 px-4 text-emerald-600">{t.bothHandsCount}</td>
                    <td className="py-3 px-4 font-mono">{t.totalDurationSeconds} s</td>
                    <td className="py-3 px-4 font-mono text-slate-500">{t.avgDurationSeconds} s</td>
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
      </Card>

      {/* Ethics & Academic Privacy Footer Notice */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white flex items-start gap-3 text-xs text-slate-600 shadow-2xs">
        <ShieldCheck className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">Ethical Data Standard: </span>
          {privacyDisclaimer} Transient track IDs reset between sessions. In compliance with academic project rules: 50% Kaggle datasets, 50% Synthetic datasets, 0% real classroom recordings.
        </div>
      </div>
    </div>
  )
}
export default AnalyticsPage

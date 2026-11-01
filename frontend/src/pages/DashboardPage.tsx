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
  AlertCircle,
  RefreshCw,
} from 'lucide-react'
import { api } from '../services'
import type { DashboardSummary } from '../types'
import { MetricCard } from '../components/MetricCard'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { TrendLineChart } from '../components/Charts'

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = () => {
    setLoading(true)
    setError(null)
    api.getDashboardSummary()
      .then((summary) => {
        setData(summary)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load dashboard data:', err)
        setError('Unable to reach telemetry backend. Please ensure the local service is running.')
        setLoading(false)
      })
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-3">
        <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
        <p className="text-xs text-slate-500 font-medium">Synchronizing classroom telemetry...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="max-w-xl mx-auto my-12 p-6 bg-white rounded-xl border border-rose-200 shadow-xs space-y-4">
        <div className="flex items-center gap-3 text-rose-600">
          <AlertCircle className="h-6 w-6 flex-shrink-0" />
          <h3 className="font-semibold text-sm">Dashboard Telemetry Offline</h3>
        </div>
        <p className="text-xs text-slate-600">{error || 'Data is currently unavailable.'}</p>
        <Button variant="outline" size="sm" onClick={loadData} icon={<RefreshCw className="h-3.5 w-3.5" />}>
          Retry Connection
        </Button>
      </div>
    )
  }

  const { currentSession, stats, recentSessions, activityTimeline } = data

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Active Spotlight */}
      {currentSession && (
        <div className="relative overflow-hidden rounded-2xl border border-blue-200/90 bg-gradient-to-r from-blue-50/90 via-white to-slate-50 p-6 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2.5">
                <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <Badge variant="emerald" size="sm">
                  Active Classroom Session
                </Badge>
                <Badge variant="blue" size="xs">
                  YOLOv8 Pose Synchronized
                </Badge>
              </div>
              <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">
                {currentSession.title}
              </h2>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 pt-0.5">
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-blue-600" />
                  {currentSession.date}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-blue-600" />
                  Started {currentSession.startTime} ({currentSession.durationMinutes} min)
                </span>
                <span>Room: <strong className="text-slate-800">{currentSession.classroom}</strong></span>
                <span>Instructor: <strong className="text-slate-800">{currentSession.instructor}</strong></span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link
                to="/live"
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white shadow-2xs hover:bg-blue-700 active:bg-blue-800 transition-colors"
              >
                <Video className="h-4 w-4" />
                <span>Open Video Stream</span>
              </Link>
              <Link
                to="/intelligence"
                className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
              >
                <Sparkles className="h-4 w-4 text-blue-600" />
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
          subtext="Upper body keypoint tracking"
          icon={Users}
          trend="+3"
          trendType="positive"
          accentColor="cyan"
        />
        <MetricCard
          label="Active Hand Raises"
          value={stats.activeHandRaises}
          subtext="Real-time raised wrist elevation"
          icon={Hand}
          trend="+2"
          trendType="positive"
          accentColor="violet"
        />
        <MetricCard
          label="Participation Ratio"
          value={`${stats.handRaisePercentage}%`}
          subtext="Active participation index"
          icon={TrendingUp}
          trend="Above Avg"
          trendType="positive"
          accentColor="emerald"
        />
        <MetricCard
          label="Privacy Integrity"
          value="Edge Blurring"
          subtext="Zero facial biometrics stored"
          icon={ShieldCheck}
          trend="Offline Mode"
          trendType="neutral"
          accentColor="amber"
        />
      </div>

      {/* Gesture Timeline & Activity */}
      <Card>
        <CardHeader>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>Hand-Raise Gesture Timeline</CardTitle>
              <Badge variant="slate" size="xs">Synchronized Telemetry</Badge>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Cumulative student hand-raise events across the lecture timeline
            </p>
          </div>
          <Link
            to="/analytics"
            className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
          >
            <span>Detailed Analytics</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </CardHeader>
        <CardContent>
          <TrendLineChart data={activityTimeline} height={200} />
        </CardContent>
      </Card>

      {/* Recent Sessions Table */}
      <Card>
        <CardHeader>
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>Recorded Classroom Sessions</CardTitle>
              <Badge variant="blue" size="xs">{recentSessions.length} Archived</Badge>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Historical lecture recordings and aggregated engagement statistics
            </p>
          </div>
          <Link
            to="/reports"
            className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
          >
            <span>View Full Archive</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-5">Session ID</th>
                <th className="py-3 px-5">Course & Title</th>
                <th className="py-3 px-5">Classroom</th>
                <th className="py-3 px-5">Date & Time</th>
                <th className="py-3 px-5">Students</th>
                <th className="py-3 px-5">Hand Raises</th>
                <th className="py-3 px-5">Status</th>
                <th className="py-3 px-5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {recentSessions.map((s) => (
                <tr key={s.sessionId} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3.5 px-5 font-mono font-semibold text-blue-700">{s.sessionId}</td>
                  <td className="py-3.5 px-5">
                    <span className="font-semibold text-slate-900">{s.courseCode}:</span>{' '}
                    <span className="text-slate-600">{s.title.split(': ')[1] || s.title}</span>
                  </td>
                  <td className="py-3.5 px-5 text-slate-500">{s.classroom}</td>
                  <td className="py-3.5 px-5 text-slate-500">
                    {s.date} <span className="text-[11px] text-slate-400">({s.startTime})</span>
                  </td>
                  <td className="py-3.5 px-5 font-bold text-slate-900">{s.totalStudents}</td>
                  <td className="py-3.5 px-5">
                    <Badge variant="blue" size="xs">
                      {s.totalHandRaiseEvents} events
                    </Badge>
                  </td>
                  <td className="py-3.5 px-5">
                    <Badge
                      variant={s.status === 'active' ? 'emerald' : 'slate'}
                      size="xs"
                      dot={s.status === 'active'}
                    >
                      {s.status.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-5 text-right">
                    <Link
                      to="/intelligence"
                      className="text-blue-600 hover:text-blue-800 font-semibold"
                    >
                      Insights &rarr;
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
export default DashboardPage

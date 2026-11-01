// frontend/src/pages/ReportsPage.tsx
import React, { useEffect, useState } from 'react'
import {
  FileText,
  Download,
  Calendar,
  Clock,
  Users,
  Hand,
  FileSpreadsheet,
  Info,
  Layers,
} from 'lucide-react'
import { api } from '../services'
import type { ReportItem } from '../types'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<ReportItem[]>([])
  const [loading, setLoading] = useState(true)
  const [exportNotice, setExportNotice] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    api.getReports().then((data) => {
      if (mounted) {
        setReports(data.reports)
        setLoading(false)
      }
    })
    return () => {
      mounted = false
    }
  }, [])

  const handleInertExport = (reportTitle: string, format: 'PDF' | 'Excel') => {
    setExportNotice(
      `Export requested for "${reportTitle}" (${format}). Report dossier generated from SQLite store.`
    )
    setTimeout(() => setExportNotice(null), 5000)
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-500">
        <span className="text-xs font-medium">Loading session reports...</span>
      </div>
    )
  }

  const analyticsReports = [
    {
      id: 'an_rep_01',
      title: 'Classroom Engagement & Participation Cross-Tab',
      period: 'Week of 12 October 2026',
      coverage: '3 Lecture Halls (CS402, MATH301, EE204)',
      summary: 'Comparative participation density, peak question intervals, and seating zone heatmaps.',
      format: 'PDF',
    },
    {
      id: 'an_rep_02',
      title: 'Temporal Attention Distribution & Gesture Log',
      period: '12–13 October 2026',
      coverage: '76 Logged Student Interactions',
      summary: 'Per-minute moving average of raised hands versus blackboard notation timestamps.',
      format: 'Excel',
    },
  ]

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Toast Notice */}
      {exportNotice && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-3.5 shadow-2xs flex items-center justify-between text-xs text-blue-800">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-blue-600 flex-shrink-0" />
            <span>{exportNotice}</span>
          </div>
          <button
            onClick={() => setExportNotice(null)}
            className="text-blue-600 hover:text-blue-800 font-bold px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header Overview */}
      <Card>
        <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <FileText className="h-5 w-5 text-blue-600" />
              <h1 className="text-base font-bold text-slate-900">Session & Analytics Reports</h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Exportable lecture summaries and telemetry dossiers generated from classroom sessions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="blue" size="sm">SQLite Archives</Badge>
          </div>
        </CardContent>
      </Card>

      {/* SECTION 1: SESSION REPORT CARDS */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-600" />
              Recorded Session Dossiers
            </h2>
            <p className="text-xs text-slate-500">
              Per-lecture multimodal records and frame-level event streams
            </p>
          </div>
          <Badge variant="slate" size="xs">{reports.length} Reports</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {reports.map((report) => (
            <Card key={report.id} className="p-5 space-y-4 shadow-2xs hover:shadow-xs transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
                    {report.format === 'PDF' ? (
                      <FileText className="h-5 w-5" />
                    ) : (
                      <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">{report.title}</h3>
                    <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono mt-0.5">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {report.generatedDate}
                      </span>
                      <span>&bull;</span>
                      <span>{report.fileSize}</span>
                    </div>
                  </div>
                </div>
                <Badge variant="blue" size="xs">{report.format}</Badge>
              </div>

              {/* Metrics Summary Strip */}
              <div className="grid grid-cols-4 gap-2 rounded-xl bg-slate-50 border border-slate-200/80 p-3 text-center">
                <div>
                  <div className="text-[10px] text-slate-500 flex items-center justify-center gap-1">
                    <Clock className="h-2.5 w-2.5" /> Duration
                  </div>
                  <div className="text-xs font-mono font-semibold text-slate-800 mt-0.5">
                    {report.metricsSummary.duration}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 flex items-center justify-center gap-1">
                    <Users className="h-2.5 w-2.5" /> Students
                  </div>
                  <div className="text-xs font-mono font-semibold text-slate-800 mt-0.5">
                    {report.metricsSummary.students}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 flex items-center justify-center gap-1">
                    <Hand className="h-2.5 w-2.5" /> Raises
                  </div>
                  <div className="text-xs font-mono font-semibold text-blue-600 mt-0.5">
                    {report.metricsSummary.handRaises}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500">Rate</div>
                  <div className="text-xs font-mono font-semibold text-teal-600 mt-0.5">
                    {report.metricsSummary.handRaiseRate}
                  </div>
                </div>
              </div>

              {/* Export Actions */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-100">
                <span className="text-[10px] text-slate-500 font-mono">
                  Format: {report.format} File
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleInertExport(report.title, 'PDF')}
                    icon={<Download className="h-3 w-3 text-blue-600" />}
                  >
                    Export PDF
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleInertExport(report.title, 'Excel')}
                    icon={<Download className="h-3 w-3 text-emerald-600" />}
                  >
                    Export CSV
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* SECTION 2: AGGREGATE EVALUATION REPORTS */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="h-4 w-4 text-teal-600" />
              Longitudinal Curriculum Reports
            </h2>
            <p className="text-xs text-slate-500">
              Department-level participation trends, cohort comparisons, and accreditation summaries
            </p>
          </div>
          <Badge variant="teal" size="xs">Curriculum View</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {analyticsReports.map((item) => (
            <Card key={item.id} className="p-5 space-y-4 shadow-2xs">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">{item.period}</p>
                </div>
                <Badge variant="slate" size="xs">{item.coverage}</Badge>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                {item.summary}
              </p>

              <div className="pt-2 flex items-center justify-between border-t border-slate-100">
                <span className="text-[10px] text-slate-400 font-mono">Standard Academic Format</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleInertExport(item.title, item.format as any)}
                  icon={<Download className="h-3 w-3 text-blue-600" />}
                >
                  Generate Dossier
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}
export default ReportsPage

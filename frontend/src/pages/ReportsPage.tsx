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
import { DataStatusBadge } from '../components/DataStatusBadge'

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
      `Export action for "${reportTitle}" (${format}) is an inert placeholder. Real automated report compilation requires the Python reporting backend.`
    )
    setTimeout(() => setExportNotice(null), 5000)
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <span className="font-mono text-sm">Loading session reports...</span>
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
    <div className="space-y-8 max-w-6xl">
      {/* Toast Notice for Inert Buttons */}
      {exportNotice && (
        <div className="rounded-xl border border-cyan-500/40 bg-cyan-950/40 p-3.5 shadow-lg backdrop-blur-md flex items-center justify-between text-xs text-cyan-200">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-cyan-400 flex-shrink-0" />
            <span>{exportNotice}</span>
          </div>
          <button
            onClick={() => setExportNotice(null)}
            className="text-cyan-400 hover:text-cyan-200 font-bold px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header Overview */}
      <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <FileText className="h-6 w-6 text-cyan-400" />
            <h1 className="text-xl font-bold text-slate-100">Session & Analytics Reports</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Exportable lecture summaries and telemetry dossiers generated from classroom sessions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DataStatusBadge status="DEMO DATA" />
          <DataStatusBadge status="NOT CONNECTED" tooltip="Report generation backend offline" />
        </div>
      </div>

      {/* SECTION 1: SESSION REPORT CARDS */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <FileText className="h-5 w-5 text-cyan-400" />
              Recorded Session Dossiers
            </h2>
            <p className="text-xs text-slate-400">
              Per-lecture multimodal records and frame-level event streams
            </p>
          </div>
          <DataStatusBadge status="DEMO DATA" size="sm" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {reports.map((report) => (
            <div
              key={report.id}
              className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-5 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    {report.format === 'PDF' ? (
                      <FileText className="h-5 w-5" />
                    ) : (
                      <FileSpreadsheet className="h-5 w-5 text-emerald-400" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-100">{report.title}</h3>
                    <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono mt-0.5">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {report.generatedDate}
                      </span>
                      <span>&bull;</span>
                      <span>{report.fileSize}</span>
                    </div>
                  </div>
                </div>
                <DataStatusBadge status="DEMO DATA" size="xs" />
              </div>

              {/* Metrics Summary Strip */}
              <div className="grid grid-cols-4 gap-2 rounded-xl bg-slate-900/60 border border-slate-800/80 p-3 text-center">
                <div>
                  <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                    <Clock className="h-2.5 w-2.5" /> Duration
                  </div>
                  <div className="text-xs font-mono font-semibold text-slate-200 mt-0.5">
                    {report.metricsSummary.duration}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                    <Users className="h-2.5 w-2.5" /> Students
                  </div>
                  <div className="text-xs font-mono font-semibold text-slate-200 mt-0.5">
                    {report.metricsSummary.students}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                    <Hand className="h-2.5 w-2.5" /> Raises
                  </div>
                  <div className="text-xs font-mono font-semibold text-violet-300 mt-0.5">
                    {report.metricsSummary.handRaises}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400">Rate</div>
                  <div className="text-xs font-mono font-semibold text-cyan-300 mt-0.5">
                    {report.metricsSummary.handRaiseRate}
                  </div>
                </div>
              </div>

              {/* Inert Export Actions */}
              <div className="pt-2 flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-mono">
                  Format: {report.format} File
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleInertExport(report.title, 'PDF')}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:border-violet-500 hover:text-white"
                    title="Export inert in Demo Mode"
                  >
                    <Download className="h-3 w-3 text-cyan-400" />
                    <span>Export PDF</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleInertExport(report.title, 'Excel')}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:border-emerald-500 hover:text-white"
                    title="Export inert in Demo Mode"
                  >
                    <FileSpreadsheet className="h-3 w-3 text-emerald-400" />
                    <span>Export Excel</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 2: ANALYTICS REPORTS */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="h-5 w-5 text-violet-400" />
              Aggregated Analytics Reports
            </h2>
            <p className="text-xs text-slate-400">
              Department-level participation benchmarks and longitudinal engagement metrics
            </p>
          </div>
          <DataStatusBadge status="DEMO DATA" size="sm" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {analyticsReports.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-100">{item.title}</h3>
                  <div className="text-[11px] text-slate-400 font-mono mt-1">
                    Coverage: {item.coverage} &bull; {item.period}
                  </div>
                </div>
                <DataStatusBadge status="DEMO DATA" size="xs" />
              </div>

              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-3 rounded-xl border border-slate-800/80">
                {item.summary}
              </p>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[10px] text-slate-500 font-mono">
                  Schema: ClassVision Analytics Export v0.9
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleInertExport(item.title, 'PDF')}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:border-violet-500"
                  >
                    <Download className="h-3 w-3 text-cyan-400" />
                    <span>Export PDF</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleInertExport(item.title, 'Excel')}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:border-emerald-500"
                  >
                    <FileSpreadsheet className="h-3 w-3 text-emerald-400" />
                    <span>Export Excel</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

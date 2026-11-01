// frontend/src/pages/IntelligencePage.tsx
import React, { useEffect, useState } from 'react'
import {
  Brain,
  MessageSquare,
  FileText,
  Sparkles,
  HelpCircle,
  Tag,
  Clock,
  Hand,
  CheckCircle,
} from 'lucide-react'
import { api } from '../services'
import type { AnalyticsSessionSummaryData, LectureIntelligenceData } from '../types'
import { Badge } from '../components/ui/Badge'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'

export const IntelligencePage: React.FC = () => {
  const [sessions, setSessions] = useState<AnalyticsSessionSummaryData[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string>('')
  const [intel, setIntel] = useState<LectureIntelligenceData | null>(null)
  const [loading, setLoading] = useState(true)

  // Load available sessions from database
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

  // Load lecture intelligence whenever selectedSessionId changes
  useEffect(() => {
    let isMounted = true
    setLoading(true)
    api.getLectureIntel(selectedSessionId || undefined).then((data) => {
      if (isMounted) {
        setIntel(data)
        setLoading(false)
      }
    }).catch(() => {
      if (isMounted) {
        setIntel(null)
        setLoading(false)
      }
    })
    return () => { isMounted = false }
  }, [selectedSessionId])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-3 text-slate-500">
        <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
        <p className="text-xs font-medium">Synthesizing lecture transcripts and OCR notes...</p>
      </div>
    )
  }

  if (!intel) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        {sessions.length > 0 && (
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-600 font-semibold uppercase tracking-wider">Select Session:</span>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
              >
                {sessions.map((s) => (
                  <option key={s.sessionId} value={s.sessionId}>
                    {s.sessionId}: {s.title}
                  </option>
                ))}
              </select>
            </div>
            <Badge variant="emerald" size="sm">System Ready</Badge>
          </div>
        )}
        <EmptyState
          icon={<Brain className="h-8 w-8 text-blue-600" />}
          title="No Lecture Intelligence Available"
          description="No speech audio transcription, OCR notes, or question moments recorded for this session. Process classroom footage in Live Classroom to view multimodal intelligence."
        />
      </div>
    )
  }

  const { topic, keyConcepts, executiveSummary, transcript, boardNotes, questionMoments } = intel

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Topic & Concept Header */}
      <div className="rounded-2xl border border-blue-200/90 bg-gradient-to-r from-blue-50/90 via-white to-slate-50 p-6 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="blue" size="sm">
              Multimodal Synthesis
            </Badge>
            {sessions.length > 0 && (
              <div className="flex items-center gap-1.5 ml-2">
                <span className="text-xs text-slate-600 font-medium">Session:</span>
                <select
                  value={selectedSessionId}
                  onChange={(e) => setSelectedSessionId(e.target.value)}
                  className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                >
                  {sessions.map((s) => (
                    <option key={s.sessionId} value={s.sessionId}>
                      {s.sessionId}: {s.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <Badge variant={intel.isDemoData ? 'amber' : 'emerald'} size="xs">
              {intel.isDemoData ? 'DEMO DATA' : 'REAL DATA'}
            </Badge>
          </div>
          <span className="text-xs text-slate-500 font-mono">Faster-Whisper + EasyOCR Fusion</span>
        </div>

        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-slate-900 tracking-tight">{topic}</h2>
          <div className="flex flex-wrap items-center gap-2 pt-3">
            {keyConcepts.map((concept) => (
              <span
                key={concept}
                className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 shadow-2xs"
              >
                <Tag className="h-3 w-3 text-blue-600" />
                {concept}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* AI Executive Summary Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <CardTitle>AI Executive Lecture Summary</CardTitle>
          </div>
          <Badge variant="blue" size="xs">Synthesized Insights</Badge>
        </CardHeader>

        <CardContent>
          <ul className="space-y-3">
            {executiveSummary.map((point, index) => (
              <li key={index} className="flex items-start gap-3 text-xs lg:text-sm text-slate-700 leading-relaxed">
                <span className="flex h-5 w-5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold items-center justify-center flex-shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Two Column Section: Speech Transcript & Board OCR */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Synchronized Transcript */}
        <Card>
          <CardHeader>
            <div>
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-blue-600" />
                <CardTitle>Synchronized Audio Transcript</CardTitle>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">Speech-to-text correlated with student hand raises</p>
            </div>
            <Badge variant="slate" size="xs">Faster-Whisper</Badge>
          </CardHeader>

          <CardContent className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            {transcript.length === 0 ? (
              <p className="text-xs text-slate-500 italic p-4 text-center">No audio transcripts recorded for this session.</p>
            ) : (
              transcript.map((item) => (
                <div
                  key={item.id}
                  className={`rounded-xl border p-3.5 space-y-1.5 transition-colors ${
                    item.relatedGesture === 'hand_raised'
                      ? 'border-blue-200 bg-blue-50/70'
                      : 'border-slate-200 bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-900">{item.speaker}</span>
                    <div className="flex items-center gap-2">
                      {item.relatedGesture === 'hand_raised' && (
                        <span className="flex items-center gap-1 rounded bg-blue-100 border border-blue-200 px-2 py-0.5 text-[10px] font-bold text-blue-700">
                          <Hand className="h-3 w-3" />
                          Hand Raised Prompt
                        </span>
                      )}
                      <span className="font-mono text-[11px] text-slate-500">{item.timestamp}</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">{item.text}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Right: Board & Slide OCR Extractions */}
        <Card>
          <CardHeader>
            <div>
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-600" />
                <CardTitle>Whiteboard & Slide OCR Notes</CardTitle>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">Detected equations, definitions, and code syntax</p>
            </div>
            <Badge variant="emerald" size="xs">EasyOCR</Badge>
          </CardHeader>

          <CardContent className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            {boardNotes.length === 0 ? (
              <p className="text-xs text-slate-500 italic p-4 text-center">No whiteboard OCR notes captured for this session.</p>
            ) : (
              boardNotes.map((note) => (
                <div key={note.id} className="rounded-xl border border-slate-200 bg-white p-3.5 space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-blue-700 font-semibold uppercase text-[11px]">
                      [{note.boardRegion.replace('_', ' ')}]
                    </span>
                    <span className="font-mono text-[11px] text-slate-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {note.timestamp}
                    </span>
                  </div>

                  <div className="rounded-lg bg-slate-900 border border-slate-800 p-2.5 font-mono text-xs text-emerald-400">
                    {note.detectedText}
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-0.5">
                    {note.tags.map((t) => (
                      <span
                        key={t}
                        className="rounded bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600 border border-slate-200"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Question Moments Tracker */}
      <Card>
        <CardHeader>
          <div>
            <div className="flex items-center gap-2">
              <HelpCircle className="h-4 w-4 text-amber-600" />
              <CardTitle>Student Interaction & Question Incidents</CardTitle>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Moments where verified hand raises triggered instructor discussion
            </p>
          </div>
          <Badge variant="amber" size="xs">Interaction Log</Badge>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {questionMoments.length === 0 ? (
              <p className="col-span-2 text-xs text-slate-500 italic p-4 text-center">No student question moments logged for this session.</p>
            ) : (
              questionMoments.map((q, idx) => (
                <div key={idx} className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-800">{q.studentId}</span>
                    <span className="font-mono text-blue-600 text-[11px]">{q.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-700">{q.promptOrQuestion}</p>
                  <div className="flex items-center gap-1.5 text-[11px] text-emerald-700 pt-1">
                    <CheckCircle className="h-3.5 w-3.5" />
                    <span>Addressed by instructor during lecture</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
export default IntelligencePage

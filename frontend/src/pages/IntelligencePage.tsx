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
import { DataStatusBadge } from '../components/DataStatusBadge'

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
    return <div className="text-slate-400 p-8">Loading multimodal lecture intelligence...</div>
  }

  if (!intel) {
    return (
      <div className="space-y-6">
        {sessions.length > 0 && (
          <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Select Session:</span>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500 font-medium"
              >
                {sessions.map((s) => (
                  <option key={s.sessionId} value={s.sessionId}>
                    {s.sessionId}: {s.title}
                  </option>
                ))}
              </select>
            </div>
            <DataStatusBadge status="REAL" size="sm" />
          </div>
        )}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 text-center backdrop-blur shadow-xl space-y-4">
          <div className="flex justify-center">
            <div className="rounded-full bg-violet-500/10 p-4 border border-violet-500/20">
              <Brain className="h-10 w-10 text-violet-400" />
            </div>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">No Lecture Intelligence Available</h2>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            No speech audio transcription, OCR notes, or question moments recorded for this session. Process classroom footage in Live Monitoring to view multimodal intelligence.
          </p>
        </div>
      </div>
    )
  }

  const { topic, keyConcepts, executiveSummary, transcript, boardNotes, questionMoments } = intel

  return (
    <div className="space-y-6">
      {/* Topic & Concept Header */}
      <div className="rounded-2xl border border-violet-500/30 bg-gradient-to-r from-violet-950/40 via-slate-900/60 to-cyan-950/40 p-6 backdrop-blur shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-violet-500/20 px-2.5 py-1 text-xs font-bold text-violet-300 border border-violet-500/30 flex items-center gap-1.5">
              <Brain className="h-3.5 w-3.5" />
              Multimodal Synthesis
            </span>
            {sessions.length > 0 && (
              <div className="flex items-center gap-1.5 ml-2">
                <span className="text-xs text-slate-400 font-medium">Session:</span>
                <select
                  value={selectedSessionId}
                  onChange={(e) => setSelectedSessionId(e.target.value)}
                  className="rounded-lg border border-slate-700/80 bg-slate-950 px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500 font-medium"
                >
                  {sessions.map((s) => (
                    <option key={s.sessionId} value={s.sessionId}>
                      {s.sessionId}: {s.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <DataStatusBadge status={intel.isDemoData ? 'DEMO DATA' : 'REAL'} size="sm" />
            <DataStatusBadge
              status={intel.isDemoData ? 'NOT CONNECTED' : 'CONNECTED'}
              size="sm"
              tooltip={intel.isDemoData ? 'Demo fallback active' : 'Live Whisper & EasyOCR multimodal fusion'}
            />
          </div>
          <span className="text-xs text-slate-400 font-mono">Whisper Audio + EasyOCR Vision Fusion</span>
        </div>

        <div>
          <h2 className="text-xl lg:text-2xl font-bold text-white tracking-tight">{topic}</h2>
          <div className="flex flex-wrap items-center gap-2 pt-3">
            {keyConcepts.map((concept) => (
              <span
                key={concept}
                className="inline-flex items-center gap-1 rounded-full border border-slate-700/80 bg-slate-800/60 px-3 py-1 text-xs font-medium text-slate-200"
              >
                <Tag className="h-3 w-3 text-cyan-400" />
                {concept}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* AI Executive Summary Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-violet-400" />
            <span>AI Executive Lecture Summary</span>
          </h3>
          <DataStatusBadge status={intel.isDemoData ? 'DEMO DATA' : 'REAL'} size="sm" />
        </div>

        <ul className="space-y-2.5 pt-1">
          {executiveSummary.map((point, index) => (
            <li key={index} className="flex items-start gap-3 text-xs lg:text-sm text-slate-300 leading-relaxed">
              <span className="flex h-5 w-5 rounded-full bg-violet-500/20 text-violet-400 text-xs font-bold items-center justify-center flex-shrink-0 mt-0.5">
                {index + 1}
              </span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Two Column Section: Speech Transcript & Board OCR */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Synchronized Transcript */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-cyan-400" />
                <span>Synchronized Audio Transcript</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Speech-to-text correlated with student hand raises</p>
            </div>
            <DataStatusBadge status={intel.isDemoData ? 'DEMO DATA' : 'REAL'} size="sm" />
          </div>

          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
            {transcript.length === 0 ? (
              <p className="text-xs text-slate-500 italic p-4 text-center">No audio transcripts recorded for this session.</p>
            ) : (
              transcript.map((item) => (
                <div
                  key={item.id}
                  className={`rounded-xl border p-3.5 space-y-1.5 transition-colors ${
                    item.relatedGesture === 'hand_raised'
                      ? 'border-violet-500/40 bg-violet-950/20'
                      : 'border-slate-800/80 bg-slate-950/40'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-200">{item.speaker}</span>
                    <div className="flex items-center gap-2">
                      {item.relatedGesture === 'hand_raised' && (
                        <span className="flex items-center gap-1 rounded bg-violet-500/20 border border-violet-500/40 px-2 py-0.5 text-[10px] font-bold text-violet-300">
                          <Hand className="h-3 w-3" />
                          Hand Raised Prompt
                        </span>
                      )}
                      <span className="font-mono text-[11px] text-slate-500">{item.timestamp}</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{item.text}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Board & Slide OCR Extractions */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-400" />
                <span>Whiteboard & Slide OCR Notes</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Detected equations, definitions, and code syntax</p>
            </div>
            <DataStatusBadge status={intel.isDemoData ? 'DEMO DATA' : 'REAL'} size="sm" />
          </div>

          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
            {boardNotes.length === 0 ? (
              <p className="text-xs text-slate-500 italic p-4 text-center">No whiteboard OCR notes captured for this session.</p>
            ) : (
              boardNotes.map((note) => (
                <div key={note.id} className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-3.5 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-cyan-400 font-semibold uppercase text-[11px]">
                      [{note.boardRegion.replace('_', ' ')}]
                    </span>
                    <span className="font-mono text-[11px] text-slate-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {note.timestamp}
                    </span>
                  </div>

                  <div className="rounded-lg bg-black/60 border border-slate-800 p-2.5 font-mono text-xs text-emerald-300">
                    {note.detectedText}
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-0.5">
                    {note.tags.map((t) => (
                      <span
                        key={t}
                        className="rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400 border border-slate-700/60"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Question Moments Tracker */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <HelpCircle className="h-4 w-4 text-amber-400" />
              <span>Student Interaction & Question Incidents</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Moments where verified hand raises triggered instructor discussion
            </p>
          </div>
          <DataStatusBadge status={intel.isDemoData ? 'DEMO DATA' : 'REAL'} size="sm" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {questionMoments.length === 0 ? (
            <p className="col-span-2 text-xs text-slate-500 italic p-4 text-center">No student question moments logged for this session.</p>
          ) : (
            questionMoments.map((q, idx) => (
              <div key={idx} className="rounded-xl border border-slate-800/90 bg-slate-950/40 p-4 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300">{q.studentId}</span>
                  <span className="font-mono text-cyan-400 text-[11px]">{q.timestamp}</span>
                </div>
                <p className="text-xs text-slate-200">{q.promptOrQuestion}</p>
                <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 pt-1">
                  <CheckCircle className="h-3.5 w-3.5" />
                  <span>Addressed by instructor during lecture</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

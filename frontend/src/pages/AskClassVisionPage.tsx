// frontend/src/pages/AskClassVisionPage.tsx
import React, { useState, useEffect } from 'react'
import {
  Sparkles,
  Search,
  Database,
  BookOpen,
  FileText,
  AlertTriangle,
  HelpCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  History,
} from 'lucide-react'
import { api } from '../services'
import type { RagResponse } from '../types'
import { DataStatusBadge } from '../components/DataStatusBadge'

const SUGGESTED_QUESTIONS = [
  'What was covered regarding gradient descent and optimizers?',
  'Did students ask questions during the dilated convolution topic?',
  'What formula was written on the whiteboard at 09:22?',
  'Summarize student engagement during the chain rule derivation.',
]

interface HistoryItem {
  query: string
  answer: string
  timestamp: string
}

export const AskClassVisionPage: React.FC = () => {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<RagResponse | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (questionText: string) => {
    if (!questionText.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.askQuestion(questionText)
      setResponse(res)
      setHistory((prev) => [
        {
          query: questionText,
          answer: res.answer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
        ...prev.filter((h) => h.query !== questionText),
      ])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to query RAG assistant')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true
    api
      .askQuestion(SUGGESTED_QUESTIONS[0])
      .then((res) => {
        if (mounted) {
          setResponse(res)
          setHistory([
            {
              query: SUGGESTED_QUESTIONS[0],
              answer: res.answer,
              timestamp: '09:45 AM',
            },
          ])
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to query RAG assistant')
          setLoading(false)
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="space-y-6">
      {/* Top Disclaimer Banner */}
      <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 shadow-lg backdrop-blur-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-amber-200">
                RAG Integration Pending — UI Assistant Placeholder
              </h2>
              <DataStatusBadge status="NOT CONNECTED" size="sm" tooltip="Dense vector store & LLM engine not connected" />
              <DataStatusBadge status="DEMO DATA" size="sm" />
            </div>
            <p className="text-xs text-amber-300/80 leading-relaxed">
              This interface is a frontend design mockup for the upcoming lecture Retrieval-Augmented
              Generation (RAG) pipeline. No real embedding index or LLM backend is active yet. All
              answers and source citations are strictly canned demonstration entries pulled from the
              demo-data layer.
            </p>
          </div>
        </div>
      </div>

      {/* Query Bar Card */}
      <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-violet-400" />
            <h1 className="text-lg font-semibold text-slate-100">Ask ClassVision</h1>
          </div>
          <div className="flex items-center gap-2">
            <DataStatusBadge status="DEMO DATA" size="xs" />
            <span className="text-xs text-slate-400 font-mono">
              Grounding: CS402 (Audio + Board OCR)
            </span>
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSearch(query)
          }}
          className="relative"
        >
          <div className="relative flex items-center">
            <Search className="absolute left-4 h-5 w-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about lecture concepts, student queries, or whiteboard derivations..."
              className="w-full rounded-xl border border-slate-700 bg-slate-900/90 py-3.5 pl-12 pr-28 text-sm text-slate-100 placeholder-slate-500 transition-colors focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-2 inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-cyan-600 px-4 py-2 text-xs font-medium text-white shadow-md transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <span>Query</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Suggested Queries */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 flex items-center gap-1">
            <HelpCircle className="h-3.5 w-3.5 text-cyan-400" />
            Suggested prompts:
          </span>
          {SUGGESTED_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(q)
                handleSearch(q)
              }}
              className="rounded-full border border-slate-700 bg-slate-800/60 px-3 py-1 text-xs text-slate-300 transition-colors hover:border-violet-500/50 hover:bg-violet-950/30 hover:text-white"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Answer, Citations & History Grid */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4 text-xs text-red-300">
          {error}
        </div>
      )}

      {response && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Synthesized Answer & Conversation History */}
          <div className="lg:col-span-2 space-y-6">
            {/* Active Answer Card */}
            <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600/20 text-violet-400 border border-violet-500/30">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-100">Synthesized Response</h3>
                    <p className="text-[11px] text-slate-400 font-mono">
                      Query: &quot;{response.query}&quot;
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <DataStatusBadge status="DEMO DATA" size="sm" />
                  <span className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-[11px] font-mono text-cyan-300">
                    Confidence: {(response.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="pt-5 pb-2 text-sm text-slate-200 leading-relaxed space-y-3">
                <p>{response.answer}</p>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  <span>Verified locally against offline session vector cache</span>
                </div>
                <span className="font-mono text-[10px] text-slate-500">
                  Engine: RAG-DenseRetriever (Planned)
                </span>
              </div>
            </div>

            {/* Conversation History Panel */}
            <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/60 p-6 shadow-md backdrop-blur-sm space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <History className="h-4 w-4 text-violet-400" />
                  <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                    Session Conversation History
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  {history.length} logged queries
                </span>
              </div>

              <div className="space-y-2.5 pt-1">
                {history.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setQuery(item.query)
                      handleSearch(item.query)
                    }}
                    className="p-3 rounded-xl border border-slate-800/80 bg-slate-900/50 hover:border-slate-700 cursor-pointer transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-200">{item.query}</span>
                      <span className="text-[10px] font-mono text-slate-500">{item.timestamp}</span>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1 italic">&quot;{item.answer}&quot;</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Source Documents & References */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-slate-100">Grounded Citations</h3>
                </div>
                <DataStatusBadge status="DEMO DATA" size="xs" />
              </div>

              <div className="pt-4 space-y-3">
                {response.sources.map((src, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-slate-800/90 bg-slate-900/60 p-3.5 space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-violet-300">
                        {src.sourceType === 'transcript' ? (
                          <FileText className="h-3.5 w-3.5 text-violet-400" />
                        ) : (
                          <BookOpen className="h-3.5 w-3.5 text-cyan-400" />
                        )}
                        <span>{src.title}</span>
                      </div>
                      {src.timestamp && (
                        <span className="inline-flex items-center gap-1 font-mono text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                          <Clock className="h-2.5 w-2.5" />
                          {src.timestamp}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 italic bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/60 font-mono">
                      &quot;{src.snippet}&quot;
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 leading-snug">
                Sources are aligned with Whisper speech tokens and EasyOCR whiteboard bounding
                boxes.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

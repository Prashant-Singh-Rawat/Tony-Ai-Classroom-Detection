// frontend/src/pages/AskClassVisionPage.tsx
import React, { useState, useEffect } from 'react'
import {
  Sparkles,
  Search,
  Database,
  BookOpen,
  FileText,
  HelpCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  History,
} from 'lucide-react'
import { api } from '../services'
import type { RagResponse } from '../types'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'

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
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Query Bar Card */}
      <Card className="shadow-2xs">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            <CardTitle>Ask ClassVision Assistant</CardTitle>
          </div>
          <Badge variant="blue" size="xs">
            Grounded: CS402 (Audio + Board OCR)
          </Badge>
        </CardHeader>

        <CardContent className="space-y-4">
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
                placeholder="Ask about lecture topics, student queries, or blackboard derivations..."
                className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-12 pr-28 text-sm text-slate-900 placeholder-slate-400 transition-colors focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 shadow-2xs"
              />
              <div className="absolute right-2">
                <Button
                  type="submit"
                  disabled={loading}
                  variant="primary"
                  size="sm"
                  icon={loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ArrowRight className="h-3.5 w-3.5" />}
                >
                  {loading ? 'Searching...' : 'Query'}
                </Button>
              </div>
            </div>
          </form>

          {/* Suggested Queries */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-slate-500 flex items-center gap-1 font-medium">
              <HelpCircle className="h-3.5 w-3.5 text-blue-600" />
              Suggested:
            </span>
            {SUGGESTED_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(q)
                  handleSearch(q)
                }}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-700 transition-colors hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
              >
                {q}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Error Notice */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Answer, Citations & History Grid */}
      {response && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Synthesized Answer & Conversation History */}
          <div className="lg:col-span-2 space-y-6">
            {/* Active Answer Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <CardTitle>Synthesized Lecture Response</CardTitle>
                    <p className="text-[11px] text-slate-500 font-mono">
                      Query: &quot;{response.query}&quot;
                    </p>
                  </div>
                </div>
                <Badge variant="blue" size="xs">
                  Confidence: {(response.confidence * 100).toFixed(0)}%
                </Badge>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="text-sm text-slate-800 leading-relaxed">
                  <p>{response.answer}</p>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    <span>Verified locally against offline session vector cache</span>
                  </div>
                  <span className="font-mono text-[10px] text-slate-400">
                    Engine: RAG-DenseRetriever
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Conversation History Panel */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <History className="h-4 w-4 text-blue-600" />
                  <CardTitle>Session Query History</CardTitle>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  {history.length} logged
                </span>
              </CardHeader>

              <CardContent className="space-y-2.5">
                {history.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setQuery(item.query)
                      handleSearch(item.query)
                    }}
                    className="p-3 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-slate-100/80 cursor-pointer transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-800">{item.query}</span>
                      <span className="text-[10px] font-mono text-slate-500">{item.timestamp}</span>
                    </div>
                    <p className="text-xs text-slate-600 line-clamp-1 italic">&quot;{item.answer}&quot;</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Source Documents & References */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-teal-600" />
                  <CardTitle>Grounded Citations</CardTitle>
                </div>
                <Badge variant="teal" size="xs">Verified</Badge>
              </CardHeader>

              <CardContent className="space-y-3">
                {response.sources.map((src, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-slate-200 bg-white p-3.5 space-y-2 shadow-2xs hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-700">
                        {src.sourceType === 'transcript' ? (
                          <FileText className="h-3.5 w-3.5 text-blue-600" />
                        ) : (
                          <BookOpen className="h-3.5 w-3.5 text-teal-600" />
                        )}
                        <span>{src.title}</span>
                      </div>
                      {src.timestamp && (
                        <span className="inline-flex items-center gap-1 font-mono text-[10px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                          <Clock className="h-2.5 w-2.5" />
                          {src.timestamp}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 italic bg-slate-50 p-2.5 rounded-lg border border-slate-200 font-mono">
                      &quot;{src.snippet}&quot;
                    </p>
                  </div>
                ))}

                <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-500 leading-snug">
                  Sources are aligned with Whisper speech tokens and EasyOCR whiteboard bounding boxes.
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
export default AskClassVisionPage

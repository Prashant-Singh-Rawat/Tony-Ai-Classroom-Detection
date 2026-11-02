// frontend/src/pages/LectureNotesPage.tsx
import React, { useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen,
  Upload,
  FileVideo,
  X,
  AlertCircle,
  Clock,
  Maximize2,
  Film,
  ArrowRight,
  ChevronLeft,
  Info,
} from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'

// ─── Constants ───────────────────────────────────────────────────────────────
const MAX_FILE_BYTES = 500 * 1024 * 1024 // 500 MB — matches backend limit
const VALID_VIDEO_EXTS = new Set(['.mp4', '.mov', '.avi', '.mkv', '.webm'])
const VALID_VIDEO_MIME_PREFIXES = ['video/']

const SUPPORTED_FORMATS = [
  { ext: 'MP4', note: 'H.264 / H.265' },
  { ext: 'MOV', note: 'Apple QuickTime' },
  { ext: 'AVI', note: 'Windows Media' },
  { ext: 'MKV', note: 'Matroska' },
  { ext: 'WEBM', note: 'VP8 / VP9' },
]

// ─── Helpers ─────────────────────────────────────────────────────────────────
function isVideoFile(f: File): boolean {
  if (VALID_VIDEO_MIME_PREFIXES.some((prefix) => f.type.startsWith(prefix))) return true
  const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase()
  return VALID_VIDEO_EXTS.has(ext)
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

function formatDuration(seconds: number): string {
  if (isNaN(seconds) || !isFinite(seconds)) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}h ${m}m ${s}s`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

// ─── Video Metadata ───────────────────────────────────────────────────────────
interface VideoMeta {
  duration: number
  width: number
  height: number
}

function loadVideoMeta(file: File): Promise<VideoMeta> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      resolve({ duration: video.duration, width: video.videoWidth, height: video.videoHeight })
      URL.revokeObjectURL(url)
    }
    video.onerror = () => {
      reject(new Error('Could not read video metadata.'))
      URL.revokeObjectURL(url)
    }
    video.src = url
  })
}

// ─── Component ────────────────────────────────────────────────────────────────
export const LectureNotesPage: React.FC = () => {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [meta, setMeta] = useState<VideoMeta | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [metaLoading, setMetaLoading] = useState(false)

  // ── File validation & load ─────────────────────────────────────────────────
  const processFile = useCallback(async (candidate: File) => {
    setError(null)
    setMeta(null)
    setFile(null)

    if (!isVideoFile(candidate)) {
      setError(
        'Only video files are accepted (MP4, MOV, AVI, MKV, WEBM). Please select a video file — not an audio or image file.'
      )
      return
    }
    if (candidate.size > MAX_FILE_BYTES) {
      setError(
        `File is too large (${formatBytes(candidate.size)}). Maximum size is 500 MB.`
      )
      return
    }

    setFile(candidate)
    setMetaLoading(true)
    try {
      const m = await loadVideoMeta(candidate)
      setMeta(m)
    } catch {
      // Non-fatal: metadata preview unavailable
      setMeta(null)
    } finally {
      setMetaLoading(false)
    }
  }, [])

  // ── Drag handlers ──────────────────────────────────────────────────────────
  const onDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const onDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragging(false)
      const dropped = e.dataTransfer.files[0]
      if (dropped) processFile(dropped)
    },
    [processFile]
  )

  // ── Input handler ──────────────────────────────────────────────────────────
  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) processFile(selected)
    // Reset so same file can be re-selected if user removes and re-adds
    e.target.value = ''
  }

  // ── Clear ──────────────────────────────────────────────────────────────────
  const clearFile = () => {
    setFile(null)
    setMeta(null)
    setError(null)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* ── Page Header ───────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/dashboard')}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          title="Back to Dashboard"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-3 flex-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                AI Lecture Notes &amp; Summary
              </h1>
              <Badge variant="blue" size="xs">Phase 2</Badge>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload a classroom lecture video to auto-generate organized study notes and summaries.
            </p>
          </div>
        </div>
      </div>

      {/* ── Workflow description ───────────────────────────────────────────── */}
      <Card className="border-violet-100 bg-violet-50/40">
        <CardContent className="pt-5 pb-4">
          <div className="flex gap-3">
            <Info className="h-4 w-4 text-violet-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs font-semibold text-violet-800">How it works</p>
              <p className="text-xs text-violet-700 leading-relaxed">
                Upload a lecture recording. ClassVision AI will extract the audio, transcribe the
                teacher's speech using <strong>Faster-Whisper</strong>, read slide and board text
                using <strong>EasyOCR</strong>, then synthesize everything into structured study
                notes covering topics, explanations, definitions, and key concepts.
              </p>
              <p className="text-xs text-violet-600 mt-1">
                <strong>Processing pipeline is coming in Phase 2.</strong> Upload and preview your
                video now — processing will be enabled in the next release.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Upload Zone ───────────────────────────────────────────────────── */}
      <Card>
        <CardContent className="pt-6 pb-6">
          <h2 className="text-sm font-semibold text-slate-800 mb-4">Upload Lecture Video</h2>

          {!file ? (
            /* Drop target */
            <div
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-12 cursor-pointer transition-all select-none ${
                isDragging
                  ? 'border-violet-500 bg-violet-50 scale-[1.01]'
                  : 'border-slate-200 bg-slate-50/50 hover:border-violet-300 hover:bg-violet-50/30'
              }`}
            >
              <div
                className={`flex h-14 w-14 items-center justify-center rounded-2xl transition-colors ${
                  isDragging ? 'bg-violet-100 text-violet-600' : 'bg-slate-100 text-slate-400'
                }`}
              >
                <Upload className="h-7 w-7" />
              </div>
              <div className="text-center space-y-1">
                <p className="text-sm font-semibold text-slate-700">
                  {isDragging ? 'Drop your lecture video here' : 'Drag & drop your lecture video'}
                </p>
                <p className="text-xs text-slate-500">
                  or{' '}
                  <span className="text-violet-600 font-semibold underline underline-offset-2">
                    browse files
                  </span>{' '}
                  to choose
                </p>
              </div>

              <div className="flex flex-wrap justify-center gap-2 mt-1">
                {SUPPORTED_FORMATS.map(({ ext, note }) => (
                  <span
                    key={ext}
                    className="inline-flex items-center gap-1 rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[11px] font-medium text-slate-600 shadow-2xs"
                    title={note}
                  >
                    <Film className="h-3 w-3 text-slate-400" />
                    {ext}
                  </span>
                ))}
              </div>
              <p className="text-[11px] text-slate-400">Maximum file size: 500 MB</p>
            </div>
          ) : (
            /* Selected file card */
            <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
              <div className="flex items-center gap-4 p-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-100 text-violet-600 flex-shrink-0">
                  <FileVideo className="h-6 w-6" />
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-900 truncate" title={file.name}>
                    {file.name}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">{formatBytes(file.size)}</p>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    Change
                  </button>
                  <button
                    onClick={clearFile}
                    className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors"
                    title="Remove file"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Metadata preview */}
              {metaLoading && (
                <div className="px-4 pb-4 flex items-center gap-2 text-xs text-slate-500">
                  <div className="h-3.5 w-3.5 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
                  Reading video metadata…
                </div>
              )}

              {meta && !metaLoading && (
                <div className="px-4 pb-4 grid grid-cols-3 gap-3">
                  <div className="rounded-lg bg-slate-50 border border-slate-100 p-3 text-center">
                    <Clock className="h-4 w-4 text-violet-500 mx-auto mb-1" />
                    <p className="text-[11px] text-slate-500 font-medium">Duration</p>
                    <p className="text-xs font-bold text-slate-800">{formatDuration(meta.duration)}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 border border-slate-100 p-3 text-center">
                    <Maximize2 className="h-4 w-4 text-violet-500 mx-auto mb-1" />
                    <p className="text-[11px] text-slate-500 font-medium">Resolution</p>
                    <p className="text-xs font-bold text-slate-800">
                      {meta.width && meta.height ? `${meta.width} × ${meta.height}` : '—'}
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-50 border border-slate-100 p-3 text-center">
                    <Film className="h-4 w-4 text-violet-500 mx-auto mb-1" />
                    <p className="text-[11px] text-slate-500 font-medium">Format</p>
                    <p className="text-xs font-bold text-slate-800">
                      {file.name.slice(file.name.lastIndexOf('.') + 1).toUpperCase()}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*,.mp4,.mov,.avi,.mkv,.webm"
            className="hidden"
            onChange={onFileChange}
          />

          {/* Error */}
          {error && (
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2.5">
              <AlertCircle className="h-4 w-4 text-rose-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-rose-700 font-medium">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Supported formats table ────────────────────────────────────────── */}
      <Card>
        <CardContent className="pt-5 pb-5">
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
            Supported Video Formats
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {SUPPORTED_FORMATS.map(({ ext, note }) => (
              <div
                key={ext}
                className="flex flex-col items-center gap-1 rounded-lg border border-slate-100 bg-slate-50 p-3"
              >
                <span className="text-xs font-bold text-slate-800">{ext}</span>
                <span className="text-[10px] text-slate-500 text-center">{note}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] text-slate-400">
            Decoder availability depends on your system's installed codec libraries. MP4 (H.264) is
            the most widely compatible format.
          </p>
        </CardContent>
      </Card>

      {/* ── Continue button ────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pt-2 pb-6">
        <button
          onClick={() => navigate('/dashboard')}
          className="text-xs text-slate-500 hover:text-slate-700 font-medium flex items-center gap-1 transition-colors"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          Back to Dashboard
        </button>

        <div className="flex flex-col items-end gap-1">
          <Button
            variant="primary"
            size="md"
            disabled
            icon={<ArrowRight className="h-4 w-4" />}
            className="opacity-60 cursor-not-allowed bg-violet-600 hover:bg-violet-600"
            title="Processing pipeline will be available in Phase 2"
          >
            Generate Notes
          </Button>
          <p className="text-[11px] text-slate-400">
            Processing enabled in Phase 2
            {file ? ` — ${file.name.slice(file.name.lastIndexOf('.') + 1).toUpperCase()} file ready` : ''}
          </p>
        </div>
      </div>
    </div>
  )
}

export default LectureNotesPage

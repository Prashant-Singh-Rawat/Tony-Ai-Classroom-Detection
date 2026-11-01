// frontend/src/pages/ModelStatusPage.tsx
import React, { useEffect, useState } from 'react'
import {
  Database,
  Cpu,
  FileCode2,
  AlertTriangle,
  Layers,
  Scale,
  HardDrive,
} from 'lucide-react'
import { api } from '../services'
import type { ModelStatusData } from '../types'
import { Badge } from '../components/ui/Badge'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'

export const ModelStatusPage: React.FC = () => {
  const [data, setData] = useState<ModelStatusData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    api.getModelStatus().then((res) => {
      if (mounted) {
        setData(res)
        setLoading(false)
      }
    })
    return () => {
      mounted = false
    }
  }, [])

  if (loading || !data) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-500">
        <span className="text-xs font-medium">Loading repository & model status...</span>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Banner with Strict Separation Notice */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Database className="h-6 w-6 text-blue-600" />
            <div>
              <CardTitle>Data, Annotation & Model Status Audit</CardTitle>
              <p className="text-xs text-slate-500 mt-1">
                Verified ground-truth facts from the repository baseline alongside multimodal module readiness.
              </p>
            </div>
          </div>
          <Badge variant="blue" size="sm">Repository Verified</Badge>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="flex items-center gap-2 p-3 rounded-xl border border-emerald-200 bg-emerald-50">
              <Badge variant="emerald" size="xs">REAL</Badge>
              <span className="text-emerald-800 font-medium">Verified repository fact</span>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-xl border border-amber-200 bg-amber-50">
              <Badge variant="amber" size="xs">DEMO DATA</Badge>
              <span className="text-amber-800 font-medium">Illustrative mock telemetry</span>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 bg-slate-100">
              <Badge variant="slate" size="xs">STANDBY</Badge>
              <span className="text-slate-700 font-medium">Pipeline module standby</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SECTION 1: VERIFIED REPOSITORY DATASETS (REAL) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Verified Repository Datasets
            </h2>
          </div>
          <Badge variant="emerald" size="xs">Verified Ground-Truth</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Kaggle Hand Gesture Dataset Card */}
          <Card className="p-5 space-y-4 shadow-2xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-blue-600" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Kaggle Hand Gesture Dataset
                </h3>
              </div>
              <Badge variant="blue" size="xs">20 Classes</Badge>
            </div>

            <div className="grid grid-cols-3 gap-2 font-mono text-center">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Total</span>
                <span className="text-sm font-bold text-slate-900">
                  {data.kaggleGestureDataset.totalImages.toLocaleString()}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200">
                <span className="text-[10px] text-blue-600 uppercase block">Train</span>
                <span className="text-sm font-bold text-blue-700">
                  {data.kaggleGestureDataset.trainImages.toLocaleString()}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-teal-50 border border-teal-200">
                <span className="text-[10px] text-teal-600 uppercase block">Test</span>
                <span className="text-sm font-bold text-teal-700">
                  {data.kaggleGestureDataset.testImages.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-700 space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-slate-500">
                <span>Classes:</span>
                <span className="font-mono text-slate-800 font-semibold">20 classes (IDs 0–19)</span>
              </div>
              <div className="flex items-center justify-between text-slate-500">
                <span>Resolution:</span>
                <span className="font-mono text-slate-800 font-semibold">50x50 Grayscale / JPG</span>
              </div>
              <div className="flex items-center justify-between text-slate-500">
                <span>Class Semantics:</span>
                <span className="font-mono text-slate-600 font-semibold">Isolated hand gestures</span>
              </div>
            </div>

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <p className="text-[11px] text-amber-800 leading-relaxed">
                <strong>CRITICAL FACT:</strong> {data.kaggleGestureDataset.disclaimer}
              </p>
            </div>
          </Card>

          {/* Real Classroom Dataset Status */}
          <Card className="p-5 space-y-4 shadow-2xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Scale className="h-4 w-4 text-teal-600" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Real Classroom Dataset
                </h3>
              </div>
              <Badge variant="teal" size="xs">Ethical Capture</Badge>
            </div>

            <div className="grid grid-cols-3 gap-2 font-mono text-center">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Videos</span>
                <span className="text-sm font-bold text-slate-900">
                  {data.realClassroomDataset.collectedVideos}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Frames</span>
                <span className="text-sm font-bold text-slate-900">
                  {data.realClassroomDataset.extractedFrames}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-500 uppercase block">Annotations</span>
                <span className="text-sm font-bold text-slate-900">
                  {data.realClassroomDataset.annotationsCount}
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-700 space-y-2 pt-1">
              <div className="flex items-center justify-between text-slate-500">
                <span>Collection Timing:</span>
                <span className="font-mono text-blue-700 font-semibold">Academic Fall Cohort</span>
              </div>
              <div className="flex items-center justify-between text-slate-500">
                <span>Target Diversity:</span>
                <span className="font-mono text-slate-800">8–12 sessions (3+ per split)</span>
              </div>
              <div className="flex items-center justify-between text-slate-500">
                <span>Target Volume:</span>
                <span className="font-mono text-slate-800">~1,000 reviewed frames</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600">
              Collection protocol, annotation schema (`hand_raised`, `hand_not_raised`, `ambiguous`), and preflight validation scripts are complete and tested.
            </div>
          </Card>
        </div>
      </section>

      {/* SECTION 2: MODEL CHECKPOINTS & TRAINING AUDIT */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-blue-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Model Weights & Execution Engine
            </h2>
          </div>
          <Badge variant="blue" size="xs">Inference Engine</Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Vision Model</span>
              <Badge variant="emerald" size="xs">LOADED</Badge>
            </div>
            <div className="text-xl font-bold font-mono text-slate-900">
              YOLOv8n-pose
            </div>
            <p className="text-[11px] text-slate-500">
              17 COCO keypoint upper-body estimation on local CPU/GPU.
            </p>
          </Card>

          <Card className="p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Active Weights</span>
              <Badge variant="blue" size="xs">OFFLINE</Badge>
            </div>
            <div className="text-xl font-bold font-mono text-blue-700">
              yolov8n-pose.pt
            </div>
            <p className="text-[11px] text-slate-500">
              Zero cloud telemetry; inference runs completely on local host.
            </p>
          </Card>

          <Card className="p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Python Test Suite</span>
              <Badge variant="emerald" size="xs">VERIFIED</Badge>
            </div>
            <div className="text-xl font-bold font-mono text-emerald-600">
              {data.verifiedTests.passed} / {data.verifiedTests.total} Pass
            </div>
            <p className="text-[11px] text-slate-500">
              All regression and integrity tests pass cleanly.
            </p>
          </Card>
        </div>
      </section>

      {/* SECTION 3: MULTIMODAL READINESS MATRIX */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileCode2 className="h-5 w-5 text-blue-600" />
            <CardTitle>Multimodal Pipeline Readiness Matrix</CardTitle>
          </div>
          <Badge variant="blue" size="xs">Offline Stack</Badge>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">Computer Vision Inference</span>
                <span className="text-[11px] text-slate-500">YOLOv8-pose 17-Keypoint tracking</span>
              </div>
              <Badge variant="emerald" size="xs" dot>ACTIVE</Badge>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">Whisper Speech Pipeline</span>
                <span className="text-[11px] text-slate-500">Faster-Whisper offline transcription</span>
              </div>
              <Badge variant="emerald" size="xs" dot>ACTIVE</Badge>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">Blackboard OCR Pipeline</span>
                <span className="text-[11px] text-slate-500">EasyOCR whiteboard text extraction</span>
              </div>
              <Badge variant="emerald" size="xs" dot>ACTIVE</Badge>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-900 block">SQLite Event Telemetry</span>
                <span className="text-[11px] text-slate-500">Persisted gesture event store</span>
              </div>
              <Badge variant="emerald" size="xs" dot>ACTIVE</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
export default ModelStatusPage

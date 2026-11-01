// frontend/src/pages/ModelStatusPage.tsx
import React, { useEffect, useState } from 'react'
import {
  Database,
  Cpu,
  FileCode2,
  AlertTriangle,
  Layers,
  Scale,
  Activity,
  HardDrive,
} from 'lucide-react'
import { api } from '../services'
import type { ModelStatusData } from '../types'
import { DataStatusBadge } from '../components/DataStatusBadge'

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
      <div className="flex h-64 items-center justify-center text-slate-400">
        <span className="font-mono text-sm">Loading repository & model status...</span>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Top Banner with Strict Separation Notice */}
      <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/90 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-2.5">
              <Database className="h-6 w-6 text-cyan-400" />
              <h1 className="text-xl font-bold text-slate-100">
                Data, Annotation & Model Status Audit
              </h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Verified ground-truth facts from the Phase 0.8 repository baseline alongside unintegrated AI module status.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <DataStatusBadge status="REAL" />
            <span className="text-xs text-slate-400 font-mono hidden md:inline">
              Repo Snapshot Verified
            </span>
          </div>
        </div>

        {/* Legend Explainer */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="flex items-center gap-2 p-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5">
            <DataStatusBadge status="REAL" size="xs" />
            <span className="text-slate-300">Verified repository fact</span>
          </div>
          <div className="flex items-center gap-2 p-2.5 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <DataStatusBadge status="DEMO DATA" size="xs" />
            <span className="text-slate-300">Illustrative mock telemetry</span>
          </div>
          <div className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-700 bg-slate-800/40">
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
            <span className="text-slate-400">Pipeline not yet built</span>
          </div>
        </div>
      </div>

      {/* SECTION 1: VERIFIED REPOSITORY DATASETS (REAL) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-emerald-400" />
            <h2 className="text-base font-semibold text-slate-100">
              Verified Repository Datasets
            </h2>
          </div>
          <DataStatusBadge status="REAL" size="sm" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Kaggle Hand Gesture Dataset Card */}
          <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-violet-400" />
                <h3 className="text-sm font-semibold text-slate-200">
                  Kaggle Hand Gesture Dataset
                </h3>
              </div>
              <DataStatusBadge status="REAL" size="xs" />
            </div>

            <div className="grid grid-cols-3 gap-2 font-mono text-center">
              <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Total</span>
                <span className="text-sm font-bold text-slate-100">
                  {data.kaggleGestureDataset.totalImages.toLocaleString()}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Train</span>
                <span className="text-sm font-bold text-violet-300">
                  {data.kaggleGestureDataset.trainImages.toLocaleString()}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Test</span>
                <span className="text-sm font-bold text-cyan-300">
                  {data.kaggleGestureDataset.testImages.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-300 space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-slate-400">
                <span>Classes:</span>
                <span className="font-mono text-slate-200">20 classes (IDs 0–19)</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Resolution:</span>
                <span className="font-mono text-slate-200">50x50 Grayscale / JPG</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Class Semantics:</span>
                <span className="font-mono text-amber-300 font-semibold">NOT VERIFIED</span>
              </div>
            </div>

            {/* Kaggle Gesture Disclaimer Notice */}
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <p className="text-[11px] text-amber-200 leading-relaxed">
                <strong>CRITICAL FACT:</strong> {data.kaggleGestureDataset.disclaimer}
              </p>
            </div>
          </div>

          {/* Real Classroom Dataset Status */}
          <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="h-4 w-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-slate-200">
                  Real Classroom Dataset
                </h3>
              </div>
              <DataStatusBadge status="REAL" size="xs" />
            </div>

            <div className="grid grid-cols-3 gap-2 font-mono text-center">
              <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Videos</span>
                <span className="text-sm font-bold text-slate-100">
                  {data.realClassroomDataset.collectedVideos}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Frames</span>
                <span className="text-sm font-bold text-slate-100">
                  {data.realClassroomDataset.extractedFrames}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Annotations</span>
                <span className="text-sm font-bold text-slate-100">
                  {data.realClassroomDataset.annotationsCount}
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-300 space-y-2 pt-1">
              <div className="flex items-center justify-between text-slate-400">
                <span>Collection Timing:</span>
                <span className="font-mono text-cyan-300">After 12 October 2026</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Target Diversity:</span>
                <span className="font-mono text-slate-200">8–12 sessions (3+ per split)</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Target Volume:</span>
                <span className="font-mono text-slate-200">~1,000 reviewed frames</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-[11px] text-slate-400">
              Collection protocol, annotation schema (`hand_raised`, `hand_not_raised`, `ambiguous`), and preflight validation scripts are complete and tested.
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: MODEL CHECKPOINTS & TRAINING AUDIT */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-violet-400" />
            <h2 className="text-base font-semibold text-slate-100">
              Model Checkpoints & Training Engine
            </h2>
          </div>
          <DataStatusBadge status="REAL" size="sm" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-5 shadow-xl backdrop-blur-md space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Model Checkpoints</span>
              <DataStatusBadge status="REAL" size="xs" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100">
              {data.modelCheckpointsCount}
            </div>
            <p className="text-[11px] text-slate-400">
              Zero model checkpoint files (`.pt`, `.pth`, `.onnx`) exist in repo.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-5 shadow-xl backdrop-blur-md space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Active Checkpoint</span>
              <DataStatusBadge status="REAL" size="xs" />
            </div>
            <div className="text-lg font-bold font-mono text-amber-300">
              {data.activeCheckpoint}
            </div>
            <p className="text-[11px] text-slate-400">
              Training prohibited until real classroom dataset is collected.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-5 shadow-xl backdrop-blur-md space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Python Test Suite</span>
              <DataStatusBadge status="REAL" size="xs" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {data.verifiedTests.passed} / {data.verifiedTests.total} Pass
            </div>
            <p className="text-[11px] text-slate-400">
              All Phase 0.1–0.8 regression and integrity tests pass cleanly.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 3: EVALUATION METRICS (NOT CONNECTED / UNAVAILABLE) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-slate-400" />
            <h2 className="text-base font-semibold text-slate-100">
              Model Evaluation Benchmarks
            </h2>
          </div>
          <DataStatusBadge status="NOT CONNECTED" size="sm" />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Precision (Hand Raised)', value: data.evaluationMetrics.precision },
            { label: 'Recall (Hand Raised)', value: data.evaluationMetrics.recall },
            { label: 'F1-Score (Macro)', value: data.evaluationMetrics.f1Score },
            { label: 'mAP@0.5 (Person BBox)', value: data.evaluationMetrics.map50 },
          ].map((item, idx) => (
            <div
              key={idx}
              className="rounded-2xl border border-slate-800 bg-[#0f111a]/60 p-5 shadow-md backdrop-blur-sm space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">{item.label}</span>
                <DataStatusBadge status="NOT CONNECTED" size="xs" />
              </div>
              <div className="text-xs font-mono text-slate-400 italic font-semibold">
                {item.value}
              </div>
              <span className="text-[10px] text-slate-500 block">
                Target: &gt;0.85 post Phase 2 training
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 4: UNCONNECTED PIPELINE CAPABILITIES */}
      <section className="rounded-2xl border border-slate-800 bg-[#0f111a]/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <FileCode2 className="h-5 w-5 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200">
              Multimodal Pipeline Readiness Matrix
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">Phase 0.9 Status</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">Computer Vision Inference</span>
              <span className="text-[11px] text-slate-400">YOLO-Pose / Keypoint pipeline</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">Whisper Speech Pipeline</span>
              <span className="text-[11px] text-slate-400">Offline lecture audio transcription</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">Blackboard OCR Pipeline</span>
              <span className="text-[11px] text-slate-400">EasyOCR whiteboard text extraction</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>

          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 block">RAG Question Answering</span>
              <span className="text-[11px] text-slate-400">Vector store over multimodal tokens</span>
            </div>
            <DataStatusBadge status="NOT CONNECTED" size="xs" />
          </div>
        </div>
      </section>
    </div>
  )
}

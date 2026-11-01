// frontend/src/components/Layout.tsx
import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { AlertCircle } from 'lucide-react'

export const Layout: React.FC = () => {
  const location = useLocation()

  const getPageMeta = (pathname: string) => {
    switch (pathname) {
      case '/dashboard':
        return {
          title: 'Classroom Intelligence Overview',
          subtitle: 'Live lecture participation telemetry and activity indicators',
        }
      case '/live':
      case '/monitoring':
        return {
          title: 'Live Classroom Monitoring',
          subtitle: 'Real-time webcam video stream, YOLOv8-pose estimation, and gesture tracking',
        }
      case '/analytics':
        return {
          title: 'Classroom Analytics & Gesture Trends',
          subtitle: 'Temporal participation distributions and cross-session engagement comparisons',
        }
      case '/intelligence':
        return {
          title: 'Lecture Intelligence (Whisper + OCR)',
          subtitle: 'Synchronized lecture transcription, blackboard notes, and executive summaries',
        }
      case '/ask':
        return {
          title: 'Ask ClassVision (RAG Assistant)',
          subtitle: 'Grounded question answering over lecture speech and blackboard extractions',
        }
      case '/reports':
        return {
          title: 'Session & Analytics Reports',
          subtitle: 'Exportable classroom dossiers and multi-hall participation summaries',
        }
      case '/model-status':
        return {
          title: 'Dataset, Annotation & Model Status Audit',
          subtitle: 'Verified repository ground truth, Kaggle dataset status, and model readiness',
        }
      case '/settings':
        return {
          title: 'System & Privacy Settings',
          subtitle: 'Camera configuration, storage roots, and offline privacy safeguards',
        }
      default:
        return {
          title: 'ClassVision AI Dashboard',
          subtitle: 'AI-Powered Multimodal Classroom Intelligence System',
        }
    }
  }

  const { title, subtitle } = getPageMeta(location.pathname)

  const isRealMode = import.meta.env.VITE_USE_DEMO_DATA === 'false'

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#08090e] text-slate-100 font-sans">
      <Sidebar />

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Persistent top notification banner */}
        <div className={`px-4 py-1.5 border-b flex items-center justify-between text-[11px] ${
          isRealMode 
            ? 'bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-violet-500/20 border-emerald-500/30 text-emerald-200' 
            : 'bg-gradient-to-r from-amber-500/20 via-violet-500/20 to-cyan-500/20 border-amber-500/30 text-amber-200'
        }`}>
          <div className="flex items-center gap-2">
            <AlertCircle className={`h-3.5 w-3.5 flex-shrink-0 ${isRealMode ? 'text-emerald-400' : 'text-amber-400'}`} />
            <span>
              {isRealMode ? (
                <><strong>CLASSVISION AI — LIVE REAL MODE</strong> — Active FastAPI Backend connected (YOLOv8 Pose + Faster-Whisper + EasyOCR + SQLite). Live Telemetry active.</>
              ) : (
                <><strong>PHASE 0.9 TRUTH-LABELED DASHBOARD</strong> — Distinctly classified into <strong>REAL</strong> (verified repository facts), <strong>DEMO DATA</strong> (illustrative values), and <strong>NOT CONNECTED</strong> (unintegrated AI modules).</>
              )}
            </span>
          </div>
          <span className={`font-mono text-[10px] uppercase tracking-wider hidden md:inline-block ${isRealMode ? 'text-emerald-400' : 'text-amber-400'}`}>
            {isRealMode ? 'VITE_USE_DEMO_DATA = FALSE' : 'VITE_USE_DEMO_DATA = TRUE'}
          </span>
        </div>

        <Topbar title={title} subtitle={subtitle} />

        <main className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

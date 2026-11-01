// frontend/src/components/Layout.tsx
import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export const Layout: React.FC = () => {
  const location = useLocation()

  const getPageMeta = (pathname: string): { title: string; subtitle?: string } => {
    switch (pathname) {
      case '/':
      case '/dashboard':
        return {
          title: 'Classroom Overview',
          subtitle: 'Institutional analytics and session activity feed',
        }
      case '/live':
      case '/monitoring':
        return {
          title: 'Live Classroom Workspace',
          subtitle: 'Real-time multi-person pose detection, hand-raise analytics, and teacher tracking',
        }
      case '/analytics':
        return {
          title: 'Classroom Analytics',
          subtitle: 'Student participation telemetry, spatial heatmaps, and longitudinal trends',
        }
      case '/intelligence':
        return {
          title: 'Lecture Intelligence',
          subtitle: 'Multimodal blackboard OCR extraction, audio transcripts, and key concepts',
        }
      case '/ask':
        return {
          title: 'Ask ClassVision',
          subtitle: 'Grounded question answering across classroom sessions and transcripts',
        }
      case '/reports':
        return {
          title: 'Evaluation Reports',
          subtitle: 'Classroom metrics export, session archives, and accreditation summaries',
        }
      case '/settings':
        return {
          title: 'Settings & Privacy Controls',
          subtitle: 'Edge hardware configuration, detection thresholds, and privacy masking',
        }
      case '/agents':
        return {
          title: 'Agent Command Center',
          subtitle: 'Autonomous perception and evaluation pipeline controls',
        }
      case '/model-status':
        return {
          title: 'Data & Model Status',
          subtitle: 'Local YOLOv8 weights, pipeline latency, and offline benchmarks',
        }
      default:
        return {
          title: 'ClassVision AI',
          subtitle: 'Classroom Intelligence Platform',
        }
    }
  }

  const { title, subtitle } = getPageMeta(location.pathname)

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-800 font-sans antialiased">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar title={title} subtitle={subtitle} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
export default Layout

// frontend/src/components/Topbar.tsx
import React from 'react'
import { Link } from 'react-router-dom'
import { Video } from 'lucide-react'

interface TopbarProps {
  title: string
  subtitle?: string
}

export const Topbar: React.FC<TopbarProps> = ({ title, subtitle }) => {
  return (
    <header className="h-14 flex-shrink-0 border-b border-slate-200 bg-white px-6 flex items-center justify-between z-10">
      <div className="flex items-center gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight">{title}</h2>
          {subtitle && <p className="text-[11px] text-slate-500 hidden sm:block">{subtitle}</p>}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Connectivity dot */}
        <div className="flex items-center gap-2 text-xs font-medium text-slate-600">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span>Connected</span>
        </div>

        {/* Quick Launch CTA */}
        <Link
          to="/live"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium hover:bg-blue-700 active:bg-blue-800 transition-colors shadow-2xs"
        >
          <Video className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Live Session</span>
        </Link>
      </div>
    </header>
  )
}

export default Topbar

// frontend/src/components/Topbar.tsx
import React from 'react'
import { Activity, User, HardDrive } from 'lucide-react'
import { DataStatusBadge } from './DataStatusBadge'

interface TopbarProps {
  title: string
  subtitle?: string
}

export const Topbar: React.FC<TopbarProps> = ({ title, subtitle }) => {
  const isRealMode = import.meta.env.VITE_USE_DEMO_DATA === 'false'

  return (
    <header className="h-16 flex-shrink-0 border-b border-slate-800/80 bg-[#0d101a]/80 backdrop-blur px-6 flex items-center justify-between z-10">
      <div>
        <h2 className="text-base font-bold text-white tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Stream health indicator */}
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300 font-medium">
          <Activity className="h-3.5 w-3.5 animate-pulse" />
          <span>{isRealMode ? 'FastAPI Backend Online' : 'Local Stream (Demo)'}</span>
        </div>

        {/* Offline storage status */}
        <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-400 border border-slate-800 rounded-md px-2.5 py-1 bg-slate-900/60">
          <HardDrive className="h-3.5 w-3.5 text-cyan-400" />
          <span>Offline Root</span>
        </div>

        {/* Data status badge */}
        <DataStatusBadge status={isRealMode ? 'REAL' : 'DEMO DATA'} size="md" />

        {/* User profile placeholder */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <User className="h-4 w-4" />
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-semibold text-slate-200">Instructor Session</p>
            <p className="text-[10px] text-slate-400">ClassVision Observer</p>
          </div>
        </div>
      </div>
    </header>
  )
}

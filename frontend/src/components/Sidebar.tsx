// frontend/src/components/Sidebar.tsx
import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Video,
  BarChart3,
  Brain,
  MessageSquareCode,
  FileSpreadsheet,
  Settings,
  ShieldCheck,
  LogOut,
  GraduationCap,
  Database,
  Bot,
} from 'lucide-react'
import { DataStatusBadge } from './DataStatusBadge'

interface SidebarProps {
  collapsed?: boolean
}

export const Sidebar: React.FC<SidebarProps> = () => {
  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/agents', label: 'Agent Command Center', icon: Bot },
    { to: '/live', label: 'Live Classroom', icon: Video },
    { to: '/analytics', label: 'Classroom Analytics', icon: BarChart3 },
    { to: '/intelligence', label: 'Lecture Intelligence', icon: Brain },
    { to: '/ask', label: 'Ask ClassVision', icon: MessageSquareCode },
    { to: '/reports', label: 'Reports', icon: FileSpreadsheet },
    { to: '/model-status', label: 'Data & Model Status', icon: Database },
    { to: '/settings', label: 'Settings', icon: Settings },
  ]

  const isRealMode = import.meta.env.VITE_USE_DEMO_DATA === 'false'

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col justify-between border-r border-slate-800/80 bg-[#0c0e17] text-slate-300">
      <div>
        {/* Brand header */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800/80">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-violet-600 to-cyan-500 text-white shadow-lg shadow-violet-950/40">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-base tracking-wide text-white">ClassVision</h1>
              <span className="rounded bg-violet-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-violet-300 border border-violet-500/30">
                AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Classroom Intelligence</p>
          </div>
        </div>

        {/* Global Mode Indicator */}
        <div className={`px-4 py-2.5 border-b flex items-center justify-between ${
          isRealMode ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-amber-500/5 border-amber-500/20'
        }`}>
          <span className={`text-[11px] font-medium ${isRealMode ? 'text-emerald-300' : 'text-amber-300'}`}>
            System Mode
          </span>
          <DataStatusBadge status={isRealMode ? 'REAL' : 'DEMO DATA'} size="xs" />
        </div>

        {/* Navigation links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-violet-600/30 to-cyan-600/20 text-white font-semibold border border-violet-500/40 shadow-sm shadow-violet-950/40'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`
                }
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
      </div>

      {/* Footer user profile & privacy badge */}
      <div className="p-4 border-t border-slate-800/80 space-y-3 bg-[#0a0c14]">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span className="text-[11px]">Zero Facial Tracking</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400">Edge Mode</span>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-violet-300">
              PR
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-200">Instructor Demo</p>
              <p className="text-[10px] text-slate-500">CS Department</p>
            </div>
          </div>

          <NavLink
            to="/login"
            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/20 transition-colors"
            title="Exit Demo Session"
          >
            <LogOut className="h-4 w-4" />
          </NavLink>
        </div>
      </div>
    </aside>
  )
}

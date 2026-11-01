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
  GraduationCap,
  Database,
  Bot,
  ExternalLink,
} from 'lucide-react'

interface SidebarProps {
  collapsed?: boolean
}

export const Sidebar: React.FC<SidebarProps> = () => {
  const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true'

  const primaryNav = [
    { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
    { to: '/live', label: 'Live Classroom', icon: Video },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/intelligence', label: 'Lecture Intelligence', icon: Brain },
    { to: '/ask', label: 'Ask ClassVision', icon: MessageSquareCode },
    { to: '/reports', label: 'Reports', icon: FileSpreadsheet },
    { to: '/settings', label: 'Settings', icon: Settings },
  ]

  const devNav = [
    { to: '/dev/agents', label: 'Agent Command Center', icon: Bot },
    { to: '/dev/model-status', label: 'Data & Model Status', icon: Database },
  ]

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col justify-between border-r border-slate-200 bg-white text-slate-700 select-none">
      <div className="flex flex-col flex-1 overflow-y-auto">
        {/* Brand header */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-100">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-sm tracking-tight text-slate-900">ClassVision AI</h1>
              <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700 border border-blue-200/80">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Classroom Intelligence</p>
          </div>
        </div>

        {/* Primary Navigation */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Platform
          </div>
          {primaryNav.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`
                }
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            )
          })}

          {showDevTools && (
            <div className="pt-4 space-y-1">
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Developer Tools
              </div>
              {devNav.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-blue-50 text-blue-700 font-semibold'
                          : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4 flex-shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                )
              })}
            </div>
          )}
        </nav>
      </div>

      {/* Footer system status & privacy */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/70 space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span className="text-[11px] font-medium text-slate-600">Privacy Safeguarded</span>
          </div>
          <span className="text-[10px] font-medium text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
            Offline Edge
          </span>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 text-xs">
          <div>
            <p className="font-semibold text-slate-800 text-[11px]">Academic Observer</p>
            <p className="text-[10px] text-slate-500">Institution License</p>
          </div>
          <NavLink
            to="/"
            className="p-1 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-200/60"
            title="Landing Page"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </NavLink>
        </div>
      </div>
    </aside>
  )
}
export default Sidebar

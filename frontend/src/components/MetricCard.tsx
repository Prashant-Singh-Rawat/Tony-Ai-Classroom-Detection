// frontend/src/components/MetricCard.tsx
import React from 'react'
import type { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  label: string
  value: string | number
  subtext?: string
  icon?: LucideIcon
  trend?: string
  trendType?: 'positive' | 'negative' | 'neutral'
  accentColor?: 'violet' | 'cyan' | 'emerald' | 'amber'
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  trend,
  trendType = 'neutral',
  accentColor = 'violet',
}) => {
  const accentClasses = {
    violet: 'from-violet-500/10 to-transparent border-violet-500/20 text-violet-400',
    cyan: 'from-cyan-500/10 to-transparent border-cyan-500/20 text-cyan-400',
    emerald: 'from-emerald-500/10 to-transparent border-emerald-500/20 text-emerald-400',
    amber: 'from-amber-500/10 to-transparent border-amber-500/20 text-amber-400',
  }

  const trendColors = {
    positive: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    negative: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
    neutral: 'text-slate-400 bg-slate-800/40 border-slate-700/40',
  }

  return (
    <div className={`relative overflow-hidden rounded-xl border bg-slate-900/60 bg-gradient-to-b p-5 backdrop-blur shadow-lg ${accentClasses[accentColor]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{label}</p>
          <h3 className="mt-2 text-2xl font-bold tracking-tight text-white">{value}</h3>
          {subtext && <p className="mt-1 text-xs text-slate-400">{subtext}</p>}
        </div>
        {Icon && (
          <div className="rounded-lg border border-slate-800 bg-slate-800/60 p-2.5 shadow-inner">
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3.5 flex items-center gap-1.5 pt-2 border-t border-slate-800/60">
          <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-medium border ${trendColors[trendType]}`}>
            {trend}
          </span>
          <span className="text-[11px] text-slate-500">vs session avg</span>
        </div>
      )}
    </div>
  )
}

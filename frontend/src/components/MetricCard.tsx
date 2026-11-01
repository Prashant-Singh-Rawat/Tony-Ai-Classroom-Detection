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
  const iconColors = {
    violet: 'bg-blue-50 text-blue-600 border-blue-100',
    cyan: 'bg-teal-50 text-teal-600 border-teal-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
  }

  const trendColors = {
    positive: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    negative: 'text-rose-700 bg-rose-50 border-rose-200',
    neutral: 'text-slate-600 bg-slate-50 border-slate-200',
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs hover:shadow-xs transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p>
          <h3 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">{value}</h3>
          {subtext && <p className="mt-1 text-xs text-slate-500">{subtext}</p>}
        </div>
        {Icon && (
          <div className={`rounded-lg border p-2.5 ${iconColors[accentColor]}`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3.5 flex items-center gap-1.5 pt-2 border-t border-slate-100 text-[11px]">
          <span className={`inline-flex items-center rounded px-1.5 py-0.5 font-medium border ${trendColors[trendType]}`}>
            {trend}
          </span>
          <span className="text-slate-400">vs session avg</span>
        </div>
      )}
    </div>
  )
}
export default MetricCard

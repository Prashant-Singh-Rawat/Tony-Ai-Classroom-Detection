import React from 'react'

interface StatProps {
  label: string
  value: string | number
  subtext?: string
  trend?: {
    value: string
    isPositive?: boolean
  }
  icon?: React.ReactNode
  className?: string
}

export const Stat: React.FC<StatProps> = ({
  label,
  value,
  subtext,
  trend,
  icon,
  className = '',
}) => {
  return (
    <div className={`bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs flex items-start justify-between ${className}`}>
      <div className="space-y-1">
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-bold tracking-tight text-slate-900">{value}</p>
        {(subtext || trend) && (
          <div className="flex items-center gap-2 pt-0.5">
            {trend && (
              <span
                className={`text-[11px] font-semibold flex items-center gap-0.5 ${
                  trend.isPositive ? 'text-emerald-600' : 'text-slate-500'
                }`}
              >
                {trend.value}
              </span>
            )}
            {subtext && <span className="text-[11px] text-slate-500">{subtext}</span>}
          </div>
        )}
      </div>
      {icon && (
        <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 flex-shrink-0">
          {icon}
        </div>
      )}
    </div>
  )
}

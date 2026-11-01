// frontend/src/components/DataStatusBadge.tsx
import React from 'react'

export type DataStatus = 'REAL' | 'DEMO DATA' | 'NOT CONNECTED'

interface DataStatusBadgeProps {
  status: DataStatus
  size?: 'xs' | 'sm' | 'md' | 'lg'
  className?: string
  tooltip?: string
}

export const DataStatusBadge: React.FC<DataStatusBadgeProps> = ({
  status,
  size = 'md',
  className = '',
  tooltip,
}) => {
  const sizeClasses = {
    xs: 'text-[9px] px-1.5 py-0.5 tracking-wider font-mono',
    sm: 'text-[10px] px-2 py-0.5 tracking-wider',
    md: 'text-xs px-2.5 py-1 tracking-wider',
    lg: 'text-sm px-3.5 py-1.5 tracking-widest',
  }

  const defaultTooltips: Record<DataStatus, string> = {
    REAL: 'Verified repository fact (snapshot of Phase 0.8 / Kaggle integrity / test suite).',
    'DEMO DATA': 'Illustrative mock telemetry from frontend/src/data/demo/. No active model prediction.',
    'NOT CONNECTED': 'Feature or backend service is offline / unintegrated. No real pipeline active.',
  }

  const badgeStyles: Record<
    DataStatus,
    { container: string; dot: string; label: string }
  > = {
    REAL: {
      container:
        'border-emerald-200 bg-emerald-50 text-emerald-700 shadow-2xs',
      dot: 'bg-emerald-500',
      label: 'REAL',
    },
    'DEMO DATA': {
      container:
        'border-amber-200 bg-amber-50 text-amber-800 shadow-2xs',
      dot: 'bg-amber-500 animate-pulse',
      label: 'DEMO DATA',
    },
    'NOT CONNECTED': {
      container:
        'border-slate-200 bg-slate-100 text-slate-600 shadow-2xs',
      dot: 'bg-slate-400',
      label: 'NOT CONNECTED',
    },
  }

  const currentStyle = badgeStyles[status]

  return (
    <span
      className={`inline-flex items-center font-bold uppercase rounded-md border ${currentStyle.container} ${sizeClasses[size]} ${className}`}
      title={tooltip || defaultTooltips[status]}
    >
      <span
        className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full ${currentStyle.dot}`}
      />
      {currentStyle.label}
    </span>
  )
}
export default DataStatusBadge

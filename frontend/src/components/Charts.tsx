// frontend/src/components/Charts.tsx
// Pure SVG charts: 100% offline, zero CDN dependencies, responsive & accessible.

import React from 'react'

interface TrendPoint {
  time: string
  handRaises: number
  attentiveStudents?: number
}

interface TrendLineChartProps {
  data: TrendPoint[]
  height?: number
}

export const TrendLineChart: React.FC<TrendLineChartProps> = ({ data, height = 220 }) => {
  if (!data || data.length === 0) return null

  const maxVal = Math.max(...data.map((d) => d.handRaises), 6)
  const paddingX = 40
  const paddingY = 25
  const width = 600

  const getX = (index: number) => paddingX + (index * (width - 2 * paddingX)) / (data.length - 1)
  const getY = (val: number) => height - paddingY - (val / maxVal) * (height - 2 * paddingY)

  const pointsString = data.map((d, i) => `${getX(i)},${getY(d.handRaises)}`).join(' ')

  const areaString = `${getX(0)},${height - paddingY} ${pointsString} ${getX(data.length - 1)},${height - paddingY}`

  return (
    <div className="w-full overflow-hidden">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
        <defs>
          <linearGradient id="violetGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        {[0, 2, 4, 6].map((tick) => {
          const y = getY(tick)
          return (
            <g key={tick}>
              <line x1={paddingX} y1={y} x2={width - paddingX} y2={y} stroke="#1f2438" strokeDasharray="3 3" />
              <text x={paddingX - 8} y={y + 4} fill="#64748b" fontSize="10" textAnchor="end">
                {tick}
              </text>
            </g>
          )
        })}

        {/* Area fill */}
        <polygon points={areaString} fill="url(#violetGradient)" />

        {/* Smooth line */}
        <polyline points={pointsString} fill="none" stroke="#a78bfa" strokeWidth="2.5" strokeLinecap="round" />

        {/* Data points & X-axis labels */}
        {data.map((d, i) => {
          const cx = getX(i)
          const cy = getY(d.handRaises)
          return (
            <g key={i}>
              <circle cx={cx} cy={cy} r="4" fill="#8b5cf6" stroke="#0f111a" strokeWidth="2" className="transition-all hover:r-6" />
              <text x={cx} y={height - 6} fill="#64748b" fontSize="10" textAnchor="middle">
                {d.time}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

interface ActivityBarItem {
  name: string
  count: number
  percentage: number
  color: string
}

interface ActivityBarChartProps {
  data: ActivityBarItem[]
}

export const ActivityBarChart: React.FC<ActivityBarChartProps> = ({ data }) => {
  return (
    <div className="space-y-4">
      {data.map((item) => (
        <div key={item.name} className="space-y-1.5">
          <div className="flex justify-between items-center text-xs">
            <span className="font-medium text-slate-300">{item.name}</span>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white">{item.count} students</span>
              <span className="text-[11px] text-slate-500">({item.percentage}%)</span>
            </div>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700/50">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

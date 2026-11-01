// frontend/src/components/DemoBadge.tsx
import React from 'react'
import { DataStatusBadge } from './DataStatusBadge'

interface DemoBadgeProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  text?: string
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({
  size = 'md',
  className = '',
}) => {
  return <DataStatusBadge status="DEMO DATA" size={size} className={className} />
}

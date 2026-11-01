// frontend/src/components/DataStatusBadge.test.ts
import { describe, it, expect } from 'vitest'
import { DataStatusBadge } from './DataStatusBadge'

describe('DataStatusBadge Component', () => {
  it('is a valid React component function', () => {
    expect(typeof DataStatusBadge).toBe('function')
  })

  it('renders without throwing for all three exact states', () => {
    const states = ['REAL', 'DEMO DATA', 'NOT CONNECTED'] as const
    for (const st of states) {
      const element = DataStatusBadge({ status: st, size: 'sm' })
      expect(element).not.toBeNull()
      expect(element).toBeDefined()
    }
  })
})

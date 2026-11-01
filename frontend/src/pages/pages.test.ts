// frontend/src/pages/pages.test.ts
import { describe, it, expect } from 'vitest'
import { LandingPage } from './LandingPage'
import { DashboardPage } from './DashboardPage'
import { MonitoringPage } from './MonitoringPage'
import { AnalyticsPage } from './AnalyticsPage'
import { IntelligencePage } from './IntelligencePage'
import { AskClassVisionPage } from './AskClassVisionPage'
import { ReportsPage } from './ReportsPage'
import { ModelStatusPage } from './ModelStatusPage'
import { SettingsPage } from './SettingsPage'
import { AgentCommandCenterPage } from './AgentCommandCenterPage'

describe('All 10 Dashboard Pages Export Integrity', () => {
  const pages = [
    { name: 'LandingPage', component: LandingPage },
    { name: 'DashboardPage', component: DashboardPage },
    { name: 'AgentCommandCenterPage', component: AgentCommandCenterPage },
    { name: 'MonitoringPage (Live Classroom)', component: MonitoringPage },
    { name: 'AnalyticsPage', component: AnalyticsPage },
    { name: 'IntelligencePage', component: IntelligencePage },
    { name: 'AskClassVisionPage', component: AskClassVisionPage },
    { name: 'ReportsPage', component: ReportsPage },
    { name: 'ModelStatusPage', component: ModelStatusPage },
    { name: 'SettingsPage', component: SettingsPage },
  ]

  for (const p of pages) {
    it(`exports ${p.name} as a valid functional component`, () => {
      expect(p.component).toBeDefined()
      expect(typeof p.component).toBe('function')
    })
  }
})

// frontend/src/App.tsx
import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LandingPage } from './pages/LandingPage'
import { DashboardPage } from './pages/DashboardPage'
import { MonitoringPage } from './pages/MonitoringPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { IntelligencePage } from './pages/IntelligencePage'
import { AskClassVisionPage } from './pages/AskClassVisionPage'
import { ReportsPage } from './pages/ReportsPage'
import { ModelStatusPage } from './pages/ModelStatusPage'
import { SettingsPage } from './pages/SettingsPage'
import { AgentCommandCenterPage } from './pages/AgentCommandCenterPage'
import { LectureNotesPage } from './pages/LectureNotesPage'

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Landing & Placeholder Auth */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LandingPage />} />

        {/* Authenticated Dashboard Core Views */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/live" element={<MonitoringPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/intelligence" element={<IntelligencePage />} />
          <Route path="/ask" element={<AskClassVisionPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/lecture-notes" element={<LectureNotesPage />} />

          {/* Developer Tools Routes (under /dev/... and legacy aliases) */}
          <Route path="/dev/agents" element={<AgentCommandCenterPage />} />
          <Route path="/agents" element={<AgentCommandCenterPage />} />
          <Route path="/dev/model-status" element={<ModelStatusPage />} />
          <Route path="/model-status" element={<ModelStatusPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

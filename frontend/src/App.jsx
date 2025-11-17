import React, { useState } from 'react'
import UploadFrame from './components/UploadFrame'
import DashboardFrame from './components/DashboardFrame'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('upload') // 'upload' or 'dashboard'
  const [currentAnalysis, setCurrentAnalysis] = useState(null)
  const [allAnalyses, setAllAnalyses] = useState([]) // Store all full analyses

  const handleAnalysisComplete = (analysis) => {
    setCurrentAnalysis(analysis)
    setAllAnalyses(prev => [...prev, analysis])
    setCurrentView('dashboard')
  }

  const handleMissionSelect = (missionId) => {
    const selectedAnalysis = allAnalyses.find(a => a.mission_id === missionId)
    if (selectedAnalysis) {
      setCurrentAnalysis(selectedAnalysis)
    }
  }

  const handleBackToUpload = () => {
    setCurrentView('upload')
  }

  // Create previous missions list from all analyses
  const previousMissions = allAnalyses.map(analysis => ({
    mission_id: analysis.mission_id,
    mission_name: analysis.mission_name,
    timestamp: new Date().toISOString(),
    compliance_score: analysis.overall_compliance_score
  }))

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect width="40" height="40" rx="8" fill="#1e3a8a"/>
            <path d="M20 8L28 14V26L20 32L12 26V14L20 8Z" stroke="white" strokeWidth="2"/>
            <circle cx="20" cy="20" r="4" fill="white"/>
          </svg>
        </div>
        <h1>i4NS LENS</h1>
        <p className="subtitle">Lessons Learned Enhancement System</p>
      </header>

      <main className="app-main">
        {currentView === 'upload' ? (
          <UploadFrame onAnalysisComplete={handleAnalysisComplete} />
        ) : (
          <DashboardFrame
            analysis={currentAnalysis}
            previousMissions={previousMissions}
            onBack={handleBackToUpload}
            onMissionSelect={handleMissionSelect}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>U.S. Navy - Offline Deployment Ready</p>
      </footer>
    </div>
  )
}

export default App

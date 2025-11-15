import React, { useState } from 'react'
import axios from 'axios'
import { format } from 'date-fns'
import './DashboardFrame.css'

function DashboardFrame({ analysis, previousMissions, onBack }) {
  const [chatInput, setChatInput] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [isLoadingChat, setIsLoadingChat] = useState(false)

  if (!analysis) {
    return <div className="dashboard-frame">No analysis available</div>
  }

  const handleChatSubmit = async (e) => {
    e.preventDefault()
    if (!chatInput.trim()) return

    const userMessage = chatInput
    setIsLoadingChat(true)

    // Add user message to chat
    setChatHistory(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }])

    setChatInput('')

    try {
      const response = await axios.post('/api/chat', {
        question: userMessage,
        mission_id: analysis.mission_id
      })

      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date()
      }])
    } catch (error) {
      console.error('Chat error:', error)
      setChatHistory(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question.',
        timestamp: new Date()
      }])
    } finally {
      setIsLoadingChat(false)
    }
  }

  // Get severity color
  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#dc2626',
      major: '#f59e0b',
      minor: '#3b82f6',
      info: '#10b981'
    }
    return colors[severity] || colors.info
  }

  // Get compliance color
  const getComplianceColor = (status) => {
    const colors = {
      compliant: '#10b981',
      partial: '#f59e0b',
      'non-compliant': '#dc2626',
      unclear: '#94a3b8'
    }
    return colors[status] || colors.unclear
  }

  return (
    <div className="dashboard-container">
      <button className="back-button" onClick={onBack}>
        ← Back to Upload
      </button>

      <div className="dashboard-frame">
        {/* Left Panel: Previous Missions */}
        <div className="previous-missions-panel">
          <div className="panel-header">
            <div className="icon-plus">+</div>
            <h3>Previous Missions</h3>
          </div>

          <div className="missions-list">
            {previousMissions.length === 0 ? (
              <p className="no-missions">No previous missions</p>
            ) : (
              previousMissions.map((mission, idx) => (
                <div key={idx} className="mission-card">
                  <div className="mission-name">{mission.mission_name}</div>
                  <div className="mission-meta">
                    <span className="mission-id">{mission.mission_id}</span>
                    <span className="compliance-badge" style={{
                      background: mission.compliance_score >= 80 ? '#10b981' :
                                 mission.compliance_score >= 60 ? '#f59e0b' : '#dc2626'
                    }}>
                      {mission.compliance_score?.toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Panel: Info/Recommendations */}
        <div className="info-recommendations-panel">
          <div className="panel-header-accent">
            <h3>INFO/RECOMMENDATIONS</h3>
            <div className="compliance-score">
              Compliance: {analysis.overall_compliance_score?.toFixed(1)}%
            </div>
          </div>

          <div className="info-content">
            {/* Timeline of Events */}
            <section className="timeline-section">
              <h4>Mission Timeline</h4>
              <div className="timeline">
                {analysis.comparisons.map((comparison, idx) => (
                  <div key={idx} className="timeline-event">
                    <div className="event-timestamp">
                      {format(new Date(comparison.timestamp), 'HH:mm:ss')}
                    </div>
                    <div className="event-details">
                      <div className="event-header">
                        <span className="event-description">
                          {comparison.event_description}
                        </span>
                        <span
                          className="compliance-indicator"
                          style={{ background: getComplianceColor(comparison.compliance_status) }}
                        >
                          {comparison.compliance_status}
                        </span>
                      </div>

                      <div className="comparison-details">
                        <div className="actual-vs-expected">
                          <div className="actual">
                            <strong>Actual:</strong> {comparison.actual_action}
                          </div>
                          <div className="expected">
                            <strong>Doctrine:</strong> {comparison.expected_action}
                          </div>
                        </div>

                        <div className="analysis-text">
                          {comparison.analysis}
                        </div>

                        {comparison.severity && (
                          <div
                            className="severity-badge"
                            style={{ borderColor: getSeverityColor(comparison.severity) }}
                          >
                            {comparison.severity.toUpperCase()}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Summary */}
            <section className="summary-section">
              <h4>Mission Summary</h4>
              <div className="summary-box">
                <pre>{analysis.summary}</pre>
              </div>
            </section>

            {/* Lessons Learned */}
            <section className="lessons-section">
              <h4>Lessons Learned</h4>
              <ul className="lessons-list">
                {analysis.lessons_learned.map((lesson, idx) => (
                  <li key={idx}>{lesson}</li>
                ))}
              </ul>
            </section>

            {/* Recommendations */}
            <section className="recommendations-section">
              <h4>Recommendations</h4>
              <ul className="recommendations-list">
                {analysis.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </section>
          </div>

          {/* Chat Interface */}
          <div className="chat-section">
            <h4>Questions/Chat?</h4>
            <div className="chat-container">
              <div className="chat-messages">
                {chatHistory.length === 0 ? (
                  <div className="chat-placeholder">
                    Ask questions about this mission or doctrine requirements...
                  </div>
                ) : (
                  chatHistory.map((msg, idx) => (
                    <div key={idx} className={`chat-message ${msg.role}`}>
                      <div className="message-content">{msg.content}</div>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          Sources: {msg.sources.join(', ')}
                        </div>
                      )}
                    </div>
                  ))
                )}
                {isLoadingChat && (
                  <div className="chat-message assistant">
                    <div className="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                )}
              </div>

              <form className="chat-input-form" onSubmit={handleChatSubmit}>
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask a question..."
                  disabled={isLoadingChat}
                />
                <button type="submit" disabled={isLoadingChat || !chatInput.trim()}>
                  Send
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardFrame

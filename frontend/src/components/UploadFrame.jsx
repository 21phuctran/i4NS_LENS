import React, { useState } from 'react'
import axios from 'axios'
import './UploadFrame.css'

function UploadFrame({ onAnalysisComplete }) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file) => {
    setIsLoading(true)
    setError(null)

    try {
      // Read file as JSON
      const text = await file.text()
      const missionData = JSON.parse(text)

      // Upload to server
      const formData = new FormData()
      formData.append('file', file)

      await axios.post('/api/missions/upload', formData)

      // Analyze mission
      const response = await axios.post('/api/missions/analyze', missionData)

      onAnalysisComplete(response.data)
    } catch (err) {
      console.error('Error:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to process mission log')
    } finally {
      setIsLoading(false)
    }
  }

  const loadSampleMission = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Get sample mission from API
      const sampleResponse = await axios.get('/api/sample/mission')
      const missionData = sampleResponse.data

      // Analyze sample mission
      const analysisResponse = await axios.post('/api/missions/analyze', missionData)

      onAnalysisComplete(analysisResponse.data)
    } catch (err) {
      console.error('Error:', err)
      setError(err.response?.data?.detail || 'Failed to load sample mission')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="upload-frame">
      <div className="welcome-section">
        <h2>Welcome! Press button below to summarize</h2>
        <p>Upload mission logs to analyze against Navy doctrines</p>
      </div>

      <div className="upload-section">
        <div
          className={`upload-area ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="upload-icon">📁</div>
          <h3>Upload Logs</h3>
          <p>Drag and drop mission log JSON file here</p>
          <p className="or-text">or</p>
          <label className="file-input-label">
            <input
              type="file"
              accept=".json"
              onChange={handleFileInput}
              disabled={isLoading}
            />
            <span className="button">Browse Files</span>
          </label>
        </div>

        <div className="run-llm-section">
          <button
            className="run-llm-button"
            onClick={loadSampleMission}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Processing...
              </>
            ) : (
              <>Run LLM (Sample Mission)</>
            )}
          </button>
          <p className="sample-note">Click to analyze a sample mission</p>
        </div>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>
    </div>
  )
}

export default UploadFrame

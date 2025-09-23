import React, { useState, useEffect, useMemo } from 'react'
import { startPipeline, getPipelineStatus, listPipelines, deletePipeline, getServerStatus, ServerStatus, testChatbot } from '../lib/api'

interface PipelineProgress {
  step: string
  current_step: number
  total_steps: number
}

interface PipelineStatus {
  run_id: string
  status: 'running' | 'completed' | 'failed' | 'not_found'
  progress: PipelineProgress
  logs: string[]
  start_time?: string
  end_time?: string
}

// Detailed step information for verbose display
const PIPELINE_STEPS = {
  0: { name: 'Initializing', description: 'Setting up pipeline environment and parameters' },
  1: { name: 'Astra DB Setup', description: 'Configuring and connecting to Astra database' },
  2: { name: 'Running Pipeline', description: 'Executing run_all.py with all pipeline steps' }
}

export function Pipeline() {
  const [startUrl, setStartUrl] = useState('https://www.incede.ai')
  const [maxDepth, setMaxDepth] = useState(2)
  const [maxPages, setMaxPages] = useState(50)
  const [isRunning, setIsRunning] = useState(false)
  const [currentRunId, setCurrentRunId] = useState<string | null>(null)
  const [status, setStatus] = useState<PipelineStatus | null>(null)
  const [pipelines, setPipelines] = useState<string[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [verboseMode, setVerboseMode] = useState(true)
  const [elapsedTime, setElapsedTime] = useState<string>('')
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null)
  const [testQuery, setTestQuery] = useState('who are you?')
  const [testResult, setTestResult] = useState<{answer: string, sources: any[]} | null>(null)
  const [testingChat, setTestingChat] = useState(false)

  const cfg = useMemo(() => ({
    apiBase: import.meta.env.VITE_API_BASE || '',
    apiKey: import.meta.env.VITE_API_KEY || ''
  }), [])

  // Load existing pipelines and server status
  useEffect(() => {
    loadPipelines()
    loadServerStatus()
  }, [])

  const loadServerStatus = async () => {
    try {
      const status = await getServerStatus(cfg.apiBase, cfg.apiKey)
      setServerStatus(status)
    } catch (err) {
      console.error('Error loading server status:', err)
    }
  }

  const handleTestChatbot = async () => {
    if (!testQuery.trim()) {
      setError('Please enter a test query')
      return
    }

    setTestingChat(true)
    setTestResult(null)
    setError('')

    try {
      const result = await testChatbot({
        apiBase: cfg.apiBase,
        apiKey: cfg.apiKey,
        query: testQuery,
        topK: 3,
        runId: currentRunId
      })
      setTestResult(result)
    } catch (err) {
      setError(`Error testing chatbot: ${err}`)
    } finally {
      setTestingChat(false)
    }
  }

  // Poll status for running pipeline
  useEffect(() => {
    if (currentRunId && isRunning) {
      const interval = setInterval(async () => {
        try {
          const pipelineStatus = await getPipelineStatus(cfg.apiBase, currentRunId, cfg.apiKey)
          setStatus(pipelineStatus)
          
          if (pipelineStatus.status === 'completed' || pipelineStatus.status === 'failed') {
            setIsRunning(false)
            loadPipelines() // Refresh pipeline list
          }
        } catch (err) {
          console.error('Error checking status:', err)
          setError(`Error checking status: ${err}`)
        }
      }, 1000) // Poll more frequently for verbose mode

      return () => clearInterval(interval)
    }
  }, [currentRunId, isRunning, cfg.apiBase, cfg.apiKey])

  // Calculate elapsed time
  useEffect(() => {
    if (status?.start_time && isRunning) {
      const interval = setInterval(() => {
        const start = new Date(status.start_time!)
        const now = new Date()
        const diff = now.getTime() - start.getTime()
        const minutes = Math.floor(diff / 60000)
        const seconds = Math.floor((diff % 60000) / 1000)
        setElapsedTime(`${minutes}:${seconds.toString().padStart(2, '0')}`)
      }, 1000)

      return () => clearInterval(interval)
    }
  }, [status?.start_time, isRunning])

  const loadPipelines = async () => {
    try {
      const result = await listPipelines(cfg.apiBase, cfg.apiKey)
      // Defensive programming: ensure pipelines is always an array
      setPipelines(Array.isArray(result?.pipelines) ? result.pipelines : [])
    } catch (err) {
      console.error('Error loading pipelines:', err)
      setPipelines([]) // Set empty array on error
    }
  }

  const handleStartPipeline = async () => {
    if (!startUrl.trim()) {
      setError('Please enter a valid URL')
      return
    }

    setError('')
    setIsRunning(true)
    
    try {
      const result = await startPipeline({
        apiBase: cfg.apiBase,
        apiKey: cfg.apiKey,
        startUrl,
        maxDepth,
        maxPages
      })
      
      setCurrentRunId(result.run_id)
      setStatus({
        run_id: result.run_id,
        status: 'running',
        progress: { step: 'Starting...', current_step: 0, total_steps: 3 },
        logs: ['Pipeline started']
      })
    } catch (err) {
      setIsRunning(false)
      setError(`Error starting pipeline: ${err}`)
    }
  }

  const handleViewPipeline = async (runId: string) => {
    try {
      const pipelineStatus = await getPipelineStatus(cfg.apiBase, runId, cfg.apiKey)
      setStatus(pipelineStatus)
      setCurrentRunId(runId)
      setSelectedPipeline(runId)
    } catch (err) {
      setError(`Error loading pipeline: ${err}`)
    }
  }

  const handleDeletePipeline = async (runId: string) => {
    if (!confirm('Are you sure you want to delete this pipeline?')) return
    
    try {
      await deletePipeline(cfg.apiBase, runId, cfg.apiKey)
      loadPipelines()
      if (currentRunId === runId) {
        setCurrentRunId(null)
        setStatus(null)
      }
    } catch (err) {
      setError(`Error deleting pipeline: ${err}`)
    }
  }

  const getProgressPercentage = () => {
    if (!status?.progress) return 0
    return Math.round((status.progress.current_step / status.progress.total_steps) * 100)
  }

  const getCurrentStepInfo = () => {
    if (!status?.progress) return null
    const stepNum = status.progress.current_step
    return PIPELINE_STEPS[stepNum as keyof typeof PIPELINE_STEPS] || null
  }

  const getStepStatus = (stepNum: number) => {
    if (!status?.progress) return 'pending'
    const current = status.progress.current_step
    if (stepNum < current) return 'completed'
    if (stepNum === current) return 'running'
    return 'pending'
  }

  const formatLogEntry = (log: string) => {
    // Add timestamp and formatting to log entries
    const timestamp = new Date().toLocaleTimeString()
    return `[${timestamp}] ${log}`
  }

  return (
    <div className="pipeline">
      <div className="pipeline-header">
        <h2>Knowledge Base Pipeline</h2>
        <p>Crawl websites and build your knowledge base</p>
      </div>

      {serverStatus && (
        <div className="server-status">
          <h3>Server Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Server:</span>
              <span className={`status-value ${serverStatus.server === 'running' ? 'success' : 'error'}`}>
                {serverStatus.server}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Astra DB:</span>
              <span className={`status-value ${serverStatus.astra_db_configured ? 'success' : 'warning'}`}>
                {serverStatus.astra_db_configured ? 'Configured' : 'Not Configured'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Watson AI:</span>
              <span className={`status-value ${serverStatus.watson_configured ? 'success' : 'warning'}`}>
                {serverStatus.watson_configured ? 'Configured' : 'Not Configured'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Connection:</span>
              <span className={`status-value ${serverStatus.astra_connection === 'active' ? 'success' : 'error'}`}>
                {serverStatus.astra_connection}
              </span>
            </div>
          </div>
          {serverStatus.astra_db_configured && (
            <div className="database-info">
              <p><strong>Database:</strong> {serverStatus.astra_endpoint}</p>
              <p><strong>Collection:</strong> {serverStatus.collection_name}</p>
              {serverStatus.collections.length > 0 && (
                <p><strong>Available Collections:</strong> {serverStatus.collections.join(', ')}</p>
              )}
            </div>
          )}
          {!serverStatus.astra_db_configured && (
            <div className="setup-notice">
              <p>⚠️ <strong>No Astra DB configured.</strong> Run a pipeline first to automatically set up the database connection.</p>
            </div>
          )}
        </div>
      )}

      {/* Test Chatbot Section - Show when pipeline is completed */}
      {status && status.status === 'completed' && (
        <div className="test-chatbot-section">
          <h3>Test Chatbot</h3>
          <p>Test your knowledge base with a sample query (like the terminal "Ask:" prompt)</p>
          
          <div className="test-query-form">
            <div className="input-group">
              <label htmlFor="testQuery">Test Query:</label>
              <input
                id="testQuery"
                type="text"
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                placeholder="Enter a question to test the chatbot..."
                className="test-query-input"
              />
            </div>
            <button
              onClick={handleTestChatbot}
              disabled={testingChat || !testQuery.trim()}
              className="test-chatbot-btn"
            >
              {testingChat ? 'Testing...' : 'Test Chatbot'}
            </button>
          </div>

          {testResult && (
            <div className="test-result">
              <h4>Answer:</h4>
              <div className="answer-content">
                {testResult.answer}
              </div>
              
              {testResult.sources && testResult.sources.length > 0 && (
                <div className="sources-section">
                  <h4>Sources:</h4>
                  <div className="sources-list">
                    {testResult.sources.map((source, index) => (
                      <div key={index} className="source-item">
                        <div className="source-title">
                          <a href={source.url} target="_blank" rel="noopener noreferrer">
                            {source.title || source.url}
                          </a>
                          {source.score && (
                            <span className="source-score">Score: {source.score.toFixed(3)}</span>
                          )}
                        </div>
                        <div className="source-url">{source.url}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="pipeline-form">
        <div className="form-group">
          <label htmlFor="startUrl">Website URL:</label>
          <input
            id="startUrl"
            type="url"
            value={startUrl}
            onChange={(e) => setStartUrl(e.target.value)}
            placeholder="https://example.com"
            disabled={isRunning}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="maxDepth">Max Depth:</label>
            <input
              id="maxDepth"
              type="number"
              value={maxDepth}
              onChange={(e) => setMaxDepth(parseInt(e.target.value))}
              min="0"
              max="5"
              disabled={isRunning}
            />
          </div>

          <div className="form-group">
            <label htmlFor="maxPages">Max Pages:</label>
            <input
              id="maxPages"
              type="number"
              value={maxPages}
              onChange={(e) => setMaxPages(parseInt(e.target.value))}
              min="1"
              max="1000"
              disabled={isRunning}
            />
          </div>
        </div>

        <button
          onClick={handleStartPipeline}
          disabled={isRunning || !startUrl.trim()}
          className="start-button"
        >
          {isRunning ? 'Running...' : 'Start Pipeline'}
        </button>
      </div>

      {status && (
        <div className="pipeline-status">
          <div className="status-header">
            <h3>Pipeline Status: {currentRunId}</h3>
            <div className="verbose-toggle">
              <label>
                <input 
                  type="checkbox" 
                  checked={verboseMode} 
                  onChange={(e) => setVerboseMode(e.target.checked)}
                />
                Verbose Mode
              </label>
            </div>
          </div>
          
          <div className="status-info">
            <div className="status-badge" data-status={status.status}>
              {status.status.toUpperCase()}
            </div>
            
            <div className="time-info">
              {status.start_time && (
                <span>Started: {status.start_time}</span>
              )}
              {elapsedTime && isRunning && (
                <span className="elapsed-time"> | Elapsed: {elapsedTime}</span>
              )}
              {status.end_time && (
                <span> | Ended: {status.end_time}</span>
              )}
            </div>
          </div>

          <div className="progress-section">
            <div className="progress-info">
              <span className="current-step">{status.progress.step}</span>
              <span className="progress-percentage">{getProgressPercentage()}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
            <div className="step-info">
              Step {status.progress.current_step} of {status.progress.total_steps}
            </div>
            
            {verboseMode && getCurrentStepInfo() && (
              <div className="step-description">
                <strong>{getCurrentStepInfo()?.name}:</strong> {getCurrentStepInfo()?.description}
              </div>
            )}
          </div>

          {verboseMode && (
            <div className="steps-overview">
              <h4>Pipeline Steps:</h4>
              <div className="steps-list">
                {Object.entries(PIPELINE_STEPS).map(([stepNum, stepInfo]) => {
                  const stepStatus = getStepStatus(parseInt(stepNum))
                  return (
                    <div key={stepNum} className={`step-item ${stepStatus}`}>
                      <div className="step-indicator">
                        {stepStatus === 'completed' && '✅'}
                        {stepStatus === 'running' && '🔄'}
                        {stepStatus === 'pending' && '⏳'}
                      </div>
                      <div className="step-details">
                        <div className="step-name">{stepInfo.name}</div>
                        <div className="step-desc">{stepInfo.description}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          <div className="logs-section">
            <div className="logs-header">
              <h4>Live Logs:</h4>
              <span className="log-count">{status.logs.length} entries</span>
            </div>
            <div className="logs">
              {status.logs.map((log, index) => (
                <div key={index} className={`log-entry ${verboseMode ? 'verbose' : ''}`}>
                  {verboseMode ? formatLogEntry(log) : log}
                </div>
              ))}
              {status.logs.length === 0 && (
                <div className="no-logs">No logs available yet...</div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="pipeline-history">
        <h3>Pipeline History</h3>
        {pipelines.length === 0 ? (
          <p>No pipelines found</p>
        ) : (
          <div className="pipeline-list">
            {pipelines.map((runId) => (
              <div key={runId} className="pipeline-item">
                <span className="run-id">{runId}</span>
                <div className="pipeline-actions">
                  <button onClick={() => handleViewPipeline(runId)}>
                    View
                  </button>
                  <button 
                    onClick={() => handleDeletePipeline(runId)}
                    className="delete-button"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

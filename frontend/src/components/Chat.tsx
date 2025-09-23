import React, { useMemo, useRef, useState, useEffect } from 'react'
import { askQuestion } from '../lib/api'

export function Chat(){
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{role:'user'|'assistant'; text:string}[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedRunId, setSelectedRunId] = useState<string>('')
  const [availableRuns, setAvailableRuns] = useState<string[]>([])
  const feedRef = useRef<HTMLDivElement>(null)

  const cfg = useMemo(() => ({
    apiBase: import.meta.env.VITE_API_BASE || '',
    apiKey: import.meta.env.VITE_API_KEY || '',
    topK: Number(import.meta.env.VITE_TOP_K || 3)
  }), [])

  // Load available pipeline runs
  useEffect(() => {
    const loadRuns = async () => {
      try {
        const response = await fetch(`${cfg.apiBase}/pipeline/list`, {
          headers: cfg.apiKey ? { 'X-API-Key': cfg.apiKey } : {}
        })
        if (response.ok) {
          const data = await response.json()
          // Defensive programming: ensure pipelines is always an array
          const pipelines = Array.isArray(data?.pipelines) ? data.pipelines : []
          setAvailableRuns(pipelines)
          // Auto-select the most recent run if available
          if (pipelines.length > 0) {
            setSelectedRunId(pipelines[0])
          }
        }
      } catch (err) {
        console.error('Error loading pipeline runs:', err)
      }
    }
    loadRuns()
  }, [cfg.apiBase, cfg.apiKey])

  async function send(){
    const q = input.trim()
    if(!q || loading || !selectedRunId) return
    setMessages(m => [...m, {role:'user', text:q}])
    setInput('')
    setLoading(true)
    try{
      const res = await askQuestion({ apiBase: cfg.apiBase, apiKey: cfg.apiKey, query: q, topK: cfg.topK, runId: selectedRunId })
      setMessages(m => [...m, {role:'assistant', text: res.answer || 'No answer.'}])
      if(Array.isArray(res.sources) && res.sources.length){
        const src = res.sources.map((s:any) => `• ${s.title || s.url || ''}`).join('\n')
        setMessages(m => [...m, {role:'assistant', text: `Sources:\n${src}` }])
      }
    }catch(err){
      setMessages(m => [...m, {role:'assistant', text:'Sorry, something went wrong.'}])
    }finally{
      setLoading(false)
      requestAnimationFrame(() => { if(feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight })
    }
  }

  return (
    <div className="chat">
      {messages.length === 0 && (
        <div className="chat-welcome">
          <h3>Welcome to the Chatbot!</h3>
          <p>Ask questions about the knowledge base. Make sure to run a pipeline first in the "Knowledge Base" tab to set up the database.</p>
          
          {availableRuns.length > 0 && (
            <div className="run-selector">
              <label htmlFor="runSelect">Select Pipeline Run:</label>
              <select 
                id="runSelect"
                value={selectedRunId} 
                onChange={(e) => setSelectedRunId(e.target.value)}
                className="run-select"
              >
                {availableRuns.map(runId => (
                  <option key={runId} value={runId}>{runId}</option>
                ))}
              </select>
            </div>
          )}
          
          {availableRuns.length === 0 && (
            <div className="no-runs">
              <p>⚠️ No pipeline runs found. Please run a pipeline first in the "Knowledge Base" tab.</p>
            </div>
          )}
        </div>
      )}
      <div className="feed" ref={feedRef}>
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="meta">{m.role === 'user' ? 'You' : 'Assistant'}</div>
            <div className="bubble">{m.text}</div>
          </div>
        ))}
        {loading && <div className="loading">Thinking…</div>}
      </div>
      <div className="composer">
        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter') send() }} placeholder="Type your question…" />
        <button onClick={send} disabled={loading || !input.trim()}>Send</button>
      </div>
    </div>
  )
} 
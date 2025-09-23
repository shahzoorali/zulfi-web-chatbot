import React, { useMemo, useRef, useState } from 'react'
import { askQuestion } from '../lib/api'

export function Chat(){
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{role:'user'|'assistant'; text:string}[]>([])
  const [loading, setLoading] = useState(false)
  const feedRef = useRef<HTMLDivElement>(null)

  const cfg = useMemo(() => ({
    apiBase: import.meta.env.VITE_API_BASE || '',
    apiKey: import.meta.env.VITE_API_KEY || '',
    runId: import.meta.env.VITE_DEFAULT_RUN_ID || null,
    topK: Number(import.meta.env.VITE_TOP_K || 3)
  }), [])

  async function send(){
    const q = input.trim()
    if(!q || loading) return
    setMessages(m => [...m, {role:'user', text:q}])
    setInput('')
    setLoading(true)
    try{
      const res = await askQuestion({ apiBase: cfg.apiBase, apiKey: cfg.apiKey, query: q, topK: cfg.topK, runId: cfg.runId })
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
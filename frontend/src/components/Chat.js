import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useRef, useState, useEffect } from 'react';
import { askQuestion } from '../lib/api';
export function Chat() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedRunId, setSelectedRunId] = useState('');
    const [availableRuns, setAvailableRuns] = useState([]);
    const feedRef = useRef(null);
    const cfg = useMemo(() => ({
        apiBase: import.meta.env.VITE_API_BASE || '',
        apiKey: import.meta.env.VITE_API_KEY || '',
        topK: Number(import.meta.env.VITE_TOP_K || 3)
    }), []);
    // Load available pipeline runs
    useEffect(() => {
        const loadRuns = async () => {
            try {
                const response = await fetch(`${cfg.apiBase}/pipeline/list`, {
                    headers: cfg.apiKey ? { 'X-API-Key': cfg.apiKey } : {}
                });
                if (response.ok) {
                    const data = await response.json();
                    // Defensive programming: ensure pipelines is always an array
                    const pipelines = Array.isArray(data?.pipelines) ? data.pipelines : [];
                    setAvailableRuns(pipelines);
                    // Auto-select the most recent run if available
                    if (pipelines.length > 0) {
                        setSelectedRunId(pipelines[0]);
                    }
                }
            }
            catch (err) {
                console.error('Error loading pipeline runs:', err);
            }
        };
        loadRuns();
    }, [cfg.apiBase, cfg.apiKey]);
    async function send() {
        const q = input.trim();
        if (!q || loading || !selectedRunId)
            return;
        setMessages(m => [...m, { role: 'user', text: q }]);
        setInput('');
        setLoading(true);
        try {
            const res = await askQuestion({ apiBase: cfg.apiBase, apiKey: cfg.apiKey, query: q, topK: cfg.topK, runId: selectedRunId });
            setMessages(m => [...m, { role: 'assistant', text: res.answer || 'No answer.' }]);
            if (Array.isArray(res.sources) && res.sources.length) {
                const src = res.sources.map((s) => `• ${s.title || s.url || ''}`).join('\n');
                setMessages(m => [...m, { role: 'assistant', text: `Sources:\n${src}` }]);
            }
        }
        catch (err) {
            setMessages(m => [...m, { role: 'assistant', text: 'Sorry, something went wrong.' }]);
        }
        finally {
            setLoading(false);
            requestAnimationFrame(() => { if (feedRef.current)
                feedRef.current.scrollTop = feedRef.current.scrollHeight; });
        }
    }
    return (_jsxs("div", { className: "chat", children: [messages.length === 0 && (_jsxs("div", { className: "chat-welcome", children: [_jsx("h3", { children: "Welcome to the Chatbot!" }), _jsx("p", { children: "Ask questions about the knowledge base. Make sure to run a pipeline first in the \"Knowledge Base\" tab to set up the database." }), availableRuns.length > 0 && (_jsxs("div", { className: "run-selector", children: [_jsx("label", { htmlFor: "runSelect", children: "Select Pipeline Run:" }), _jsx("select", { id: "runSelect", value: selectedRunId, onChange: (e) => setSelectedRunId(e.target.value), className: "run-select", children: availableRuns.map(runId => (_jsx("option", { value: runId, children: runId }, runId))) })] })), availableRuns.length === 0 && (_jsx("div", { className: "no-runs", children: _jsx("p", { children: "\u26A0\uFE0F No pipeline runs found. Please run a pipeline first in the \"Knowledge Base\" tab." }) }))] })), _jsxs("div", { className: "feed", ref: feedRef, children: [messages.map((m, i) => (_jsxs("div", { className: `msg ${m.role}`, children: [_jsx("div", { className: "meta", children: m.role === 'user' ? 'You' : 'Assistant' }), _jsx("div", { className: "bubble", children: m.text })] }, i))), loading && _jsx("div", { className: "loading", children: "Thinking\u2026" })] }), _jsxs("div", { className: "composer", children: [_jsx("input", { value: input, onChange: e => setInput(e.target.value), onKeyDown: e => { if (e.key === 'Enter')
                            send(); }, placeholder: "Type your question\u2026" }), _jsx("button", { onClick: send, disabled: loading || !input.trim(), children: "Send" })] })] }));
}

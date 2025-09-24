import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useMemo, useRef } from 'react';
import { startPipeline, getPipelineStatus, listPipelines, deletePipeline, getServerStatus, testChatbot, getPipelineHistory } from '../lib/api';
// Detailed step information for verbose display
const PIPELINE_STEPS = {
    0: { name: 'Initializing', description: 'Setting up pipeline environment and parameters' },
    1: { name: 'Astra DB Setup', description: 'Configuring and connecting to Astra database' },
    2: { name: 'Running Pipeline', description: 'Executing run_all.py with all pipeline steps' }
};
export function Pipeline() {
    const [startUrl, setStartUrl] = useState('https://www.incede.ai');
    const [maxDepth, setMaxDepth] = useState(2);
    const [maxPages, setMaxPages] = useState(50);
    const [isRunning, setIsRunning] = useState(false);
    const [currentRunId, setCurrentRunId] = useState(null);
    const [status, setStatus] = useState(null);
    const [pipelines, setPipelines] = useState([]);
    const [pipelineHistory, setPipelineHistory] = useState([]);
    const [selectedPipeline, setSelectedPipeline] = useState('');
    const [error, setError] = useState('');
    const [verboseMode, setVerboseMode] = useState(true);
    const [elapsedTime, setElapsedTime] = useState('');
    const [serverStatus, setServerStatus] = useState(null);
    const [testQuery, setTestQuery] = useState('who are you?');
    const [testResult, setTestResult] = useState(null);
    const [testingChat, setTestingChat] = useState(false);
    const isStartingRef = useRef(false);
    const cfg = useMemo(() => ({
        apiBase: import.meta.env.VITE_API_BASE || '',
        apiKey: import.meta.env.VITE_API_KEY || ''
    }), []);
    // Load existing pipelines and server status
    useEffect(() => {
        loadPipelines();
        loadPipelineHistory();
        loadServerStatus();
    }, []);
    const loadServerStatus = async () => {
        try {
            const status = await getServerStatus(cfg.apiBase, cfg.apiKey);
            setServerStatus(status);
        }
        catch (err) {
            console.error('Error loading server status:', err);
        }
    };
    const handleTestChatbot = async () => {
        if (!testQuery.trim()) {
            setError('Please enter a test query');
            return;
        }
        setTestingChat(true);
        setTestResult(null);
        setError('');
        try {
            const result = await testChatbot({
                apiBase: cfg.apiBase,
                apiKey: cfg.apiKey,
                query: testQuery,
                topK: 3,
                runId: currentRunId
            });
            setTestResult(result);
        }
        catch (err) {
            setError(`Error testing chatbot: ${err}`);
        }
        finally {
            setTestingChat(false);
        }
    };
    // Poll status for running pipeline
    useEffect(() => {
        if (currentRunId && isRunning) {
            const interval = setInterval(async () => {
                try {
                    const pipelineStatus = await getPipelineStatus(cfg.apiBase, currentRunId, cfg.apiKey);
                    setStatus(pipelineStatus);
                    if (pipelineStatus.status === 'completed' || pipelineStatus.status === 'failed') {
                        setIsRunning(false);
                        loadPipelines(); // Refresh pipeline list
                        loadPipelineHistory(); // Refresh pipeline history
                    }
                }
                catch (err) {
                    console.error('Error checking status:', err);
                    setError(`Error checking status: ${err}`);
                }
            }, 1000); // Poll more frequently for verbose mode
            return () => clearInterval(interval);
        }
    }, [currentRunId, isRunning, cfg.apiBase, cfg.apiKey]);
    // Calculate elapsed time
    useEffect(() => {
        if (status?.start_time && isRunning) {
            const interval = setInterval(() => {
                const start = new Date(status.start_time);
                const now = new Date();
                const diff = now.getTime() - start.getTime();
                const minutes = Math.floor(diff / 60000);
                const seconds = Math.floor((diff % 60000) / 1000);
                setElapsedTime(`${minutes}:${seconds.toString().padStart(2, '0')}`);
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [status?.start_time, isRunning]);
    const loadPipelines = async () => {
        try {
            const result = await listPipelines(cfg.apiBase, cfg.apiKey);
            // Defensive programming: ensure pipelines is always an array
            setPipelines(Array.isArray(result?.pipelines) ? result.pipelines : []);
        }
        catch (err) {
            console.error('Error loading pipelines:', err);
            setPipelines([]); // Set empty array on error
        }
    };
    const loadPipelineHistory = async () => {
        try {
            const result = await getPipelineHistory(cfg.apiBase, cfg.apiKey);
            // Defensive programming: ensure history is always an array
            setPipelineHistory(Array.isArray(result?.history) ? result.history : []);
        }
        catch (err) {
            console.error('Error loading pipeline history:', err);
            setPipelineHistory([]); // Set empty array on error
        }
    };
    const handleStartPipeline = async () => {
        if (!startUrl.trim()) {
            setError('Please enter a valid URL');
            return;
        }
        // Prevent multiple simultaneous starts using ref
        if (isStartingRef.current || isRunning) {
            return;
        }
        isStartingRef.current = true;
        setError('');
        setIsRunning(true);
        try {
            const result = await startPipeline({
                apiBase: cfg.apiBase,
                apiKey: cfg.apiKey,
                startUrl,
                maxDepth,
                maxPages
            });
            setCurrentRunId(result.run_id);
            setStatus({
                run_id: result.run_id,
                status: 'running',
                progress: { step: 'Starting...', current_step: 0, total_steps: 3 },
                logs: ['Pipeline started']
            });
        }
        catch (err) {
            setIsRunning(false);
            setError(`Error starting pipeline: ${err}`);
        }
        finally {
            isStartingRef.current = false;
        }
    };
    const handleViewPipeline = async (runId) => {
        try {
            const pipelineStatus = await getPipelineStatus(cfg.apiBase, runId, cfg.apiKey);
            setStatus(pipelineStatus);
            setCurrentRunId(runId);
            setSelectedPipeline(runId);
        }
        catch (err) {
            setError(`Error loading pipeline: ${err}`);
        }
    };
    const handleDeletePipeline = async (runId) => {
        if (!confirm('Are you sure you want to delete this pipeline?'))
            return;
        try {
            await deletePipeline(cfg.apiBase, runId, cfg.apiKey);
            loadPipelines();
            loadPipelineHistory();
            if (currentRunId === runId) {
                setCurrentRunId(null);
                setStatus(null);
            }
        }
        catch (err) {
            setError(`Error deleting pipeline: ${err}`);
        }
    };
    const getProgressPercentage = () => {
        if (!status?.progress)
            return 0;
        return Math.round((status.progress.current_step / status.progress.total_steps) * 100);
    };
    const getCurrentStepInfo = () => {
        if (!status?.progress)
            return null;
        const stepNum = status.progress.current_step;
        return PIPELINE_STEPS[stepNum] || null;
    };
    const getStepStatus = (stepNum) => {
        if (!status?.progress)
            return 'pending';
        const current = status.progress.current_step;
        if (stepNum < current)
            return 'completed';
        if (stepNum === current)
            return 'running';
        return 'pending';
    };
    const formatTimestamp = (timestamp) => {
        if (!timestamp)
            return 'Unknown';
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        }
        catch {
            return timestamp;
        }
    };
    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed': return '✅';
            case 'running': return '🔄';
            case 'failed': return '❌';
            default: return '❓';
        }
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return '#28a745';
            case 'running': return '#007bff';
            case 'failed': return '#dc3545';
            default: return '#6c757d';
        }
    };
    const formatLogEntry = (log) => {
        // Add timestamp and formatting to log entries
        const timestamp = new Date().toLocaleTimeString();
        return `[${timestamp}] ${log}`;
    };
    return (_jsxs("div", { className: "pipeline", children: [_jsxs("div", { className: "pipeline-header", children: [_jsx("h2", { children: "Knowledge Base Pipeline" }), _jsx("p", { children: "Crawl websites and build your knowledge base" })] }), serverStatus && (_jsxs("div", { className: "server-status", children: [_jsx("h3", { children: "Server Status" }), _jsxs("div", { className: "status-grid", children: [_jsxs("div", { className: "status-item", children: [_jsx("span", { className: "status-label", children: "Server:" }), _jsx("span", { className: `status-value ${serverStatus.server === 'running' ? 'success' : 'error'}`, children: serverStatus.server })] }), _jsxs("div", { className: "status-item", children: [_jsx("span", { className: "status-label", children: "Astra DB:" }), _jsx("span", { className: `status-value ${serverStatus.astra_db_configured ? 'success' : 'warning'}`, children: serverStatus.astra_db_configured ? 'Configured' : 'Not Configured' })] }), _jsxs("div", { className: "status-item", children: [_jsx("span", { className: "status-label", children: "Watson AI:" }), _jsx("span", { className: `status-value ${serverStatus.watson_configured ? 'success' : 'warning'}`, children: serverStatus.watson_configured ? 'Configured' : 'Not Configured' })] }), _jsxs("div", { className: "status-item", children: [_jsx("span", { className: "status-label", children: "Connection:" }), _jsx("span", { className: `status-value ${serverStatus.astra_connection === 'active' ? 'success' : 'error'}`, children: serverStatus.astra_connection })] })] }), serverStatus.astra_db_configured && (_jsxs("div", { className: "database-info", children: [_jsxs("p", { children: [_jsx("strong", { children: "Database:" }), " ", serverStatus.astra_endpoint] }), _jsxs("p", { children: [_jsx("strong", { children: "Collection:" }), " ", serverStatus.collection_name] }), serverStatus.collections.length > 0 && (_jsxs("p", { children: [_jsx("strong", { children: "Available Collections:" }), " ", serverStatus.collections.join(', ')] }))] })), !serverStatus.astra_db_configured && (_jsx("div", { className: "setup-notice", children: _jsxs("p", { children: ["\u26A0\uFE0F ", _jsx("strong", { children: "No Astra DB configured." }), " Run a pipeline first to automatically set up the database connection."] }) }))] })), status && status.status === 'completed' && (_jsxs("div", { className: "test-chatbot-section", children: [_jsx("h3", { children: "Test Chatbot" }), _jsx("p", { children: "Test your knowledge base with a sample query (like the terminal \"Ask:\" prompt)" }), _jsxs("div", { className: "test-query-form", children: [_jsxs("div", { className: "input-group", children: [_jsx("label", { htmlFor: "testQuery", children: "Test Query:" }), _jsx("input", { id: "testQuery", type: "text", value: testQuery, onChange: (e) => setTestQuery(e.target.value), placeholder: "Enter a question to test the chatbot...", className: "test-query-input" })] }), _jsx("button", { onClick: handleTestChatbot, disabled: testingChat || !testQuery.trim(), className: "test-chatbot-btn", children: testingChat ? 'Testing...' : 'Test Chatbot' })] }), testResult && (_jsxs("div", { className: "test-result", children: [_jsx("h4", { children: "Answer:" }), _jsx("div", { className: "answer-content", children: testResult.answer }), testResult.sources && testResult.sources.length > 0 && (_jsxs("div", { className: "sources-section", children: [_jsx("h4", { children: "Sources:" }), _jsx("div", { className: "sources-list", children: testResult.sources.map((source, index) => (_jsxs("div", { className: "source-item", children: [_jsxs("div", { className: "source-title", children: [_jsx("a", { href: source.url, target: "_blank", rel: "noopener noreferrer", children: source.title || source.url }), source.score && (_jsxs("span", { className: "source-score", children: ["Score: ", source.score.toFixed(3)] }))] }), _jsx("div", { className: "source-url", children: source.url })] }, index))) })] }))] }))] })), error && (_jsx("div", { className: "error-message", children: error })), _jsxs("div", { className: "pipeline-form", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { htmlFor: "startUrl", children: "Website URL:" }), _jsx("input", { id: "startUrl", type: "url", value: startUrl, onChange: (e) => setStartUrl(e.target.value), placeholder: "https://example.com", disabled: isRunning })] }), _jsxs("div", { className: "form-row", children: [_jsxs("div", { className: "form-group", children: [_jsx("label", { htmlFor: "maxDepth", children: "Max Depth:" }), _jsx("input", { id: "maxDepth", type: "number", value: maxDepth, onChange: (e) => setMaxDepth(parseInt(e.target.value)), min: "0", max: "5", disabled: isRunning })] }), _jsxs("div", { className: "form-group", children: [_jsx("label", { htmlFor: "maxPages", children: "Max Pages:" }), _jsx("input", { id: "maxPages", type: "number", value: maxPages, onChange: (e) => setMaxPages(parseInt(e.target.value)), min: "1", max: "1000", disabled: isRunning })] })] }), _jsx("button", { onClick: handleStartPipeline, disabled: isRunning || !startUrl.trim(), className: "start-button", children: isRunning ? 'Running...' : 'Start Pipeline' })] }), status && (_jsxs("div", { className: "pipeline-status", children: [_jsxs("div", { className: "status-header", children: [_jsxs("h3", { children: ["Pipeline Status: ", currentRunId] }), _jsx("div", { className: "verbose-toggle", children: _jsxs("label", { children: [_jsx("input", { type: "checkbox", checked: verboseMode, onChange: (e) => setVerboseMode(e.target.checked) }), "Verbose Mode"] }) })] }), _jsxs("div", { className: "status-info", children: [_jsx("div", { className: "status-badge", "data-status": status.status, children: status.status.toUpperCase() }), _jsxs("div", { className: "time-info", children: [status.start_time && (_jsxs("span", { children: ["Started: ", status.start_time] })), elapsedTime && isRunning && (_jsxs("span", { className: "elapsed-time", children: [" | Elapsed: ", elapsedTime] })), status.end_time && (_jsxs("span", { children: [" | Ended: ", status.end_time] }))] })] }), _jsxs("div", { className: "progress-section", children: [_jsxs("div", { className: "progress-info", children: [_jsx("span", { className: "current-step", children: status.progress.step }), _jsxs("span", { className: "progress-percentage", children: [getProgressPercentage(), "%"] })] }), _jsx("div", { className: "progress-bar", children: _jsx("div", { className: "progress-fill", style: { width: `${getProgressPercentage()}%` } }) }), _jsxs("div", { className: "step-info", children: ["Step ", status.progress.current_step, " of ", status.progress.total_steps] }), verboseMode && getCurrentStepInfo() && (_jsxs("div", { className: "step-description", children: [_jsxs("strong", { children: [getCurrentStepInfo()?.name, ":"] }), " ", getCurrentStepInfo()?.description] }))] }), verboseMode && (_jsxs("div", { className: "steps-overview", children: [_jsx("h4", { children: "Pipeline Steps:" }), _jsx("div", { className: "steps-list", children: Object.entries(PIPELINE_STEPS).map(([stepNum, stepInfo]) => {
                                    const stepStatus = getStepStatus(parseInt(stepNum));
                                    return (_jsxs("div", { className: `step-item ${stepStatus}`, children: [_jsxs("div", { className: "step-indicator", children: [stepStatus === 'completed' && '✅', stepStatus === 'running' && '🔄', stepStatus === 'pending' && '⏳'] }), _jsxs("div", { className: "step-details", children: [_jsx("div", { className: "step-name", children: stepInfo.name }), _jsx("div", { className: "step-desc", children: stepInfo.description })] })] }, stepNum));
                                }) })] })), _jsxs("div", { className: "logs-section", children: [_jsxs("div", { className: "logs-header", children: [_jsx("h4", { children: "Live Logs:" }), _jsxs("span", { className: "log-count", children: [status.logs.length, " entries"] })] }), _jsxs("div", { className: "logs", children: [status.logs.map((log, index) => (_jsx("div", { className: `log-entry ${verboseMode ? 'verbose' : ''}`, children: verboseMode ? formatLogEntry(log) : log }, index))), status.logs.length === 0 && (_jsx("div", { className: "no-logs", children: "No logs available yet..." }))] })] })] })), _jsxs("div", { className: "pipeline-history", children: [_jsx("h3", { children: "Pipeline History" }), pipelineHistory.length === 0 ? (_jsx("p", { children: "No pipelines found" })) : (_jsx("div", { className: "pipeline-list", children: pipelineHistory.map((item) => (_jsxs("div", { className: "pipeline-item", children: [_jsxs("div", { className: "pipeline-info", children: [_jsxs("div", { className: "pipeline-header", children: [_jsx("span", { className: "status-icon", children: getStatusIcon(item.status) }), _jsx("span", { className: "run-id", children: item.run_id }), _jsx("span", { className: "status-badge", style: { backgroundColor: getStatusColor(item.status) }, children: item.status })] }), _jsxs("div", { className: "pipeline-details", children: [_jsx("div", { className: "site-name", children: _jsx("strong", { children: item.site_name }) }), _jsxs("div", { className: "timestamp", children: ["Started: ", formatTimestamp(item.start_time)] }), item.end_time && (_jsxs("div", { className: "timestamp", children: ["Ended: ", formatTimestamp(item.end_time)] }))] })] }), _jsxs("div", { className: "pipeline-actions", children: [_jsx("button", { onClick: () => handleViewPipeline(item.run_id), children: "View" }), _jsx("button", { onClick: () => handleDeletePipeline(item.run_id), className: "delete-button", children: "Delete" })] })] }, item.run_id))) }))] })] }));
}

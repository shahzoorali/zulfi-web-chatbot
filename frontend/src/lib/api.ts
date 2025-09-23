interface AskQuestionRequest {
  apiBase: string
  apiKey?: string
  query: string
  topK?: number
  runId?: string | null
}

interface Source {
  url?: string
  title?: string
  score?: number
}

interface AskQuestionResponse {
  answer: string
  sources: Source[]
}

interface PipelineRequest {
  apiBase: string
  apiKey?: string
  startUrl: string
  maxDepth?: number
  maxPages?: number
}

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
  site_name?: string
  start_url?: string
}

interface PipelineStartResponse {
  run_id: string
  message: string
  status: string
}

export interface ServerStatus {
  server: string
  astra_db_configured: boolean
  watson_configured: boolean
  astra_endpoint: string
  collection_name: string
  astra_connection: string
  collections: string[]
}

export async function askQuestion(req: AskQuestionRequest): Promise<AskQuestionResponse> {
  const { apiBase, apiKey, query, topK = 3, runId } = req
  
  const url = `${apiBase}/answer`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const body = JSON.stringify({
    query,
    top_k: topK,
    ...(runId && { run_id: runId })
  })
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body
  })
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  
  // Defensive programming: ensure response has expected structure
  return {
    answer: data?.answer || 'No answer available',
    sources: Array.isArray(data?.sources) ? data.sources : []
  }
}

export async function startPipeline(req: PipelineRequest): Promise<PipelineStartResponse> {
  const { apiBase, apiKey, startUrl, maxDepth = 2, maxPages = 50 } = req
  
  const url = `${apiBase}/pipeline/start`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const body = JSON.stringify({
    start_url: startUrl,
    max_depth: maxDepth,
    max_pages: maxPages
  })
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body
  })
  
  if (!response.ok) {
    throw new Error(`Pipeline start failed: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

export async function getPipelineStatus(apiBase: string, runId: string, apiKey?: string): Promise<PipelineStatus> {
  const url = `${apiBase}/pipeline/status/${runId}`
  const headers: Record<string, string> = {}
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  })
  
  if (!response.ok) {
    throw new Error(`Status check failed: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  
  // Defensive programming: ensure response has expected structure
  return {
    run_id: data?.run_id || runId,
    status: data?.status || 'not_found',
    progress: data?.progress || { step: 'unknown', current_step: 0, total_steps: 0 },
    logs: Array.isArray(data?.logs) ? data.logs : [],
    start_time: data?.start_time,
    end_time: data?.end_time,
    site_name: data?.site_name,
    start_url: data?.start_url
  }
}

export async function listPipelines(apiBase: string, apiKey?: string): Promise<{ pipelines: string[] }> {
  const url = `${apiBase}/pipeline/list`
  const headers: Record<string, string> = {}
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  })
  
  if (!response.ok) {
    throw new Error(`List pipelines failed: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  
  // Defensive programming: ensure response has expected structure
  return {
    pipelines: Array.isArray(data?.pipelines) ? data.pipelines : []
  }
}

export interface PipelineHistoryItem {
  run_id: string
  status: 'running' | 'completed' | 'failed' | 'not_found'
  site_name: string
  start_url: string
  start_time?: string
  end_time?: string
}

export async function getPipelineHistory(apiBase: string, apiKey?: string): Promise<{ history: PipelineHistoryItem[] }> {
  const url = `${apiBase}/pipeline/history`
  const headers: Record<string, string> = {}
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  })
  
  if (!response.ok) {
    throw new Error(`Get pipeline history failed: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  
  // Defensive programming: ensure response has expected structure
  return {
    history: Array.isArray(data?.history) ? data.history : []
  }
}

export async function deletePipeline(apiBase: string, runId: string, apiKey?: string): Promise<{ message: string }> {
  const url = `${apiBase}/pipeline/${runId}`
  const headers: Record<string, string> = {}
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const response = await fetch(url, {
    method: 'DELETE',
    headers
  })
  
  if (!response.ok) {
    throw new Error(`Delete pipeline failed: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

export async function getServerStatus(apiBase: string, apiKey?: string): Promise<ServerStatus> {
  const url = `${apiBase}/status`
  const headers: Record<string, string> = {}
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  })
  
  if (!response.ok) {
    throw new Error(`Status check failed: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  
  // Defensive programming: ensure response has expected structure
  return {
    server: data?.server || 'unknown',
    astra_db_configured: Boolean(data?.astra_db_configured),
    watson_configured: Boolean(data?.watson_configured),
    astra_endpoint: data?.astra_endpoint || 'not_set',
    collection_name: data?.collection_name || 'unknown',
    astra_connection: data?.astra_connection || 'unknown',
    collections: Array.isArray(data?.collections) ? data.collections : []
  }
}

export async function testChatbot(req: AskQuestionRequest): Promise<AskQuestionResponse> {
  const { apiBase, apiKey, query, topK = 3, runId } = req
  
  const url = `${apiBase}/chat/test`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  const body = JSON.stringify({
    query,
    top_k: topK,
    ...(runId && { run_id: runId })
  })
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body
  })
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  
  // Defensive programming: ensure response has expected structure
  return {
    answer: data?.answer || 'No answer available',
    sources: Array.isArray(data?.sources) ? data.sources : []
  }
}


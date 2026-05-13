// Mobile API client — connects to the Minoverse backend
// The mobile app is a thin client; all processing happens in the cloud.

import axios from "axios"

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000"

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
})

// Request interceptor — attach auth token
api.interceptors.request.use((config) => {
  const token = process.env.EXPO_PUBLIC_API_KEY
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface IngestRequest {
  url: string
  mode?: "quick" | "technical" | "research"
}

export interface IngestResult {
  id: string
  title?: string
  summary?: string
  source_type: string
  source_url: string
  tags: string[]
  entities: Array<{ name: string; type: string }>
}

export interface MemoryResult {
  memories: Array<{
    id: string
    type: string
    content: string
    importance_score: number
    created_at: string
  }>
  total: number
}

export const ApiService = {
  async health() {
    const res = await api.get("/health")
    return res.data
  },

  async ingest(req: IngestRequest): Promise<IngestResult> {
    const res = await api.post("/ingest/url", {
      ...req,
      store_memory: true,
      update_graph: true,
    })
    return res.data
  },

  async research(topic: string) {
    const res = await api.post("/research/search", { query: topic })
    return res.data
  },

  async queryMemory(query: string, limit = 10): Promise<MemoryResult> {
    const res = await api.post("/memory/query", { query, limit })
    return res.data
  },

  async listRecent(limit = 20) {
    const res = await api.get(`/ingest/recent?limit=${limit}`)
    return res.data
  },
}

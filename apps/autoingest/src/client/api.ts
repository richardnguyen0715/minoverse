// Minoverse API Client
// Typed client for the FastAPI backend

import { getConfig } from "@/config/config"

export interface IngestRequest {
  url: string
  mode?: "quick" | "technical" | "research"
  store_memory?: boolean
  update_graph?: boolean
}

export interface IngestResult {
  id: string
  title: string
  summary: string
  entities: Entity[]
  source_type: string
  source_url: string
  tags: string[]
  processing_time_ms: number
}

export interface Entity {
  name: string
  type: string
  confidence: number
}

export interface ResearchRequest {
  topic: string
  depth?: "quick" | "deep"
  sources?: string[]
}

export interface ResearchResult {
  topic: string
  summary: string
  key_findings: string[]
  entities: Entity[]
  related_resources: RelatedResource[]
  report: string
}

export interface RelatedResource {
  id: string
  title: string
  url: string
  relevance_score: number
}

export interface MemoryQueryRequest {
  query: string
  limit?: number
  types?: ("episodic" | "semantic" | "procedural")[]
}

export interface MemoryQueryResult {
  memories: Memory[]
  total: number
}

export interface Memory {
  id: string
  type: string
  content: string
  importance_score: number
  created_at: string
}

export interface GraphQueryResult {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphNode {
  id: string
  name: string
  type: string
}

export interface GraphEdge {
  source: string
  target: string
  type: string
  weight: number
}

export interface HealthResult {
  status: "ok" | "degraded" | "error"
  version: string
  components: Record<string, "ok" | "error">
}

class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public body?: unknown,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export class MinoverseClient {
  private baseUrl: string
  private apiKey?: string

  constructor() {
    const cfg = getConfig()
    this.baseUrl = cfg.MINOVERSE_API_URL.replace(/\/$/, "")
    this.apiKey = cfg.MINOVERSE_API_KEY
  }

  private headers(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    }
    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`
    }
    return headers
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const res = await fetch(url, {
      method,
      headers: this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    })

    if (!res.ok) {
      const text = await res.text().catch(() => "")
      throw new ApiError(res.status, `API ${method} ${path} failed: ${res.statusText}`, text)
    }

    return res.json() as Promise<T>
  }

  async health(): Promise<HealthResult> {
    return this.request<HealthResult>("GET", "/health")
  }

  // Ingest a URL
  async ingest(req: IngestRequest): Promise<IngestResult> {
    return this.request<IngestResult>("POST", "/ingest/url", req)
  }

  // Stream ingest events (SSE)
  async *ingestStream(req: IngestRequest): AsyncGenerator<IngestEvent> {
    const url = `${this.baseUrl}/ingest/url/stream`
    const res = await fetch(url, {
      method: "POST",
      headers: { ...this.headers(), Accept: "text/event-stream" },
      body: JSON.stringify(req),
    })

    if (!res.ok || !res.body) {
      throw new ApiError(res.status, `Stream failed: ${res.statusText}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split("\n")
      buffer = lines.pop() ?? ""

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim()
          if (data === "[DONE]") return
          try {
            yield JSON.parse(data) as IngestEvent
          } catch {
            // skip malformed lines
          }
        }
      }
    }
  }

  // Research a topic
  async research(req: ResearchRequest): Promise<ResearchResult> {
    return this.request<ResearchResult>("POST", "/research", req)
  }

  // Query memory
  async queryMemory(req: MemoryQueryRequest): Promise<MemoryQueryResult> {
    return this.request<MemoryQueryResult>("POST", "/memory/query", req)
  }

  // Get knowledge graph context
  async graphContext(entityName: string): Promise<GraphQueryResult> {
    return this.request<GraphQueryResult>(
      "GET",
      `/graph/context?entity=${encodeURIComponent(entityName)}`,
    )
  }

  // List recent ingests
  async listRecent(limit = 10): Promise<IngestResult[]> {
    return this.request<IngestResult[]>("GET", `/ingest/recent?limit=${limit}`)
  }
}

export interface IngestEvent {
  type:
    | "started"
    | "scraping"
    | "scraped"
    | "extracting_entities"
    | "entities_extracted"
    | "summarizing"
    | "summarized"
    | "storing"
    | "stored"
    | "graph_updated"
    | "completed"
    | "error"
  message: string
  data?: unknown
  progress?: number // 0-100
}

export const apiClient = new MinoverseClient()

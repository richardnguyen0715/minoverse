// Shared TUI types

export type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: number
}

export type ToolEvent = {
  id: string
  tool: string
  status: "running" | "done" | "error"
  preview: string
  durationMs?: number
  startedAt: number
}

export type AgentStatus = "idle" | "thinking" | "running" | "error"

export type Stats = {
  steps: number
  memories: number
  entities: number
  durationMs: number
}

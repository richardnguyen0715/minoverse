import { useState, useCallback, useRef } from "react"
import { v4 as uuid } from "uuid"
import { AgentRuntime } from "@/agent/agent"
import type { AgentEvent } from "@/agent/agent"
import type { ChatMessage, ToolEvent, AgentStatus, Stats } from "@/tui/types"

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: [
    "Welcome to AutoIngest 🧠  — your autonomous research assistant.",
    "",
    "  https://...            Analyze any URL",
    "  /research <topic>      Deep multi-source research",
    "  /memory <query>        Search knowledge base",
    "  /tools                 List available tools",
    "  /health                System status",
    "  /help                  Show this message",
    "  Ctrl+C                 Exit",
  ].join("\n"),
  timestamp: Date.now(),
}

export function useAgent() {
  // Use () => [] init to run only once; add WELCOME separately to avoid double-render dups
  const initialized = useRef(false)
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    initialized.current = true
    return [WELCOME]
  })
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([])
  const [status, setStatus] = useState<AgentStatus>("idle")
  const [currentStream, setCurrentStream] = useState("")
  const [stats, setStats] = useState<Stats>({ steps: 0, memories: 0, entities: 0, durationMs: 0 })

  const streamRef = useRef("")
  const toolStartTimes = useRef<Record<string, number>>({})
  const activeToolId = useRef<Record<string, string>>({}) // toolName → eventId

  const submit = useCallback(
    async (input: string) => {
      const trimmed = input.trim()
      if (!trimmed || status !== "idle") return

      // Built-in slash commands handled inline
      if (trimmed === "/help") {
        setMessages((prev) => [
          ...prev,
          { id: uuid(), role: "user", content: "/help", timestamp: Date.now() },
          { ...WELCOME, id: `help-${Date.now()}` },
        ])
        return
      }
      if (trimmed === "/tools") {
        const { globalRegistry } = await import("@/tools/index")
        const list = globalRegistry
          .list()
          .map((t) => `  • ${t.name} — ${t.description}`)
          .join("\n")
        setMessages((prev) => [
          ...prev,
          { id: uuid(), role: "user", content: "/tools", timestamp: Date.now() },
          { id: uuid(), role: "assistant", content: `Available tools:\n${list}`, timestamp: Date.now() },
        ])
        return
      }

      // Add user message
      setMessages((prev) => [
        ...prev,
        { id: uuid(), role: "user", content: trimmed, timestamp: Date.now() },
      ])
      setToolEvents([])
      setStatus("thinking")
      streamRef.current = ""
      setCurrentStream("")

      const isUrl = /^https?:\/\//i.test(trimmed)
      const isAnalyzeCmd = /^\/analyze\s+https?:\/\//i.test(trimmed)
      const isResearch = trimmed.startsWith("/research ")
      const taskType = isUrl || isAnalyzeCmd ? "analyze" : isResearch ? "research" : "custom"
      const taskInput = isAnalyzeCmd
        ? trimmed.replace(/^\/analyze\s+/, "")
        : isResearch
          ? trimmed.replace(/^\/research\s+/, "")
          : trimmed

      const runtime = new AgentRuntime((event: AgentEvent) => {
        switch (event.type) {
          case "thinking":
            setStatus("thinking")
            break

          case "tool_call": {
            setStatus("running")
            const toolName = event.step?.tool ?? "unknown"
            const toolId = uuid()
            toolStartTimes.current[toolName] = Date.now()
            activeToolId.current[toolName] = toolId
            setToolEvents((prev) => [
              ...prev,
              { id: toolId, tool: toolName, status: "running", preview: "", startedAt: Date.now() },
            ])
            break
          }

          case "tool_result": {
            const toolName = event.step?.tool ?? ""
            const eventId = activeToolId.current[toolName]
            const started = toolStartTimes.current[toolName] ?? Date.now()
            const durationMs = Date.now() - started
            const preview = String(event.message ?? "").slice(0, 60)
            setToolEvents((prev) =>
              prev.map((t) =>
                t.id === eventId ? { ...t, status: "done", preview, durationMs } : t,
              ),
            )
            break
          }

          case "stream_token":
            streamRef.current += event.token ?? ""
            setCurrentStream(streamRef.current)
            break

          case "complete": {
            const result = event.result
            if (result) {
              setMessages((prev) => [
                ...prev,
                { id: uuid(), role: "assistant", content: result.answer, timestamp: Date.now() },
              ])
              setStats({
                steps: result.steps.length,
                memories: result.memories_stored,
                entities: result.entities.length,
                durationMs: result.duration_ms,
              })
            }
            streamRef.current = ""
            setCurrentStream("")
            setStatus("idle")
            break
          }

          case "error":
            setMessages((prev) => [
              ...prev,
              {
                id: uuid(),
                role: "assistant",
                content: `⚠ Error: ${event.message ?? "Unknown error"}`,
                timestamp: Date.now(),
              },
            ])
            streamRef.current = ""
            setCurrentStream("")
            setStatus("error")
            setTimeout(() => setStatus("idle"), 1500)
            break
        }
      })

      try {
        await runtime.run({
          id: uuid(),
          type: taskType,
          input: taskInput,
          sessionId: uuid(),
          mode: "technical",
        })
      } catch (err) {
        const msg = String(err)
        const hint = msg.includes("ECONNREFUSED") || msg.includes("fetch")
          ? "\n\nHint: Is Ollama running? Start it with: ollama serve\nIs the API running? Run: make start"
          : ""
        setMessages((prev) => [
          ...prev,
          {
            id: uuid(),
            role: "assistant",
            content: `⚠ ${msg}${hint}`,
            timestamp: Date.now(),
          },
        ])
        setStatus("idle")
      }
    },
    [status],
  )

  return { messages, toolEvents, status, currentStream, stats, submit }
}

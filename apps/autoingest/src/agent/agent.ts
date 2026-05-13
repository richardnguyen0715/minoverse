// Agent Runtime
// Autonomous research & knowledge agent loop:
// observe → retrieve_memory → plan → select_tool → execute → reflect → update_memory

import { getProvider, type Provider, type Message } from "@/provider/provider"
import { globalRegistry, type ToolOutput } from "@/tools"
import { getConfig } from "@/config/config"
import { apiClient } from "@/client/api"

export interface AgentTask {
  id: string
  type: "analyze" | "research" | "memory" | "custom"
  input: string
  context?: string
  sessionId: string
  userId?: string
  mode?: "quick" | "technical" | "research"
}

export interface AgentStep {
  step: number
  action: "observe" | "plan" | "tool_call" | "reflect" | "complete"
  thought?: string
  tool?: string
  toolInput?: unknown
  toolOutput?: ToolOutput
  timestamp: number
}

export interface AgentResult {
  taskId: string
  success: boolean
  answer: string
  steps: AgentStep[]
  entities: Array<{ name: string; type: string }>
  memories_stored: number
  graph_updated: boolean
  duration_ms: number
}

export type AgentEventCallback = (event: AgentEvent) => void

export interface AgentEvent {
  type:
    | "step_started"
    | "thinking"
    | "tool_call"
    | "tool_result"
    | "step_done"
    | "stream_token"
    | "complete"
    | "error"
  step?: AgentStep
  token?: string
  message?: string
  result?: AgentResult
}

const SYSTEM_PROMPT = `You are an autonomous research and knowledge agent for the Minoverse system.

Your mission: ingest, analyze, and extract knowledge from content to build a persistent knowledge infrastructure.

You follow this loop:
1. OBSERVE: Understand the task and what information is needed
2. RETRIEVE MEMORY: Check what you already know about relevant topics
3. PLAN: Decide which tools to use and in what order
4. EXECUTE: Call tools to gather and process information
5. REFLECT: Evaluate what was learned and what should be stored
6. STORE: Update memory and knowledge graph with new insights

Available tools:
{TOOL_DESCRIPTIONS}

Response format for tool calls:
<tool_call>
{
  "tool": "tool_name",
  "input": { ... }
}
</tool_call>

When done, provide your final answer prefixed with <final_answer> ... </final_answer>

Guidelines:
- Always check memory before scraping
- Always extract entities from content
- Always store important findings in memory
- Always update the graph after entity extraction
- Be thorough but efficient — don't make unnecessary tool calls
- Cite sources in your final answer`

const MAX_STEPS = 15

export class AgentRuntime {
  private provider: Provider
  private onEvent?: AgentEventCallback

  constructor(onEvent?: AgentEventCallback) {
    this.provider = getProvider()
    this.onEvent = onEvent
  }

  private emit(event: AgentEvent): void {
    this.onEvent?.(event)
  }

  async run(task: AgentTask): Promise<AgentResult> {
    const startTime = Date.now()
    const steps: AgentStep[] = []
    let stepCount = 0
    const entities: Array<{ name: string; type: string }> = []
    let memoriesStored = 0
    let graphUpdated = false

    const toolDefs = globalRegistry.definitions()
    const toolDescriptions = toolDefs
      .map((t) => `- ${t.name}: ${t.description}`)
      .join("\n")

    const systemPrompt = SYSTEM_PROMPT.replace("{TOOL_DESCRIPTIONS}", toolDescriptions)

    const messages: Message[] = [
      { role: "system", content: systemPrompt },
      {
        role: "user",
        content: `Task type: ${task.type}
Mode: ${task.mode ?? "technical"}
Input: ${task.input}
${task.context ? `\nAdditional context:\n${task.context}` : ""}`,
      },
    ]

    let finalAnswer = ""

    try {
      while (stepCount < MAX_STEPS) {
        stepCount++
        const step: AgentStep = {
          step: stepCount,
          action: "plan",
          timestamp: Date.now(),
        }

        this.emit({ type: "step_started", step })

        // Get next agent action
        let responseText = ""
        this.emit({ type: "thinking", message: `Step ${stepCount}: thinking...` })

        for await (const token of this.provider.stream(messages, {
          temperature: 0.3,
          maxTokens: 1500,
        })) {
          responseText += token
          this.emit({ type: "stream_token", token })
        }

        messages.push({ role: "assistant", content: responseText })

        // Check for final answer
        const finalMatch = responseText.match(/<final_answer>([\s\S]*?)<\/final_answer>/)
        if (finalMatch) {
          finalAnswer = finalMatch[1].trim()
          step.action = "complete"
          steps.push(step)
          this.emit({ type: "step_done", step })
          break
        }

        // Parse tool calls
        const toolCallMatch = responseText.match(/<tool_call>([\s\S]*?)<\/tool_call>/)
        if (!toolCallMatch) {
          // No tool call and no final answer — agent is stuck, extract partial answer
          finalAnswer = responseText
          step.action = "complete"
          steps.push(step)
          break
        }

        let toolCall: { tool: string; input: Record<string, unknown> }
        try {
          toolCall = JSON.parse(toolCallMatch[1].trim())
        } catch {
          messages.push({
            role: "user",
            content:
              "Your tool_call JSON was malformed. Please fix it and try again with valid JSON.",
          })
          continue
        }

        step.action = "tool_call"
        step.tool = toolCall.tool
        step.toolInput = toolCall.input
        step.thought = responseText.split("<tool_call>")[0].trim()

        this.emit({
          type: "tool_call",
          step,
          message: `Calling ${toolCall.tool}...`,
        })

        // Execute tool
        const toolOutput = await globalRegistry.execute(toolCall.tool, toolCall.input, {
          provider: this.provider,
          sessionId: task.sessionId,
          userId: task.userId,
        })

        step.toolOutput = toolOutput
        steps.push(step)

        this.emit({ type: "tool_result", step })

        // Track side effects
        if (toolCall.tool === "store_memory" && toolOutput.success) {
          memoriesStored++
        }
        if (toolCall.tool === "build_graph" && toolOutput.success) {
          graphUpdated = true
        }
        if (toolCall.tool === "extract_entities" && toolOutput.success) {
          const data = toolOutput.data as { entities?: Array<{ name: string; type: string }> }
          if (data?.entities) {
            entities.push(...data.entities)
          }
        }

        // Feed tool result back to agent
        const toolResultMsg =
          toolOutput.success
            ? `Tool ${toolCall.tool} result:\n${JSON.stringify(toolOutput.data, null, 2)}`
            : `Tool ${toolCall.tool} failed: ${toolOutput.error}`

        messages.push({ role: "user", content: toolResultMsg })
      }

      if (!finalAnswer) {
        finalAnswer = "Agent reached maximum steps without a complete answer."
      }

      const result: AgentResult = {
        taskId: task.id,
        success: true,
        answer: finalAnswer,
        steps,
        entities,
        memories_stored: memoriesStored,
        graph_updated: graphUpdated,
        duration_ms: Date.now() - startTime,
      }

      this.emit({ type: "complete", result })
      return result
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      this.emit({ type: "error", message })

      return {
        taskId: task.id,
        success: false,
        answer: `Agent error: ${message}`,
        steps,
        entities,
        memories_stored: memoriesStored,
        graph_updated: graphUpdated,
        duration_ms: Date.now() - startTime,
      }
    }
  }
}

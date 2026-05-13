// Tool System — Base interface and registry
// All agent capabilities are expressed as tools

import type { Provider } from "@/provider/provider"

export interface ToolInput {
  [key: string]: unknown
}

export interface ToolOutput {
  success: boolean
  data?: unknown
  error?: string
  metadata?: Record<string, unknown>
}

export interface ToolContext {
  provider: Provider
  sessionId: string
  userId?: string
}

export abstract class BaseTool<TInput extends ToolInput = ToolInput> {
  abstract readonly name: string
  abstract readonly description: string
  abstract readonly inputSchema: Record<string, ToolParamSchema>

  abstract run(input: TInput, ctx: ToolContext): Promise<ToolOutput>

  // Validate input against schema (basic validation)
  validate(input: unknown): input is TInput {
    if (typeof input !== "object" || input === null) return false
    const inp = input as Record<string, unknown>
    for (const [key, schema] of Object.entries(this.inputSchema)) {
      if (schema.required && !(key in inp)) return false
    }
    return true
  }

  toJSON(): ToolDefinition {
    return {
      name: this.name,
      description: this.description,
      parameters: {
        type: "object",
        properties: this.inputSchema,
        required: Object.entries(this.inputSchema)
          .filter(([, s]) => s.required)
          .map(([k]) => k),
      },
    }
  }
}

export interface ToolParamSchema {
  type: "string" | "number" | "boolean" | "array" | "object"
  description: string
  required?: boolean
  enum?: string[]
  default?: unknown
  items?: ToolParamSchema
}

export interface ToolDefinition {
  name: string
  description: string
  parameters: {
    type: "object"
    properties: Record<string, ToolParamSchema>
    required: string[]
  }
}

// ── Tool Registry ─────────────────────────────────────────────────────────────

export class ToolRegistry {
  private tools = new Map<string, BaseTool>()

  register(tool: BaseTool): void {
    this.tools.set(tool.name, tool)
  }

  get(name: string): BaseTool | undefined {
    return this.tools.get(name)
  }

  list(): BaseTool[] {
    return Array.from(this.tools.values())
  }

  definitions(): ToolDefinition[] {
    return this.list().map((t) => t.toJSON())
  }

  async execute(
    name: string,
    input: ToolInput,
    ctx: ToolContext,
  ): Promise<ToolOutput> {
    const tool = this.get(name)
    if (!tool) {
      return { success: false, error: `Tool not found: ${name}` }
    }

    if (!tool.validate(input)) {
      return { success: false, error: `Invalid input for tool: ${name}` }
    }

    try {
      return await tool.run(input, ctx)
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      return { success: false, error: `Tool ${name} failed: ${message}` }
    }
  }
}

export const globalRegistry = new ToolRegistry()

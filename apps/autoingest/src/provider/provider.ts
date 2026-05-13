// LLM Provider Abstraction
// Supports OpenAI, Anthropic, Ollama with unified interface

import { getConfig } from "@/config/config"

export interface Message {
  role: "system" | "user" | "assistant"
  content: string
}

export interface CompletionOptions {
  model?: string
  temperature?: number
  maxTokens?: number
  stream?: boolean
}

export interface CompletionResult {
  content: string
  model: string
  usage?: {
    promptTokens: number
    completionTokens: number
    totalTokens: number
  }
}

export interface Provider {
  name: string
  complete(messages: Message[], opts?: CompletionOptions): Promise<CompletionResult>
  stream(messages: Message[], opts?: CompletionOptions): AsyncGenerator<string>
}

// ── Ollama Provider ──────────────────────────────────────────────────────────

export class OllamaProvider implements Provider {
  readonly name = "ollama"
  private baseUrl: string

  constructor() {
    this.baseUrl = getConfig().OLLAMA_BASE_URL
  }

  async complete(messages: Message[], opts: CompletionOptions = {}): Promise<CompletionResult> {
    const model = opts.model ?? getConfig().DEFAULT_MODEL
    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages,
        stream: false,
        options: {
          temperature: opts.temperature ?? 0.7,
          num_predict: opts.maxTokens ?? 2048,
        },
      }),
    })

    if (!res.ok) throw new Error(`Ollama error: ${res.statusText}`)
    const data = (await res.json()) as {
      message: { content: string }
      model: string
      prompt_eval_count?: number
      eval_count?: number
    }

    return {
      content: data.message.content,
      model: data.model,
      usage: {
        promptTokens: data.prompt_eval_count ?? 0,
        completionTokens: data.eval_count ?? 0,
        totalTokens: (data.prompt_eval_count ?? 0) + (data.eval_count ?? 0),
      },
    }
  }

  async *stream(messages: Message[], opts: CompletionOptions = {}): AsyncGenerator<string> {
    const model = opts.model ?? getConfig().DEFAULT_MODEL
    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages,
        stream: true,
        options: { temperature: opts.temperature ?? 0.7 },
      }),
    })

    if (!res.ok || !res.body) throw new Error(`Ollama stream error: ${res.statusText}`)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const lines = decoder.decode(value).split("\n").filter(Boolean)
      for (const line of lines) {
        try {
          const chunk = JSON.parse(line) as { message?: { content?: string }; done?: boolean }
          if (chunk.message?.content) yield chunk.message.content
        } catch {
          // skip
        }
      }
    }
  }
}

// ── OpenAI Provider ──────────────────────────────────────────────────────────

export class OpenAIProvider implements Provider {
  readonly name = "openai"

  async complete(messages: Message[], opts: CompletionOptions = {}): Promise<CompletionResult> {
    const key = getConfig().OPENAI_API_KEY
    if (!key) throw new Error("OPENAI_API_KEY not set")

    const model = opts.model ?? "gpt-4o-mini"
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: opts.temperature ?? 0.7,
        max_tokens: opts.maxTokens ?? 2048,
        stream: false,
      }),
    })

    if (!res.ok) throw new Error(`OpenAI error: ${res.statusText}`)
    const data = (await res.json()) as {
      choices: Array<{ message: { content: string } }>
      model: string
      usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
    }

    return {
      content: data.choices[0].message.content,
      model: data.model,
      usage: data.usage
        ? {
            promptTokens: data.usage.prompt_tokens,
            completionTokens: data.usage.completion_tokens,
            totalTokens: data.usage.total_tokens,
          }
        : undefined,
    }
  }

  async *stream(messages: Message[], opts: CompletionOptions = {}): AsyncGenerator<string> {
    const key = getConfig().OPENAI_API_KEY
    if (!key) throw new Error("OPENAI_API_KEY not set")

    const model = opts.model ?? "gpt-4o-mini"
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: opts.temperature ?? 0.7,
        max_tokens: opts.maxTokens ?? 2048,
        stream: true,
      }),
    })

    if (!res.ok || !res.body) throw new Error(`OpenAI stream error: ${res.statusText}`)

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
        if (!line.startsWith("data: ")) continue
        const data = line.slice(6).trim()
        if (data === "[DONE]") return
        try {
          const chunk = JSON.parse(data) as {
            choices?: Array<{ delta?: { content?: string } }>
          }
          const text = chunk.choices?.[0]?.delta?.content
          if (text) yield text
        } catch {
          // skip
        }
      }
    }
  }
}

// ── Anthropic Provider ───────────────────────────────────────────────────────

export class AnthropicProvider implements Provider {
  readonly name = "anthropic"

  async complete(messages: Message[], opts: CompletionOptions = {}): Promise<CompletionResult> {
    const key = getConfig().ANTHROPIC_API_KEY
    if (!key) throw new Error("ANTHROPIC_API_KEY not set")

    const model = opts.model ?? "claude-3-5-haiku-20241022"
    const system = messages.find((m) => m.role === "system")
    const userMessages = messages.filter((m) => m.role !== "system")

    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model,
        max_tokens: opts.maxTokens ?? 2048,
        system: system?.content,
        messages: userMessages,
        temperature: opts.temperature ?? 0.7,
      }),
    })

    if (!res.ok) throw new Error(`Anthropic error: ${res.statusText}`)
    const data = (await res.json()) as {
      content: Array<{ type: string; text?: string }>
      model: string
      usage?: { input_tokens: number; output_tokens: number }
    }

    const content = data.content
      .filter((b) => b.type === "text")
      .map((b) => b.text ?? "")
      .join("")

    return {
      content,
      model: data.model,
      usage: data.usage
        ? {
            promptTokens: data.usage.input_tokens,
            completionTokens: data.usage.output_tokens,
            totalTokens: data.usage.input_tokens + data.usage.output_tokens,
          }
        : undefined,
    }
  }

  async *stream(messages: Message[], opts: CompletionOptions = {}): AsyncGenerator<string> {
    const key = getConfig().ANTHROPIC_API_KEY
    if (!key) throw new Error("ANTHROPIC_API_KEY not set")

    const model = opts.model ?? "claude-3-5-haiku-20241022"
    const system = messages.find((m) => m.role === "system")
    const userMessages = messages.filter((m) => m.role !== "system")

    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model,
        max_tokens: opts.maxTokens ?? 2048,
        system: system?.content,
        messages: userMessages,
        stream: true,
      }),
    })

    if (!res.ok || !res.body) throw new Error(`Anthropic stream error: ${res.statusText}`)

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
        if (!line.startsWith("data: ")) continue
        const data = line.slice(6).trim()
        try {
          const chunk = JSON.parse(data) as {
            type?: string
            delta?: { type?: string; text?: string }
          }
          if (chunk.type === "content_block_delta" && chunk.delta?.text) {
            yield chunk.delta.text
          }
        } catch {
          // skip
        }
      }
    }
  }
}

// ── Provider Registry ────────────────────────────────────────────────────────

const providers: Record<string, Provider> = {
  ollama: new OllamaProvider(),
  openai: new OpenAIProvider(),
  anthropic: new AnthropicProvider(),
}

export function getProvider(name?: string): Provider {
  const cfg = getConfig()
  const key = name ?? cfg.DEFAULT_PROVIDER
  const provider = providers[key]
  if (!provider) throw new Error(`Unknown provider: ${key}`)
  return provider
}

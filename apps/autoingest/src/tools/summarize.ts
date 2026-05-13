// Summarization Tools
// Three modes: quick (TLDR), technical (architecture/perf), research (novelty/impact)

import { BaseTool, type ToolInput, type ToolOutput, type ToolContext } from "./base"
import type { Message } from "@/provider/provider"

interface SummarizeInput extends ToolInput {
  content: string
  title?: string
  source_url?: string
}

// ── SummarizeShortTool (TLDR) ──────────────────────────────────────────────────

export class SummarizeShortTool extends BaseTool<SummarizeInput> {
  readonly name = "summarize_short"
  readonly description =
    "Generate a concise TLDR summary (2-4 sentences) of content. Best for quick overview of articles, posts, or documents."

  readonly inputSchema = {
    content: {
      type: "string" as const,
      description: "Content to summarize",
      required: true,
    },
    title: {
      type: "string" as const,
      description: "Optional title context",
    },
    source_url: {
      type: "string" as const,
      description: "Optional source URL for context",
    },
  }

  async run(input: SummarizeInput, ctx: ToolContext): Promise<ToolOutput> {
    try {
      const messages: Message[] = [
        {
          role: "system",
          content:
            "You are a concise technical summarizer. Produce a TLDR in 2-4 sentences. Focus on the core idea and key takeaways. Be direct and specific.",
        },
        {
          role: "user",
          content: `${input.title ? `Title: ${input.title}\n\n` : ""}${input.source_url ? `URL: ${input.source_url}\n\n` : ""}Content:\n${input.content.slice(0, 6000)}`,
        },
      ]

      const result = await ctx.provider.complete(messages, { temperature: 0.3, maxTokens: 300 })
      return {
        success: true,
        data: {
          summary: result.content,
          mode: "quick",
          model: result.model,
        },
      }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── SummarizeTechnicalTool ────────────────────────────────────────────────────

export class SummarizeTechnicalTool extends BaseTool<SummarizeInput> {
  readonly name = "summarize_technical"
  readonly description =
    "Generate a structured technical summary covering architecture, performance characteristics, use cases, and limitations."

  readonly inputSchema = {
    content: {
      type: "string" as const,
      description: "Technical content to analyze",
      required: true,
    },
    title: {
      type: "string" as const,
      description: "Optional title",
    },
    source_url: {
      type: "string" as const,
      description: "Optional source URL",
    },
  }

  async run(input: SummarizeInput, ctx: ToolContext): Promise<ToolOutput> {
    try {
      const messages: Message[] = [
        {
          role: "system",
          content: `You are a senior software architect. Analyze the content and produce a structured technical summary with these sections:
## Overview
## Architecture / Design
## Performance Characteristics  
## Use Cases
## Limitations & Tradeoffs
## Key Takeaways

Be specific and technical. Use bullet points where appropriate.`,
        },
        {
          role: "user",
          content: `${input.title ? `Title: ${input.title}\n\n` : ""}${input.source_url ? `URL: ${input.source_url}\n\n` : ""}Content:\n${input.content.slice(0, 8000)}`,
        },
      ]

      const result = await ctx.provider.complete(messages, { temperature: 0.4, maxTokens: 1200 })
      return {
        success: true,
        data: {
          summary: result.content,
          mode: "technical",
          model: result.model,
        },
      }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── SummarizeResearchTool ─────────────────────────────────────────────────────

export class SummarizeResearchTool extends BaseTool<SummarizeInput> {
  readonly name = "summarize_research"
  readonly description =
    "Generate a research-grade summary covering novelty, comparisons with related work, potential impact, and future directions. Best for papers, research posts, and technical announcements."

  readonly inputSchema = {
    content: {
      type: "string" as const,
      description: "Research content to analyze",
      required: true,
    },
    title: {
      type: "string" as const,
      description: "Optional title",
    },
    source_url: {
      type: "string" as const,
      description: "Optional source URL",
    },
  }

  async run(input: SummarizeInput, ctx: ToolContext): Promise<ToolOutput> {
    try {
      const messages: Message[] = [
        {
          role: "system",
          content: `You are an AI research analyst. Analyze the content and produce a research-grade summary:

## Problem Statement
## Proposed Approach / Novelty
## Key Results
## Comparison with Prior Work
## Impact & Significance
## Limitations
## Future Directions
## Practical Implications

Be analytically rigorous. Identify what is genuinely new vs. incremental.`,
        },
        {
          role: "user",
          content: `${input.title ? `Title: ${input.title}\n\n` : ""}${input.source_url ? `URL: ${input.source_url}\n\n` : ""}Content:\n${input.content.slice(0, 10000)}`,
        },
      ]

      const result = await ctx.provider.complete(messages, { temperature: 0.4, maxTokens: 2000 })
      return {
        success: true,
        data: {
          summary: result.content,
          mode: "research",
          model: result.model,
        },
      }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

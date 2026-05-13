// Scraping Tools
// Tools for extracting content from URLs

import { BaseTool, type ToolInput, type ToolOutput, type ToolContext } from "./base"
import { apiClient } from "@/client/api"
import { getConfig } from "@/config/config"

// ── ScrapeUrlTool ─────────────────────────────────────────────────────────────

interface ScrapeUrlInput extends ToolInput {
  url: string
  mode?: "quick" | "technical" | "research"
}

export class ScrapeUrlTool extends BaseTool<ScrapeUrlInput> {
  readonly name = "scrape_url"
  readonly description =
    "Scrape a URL and extract structured content: title, body text, metadata, links, and media references. Supports web articles, GitHub repos, YouTube videos, Reddit posts, and more."

  readonly inputSchema = {
    url: {
      type: "string" as const,
      description: "The URL to scrape",
      required: true,
    },
    mode: {
      type: "string" as const,
      description: "Analysis depth: quick (TLDR), technical (architecture/perf), research (novelty/impact)",
      enum: ["quick", "technical", "research"],
      default: "quick",
    },
  }

  async run(input: ScrapeUrlInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const result = await apiClient.ingest({
        url: input.url,
        mode: input.mode ?? "quick",
        store_memory: false,
        update_graph: false,
      })
      return { success: true, data: result }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── ExtractArticleTool ────────────────────────────────────────────────────────

interface ExtractArticleInput extends ToolInput {
  url: string
  include_comments?: boolean
}

export class ExtractArticleTool extends BaseTool<ExtractArticleInput> {
  readonly name = "extract_article"
  readonly description =
    "Extract the main article content from a web page, blog post, or documentation page. Returns structured text with headings and metadata."

  readonly inputSchema = {
    url: {
      type: "string" as const,
      description: "The article URL",
      required: true,
    },
    include_comments: {
      type: "boolean" as const,
      description: "Whether to include comments section",
      default: false,
    },
  }

  async run(input: ExtractArticleInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/scrape/article`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: input.url,
          include_comments: input.include_comments ?? false,
        }),
      })
      if (!res.ok) throw new Error(`Extract failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── ExtractVideoTool ──────────────────────────────────────────────────────────

interface ExtractVideoInput extends ToolInput {
  url: string
  include_transcript?: boolean
  include_comments?: boolean
}

export class ExtractVideoTool extends BaseTool<ExtractVideoInput> {
  readonly name = "extract_video"
  readonly description =
    "Extract information from a YouTube video: transcript, metadata, description, and optionally comments."

  readonly inputSchema = {
    url: {
      type: "string" as const,
      description: "YouTube video URL",
      required: true,
    },
    include_transcript: {
      type: "boolean" as const,
      description: "Whether to include full transcript",
      default: true,
    },
    include_comments: {
      type: "boolean" as const,
      description: "Whether to include top comments",
      default: false,
    },
  }

  async run(input: ExtractVideoInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/scrape/video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      })
      if (!res.ok) throw new Error(`Video extract failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── ExtractRepoTool ───────────────────────────────────────────────────────────

interface ExtractRepoInput extends ToolInput {
  url: string
  include_issues?: boolean
  include_commits?: boolean
}

export class ExtractRepoTool extends BaseTool<ExtractRepoInput> {
  readonly name = "extract_repo"
  readonly description =
    "Extract information from a GitHub repository: README, stars, issues, commit activity, topics, and contributors."

  readonly inputSchema = {
    url: {
      type: "string" as const,
      description: "GitHub repository URL (e.g. https://github.com/owner/repo)",
      required: true,
    },
    include_issues: {
      type: "boolean" as const,
      description: "Whether to include recent issues",
      default: false,
    },
    include_commits: {
      type: "boolean" as const,
      description: "Whether to include recent commit activity",
      default: false,
    },
  }

  async run(input: ExtractRepoInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/scrape/repo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      })
      if (!res.ok) throw new Error(`Repo extract failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

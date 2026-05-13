// Research Tools
// Tools for web search and repository discovery

import { BaseTool, type ToolInput, type ToolOutput, type ToolContext } from "./base"
import { getConfig } from "@/config/config"

// ── SearchWebTool ─────────────────────────────────────────────────────────────

interface SearchWebInput extends ToolInput {
  query: string
  limit?: number
  sources?: string[]
}

export class SearchWebTool extends BaseTool<SearchWebInput> {
  readonly name = "search_web"
  readonly description =
    "Search the web for information about a topic. Returns titles, URLs, and snippets from relevant pages."

  readonly inputSchema = {
    query: {
      type: "string" as const,
      description: "Search query",
      required: true,
    },
    limit: {
      type: "number" as const,
      description: "Maximum number of results to return",
      default: 10,
    },
    sources: {
      type: "array" as const,
      description: "Preferred sources to search (e.g. ['reddit', 'hackernews', 'github'])",
      items: { type: "string" as const, description: "Source name" },
    },
  }

  async run(input: SearchWebInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/research/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input.query,
          limit: input.limit ?? 10,
          sources: input.sources ?? [],
        }),
      })
      if (!res.ok) throw new Error(`Search failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── FindRepoTool ──────────────────────────────────────────────────────────────

interface FindRepoInput extends ToolInput {
  query: string
  topic?: string
  language?: string
  min_stars?: number
  limit?: number
}

export class FindRepoTool extends BaseTool<FindRepoInput> {
  readonly name = "find_repo"
  readonly description =
    "Search GitHub for repositories matching a query. Useful for discovering tools, frameworks, and projects related to a topic."

  readonly inputSchema = {
    query: {
      type: "string" as const,
      description: "Repository search query",
      required: true,
    },
    topic: {
      type: "string" as const,
      description: "GitHub topic to filter by",
    },
    language: {
      type: "string" as const,
      description: "Programming language filter",
    },
    min_stars: {
      type: "number" as const,
      description: "Minimum stars threshold",
      default: 100,
    },
    limit: {
      type: "number" as const,
      description: "Maximum repositories to return",
      default: 5,
    },
  }

  async run(input: FindRepoInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/research/find-repo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      })
      if (!res.ok) throw new Error(`Repo search failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── SearchHackerNewsTool ──────────────────────────────────────────────────────

interface SearchHNInput extends ToolInput {
  query: string
  limit?: number
  sort?: "relevance" | "date"
}

export class SearchHackerNewsTool extends BaseTool<SearchHNInput> {
  readonly name = "search_hackernews"
  readonly description =
    "Search Hacker News for discussions, posts, and comments about a topic."

  readonly inputSchema = {
    query: {
      type: "string" as const,
      description: "Search query",
      required: true,
    },
    limit: {
      type: "number" as const,
      description: "Maximum results",
      default: 10,
    },
    sort: {
      type: "string" as const,
      description: "Sort order",
      enum: ["relevance", "date"],
      default: "relevance",
    },
  }

  async run(input: SearchHNInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      // Algolia HN search API (public, no auth needed)
      const params = new URLSearchParams({
        query: input.query,
        hitsPerPage: String(input.limit ?? 10),
      })
      if (input.sort === "date") {
        params.set("tags", "story")
      }

      const endpoint =
        input.sort === "date"
          ? "https://hn.algolia.com/api/v1/search_by_date"
          : "https://hn.algolia.com/api/v1/search"

      const res = await fetch(`${endpoint}?${params}`)
      if (!res.ok) throw new Error(`HN search failed: ${res.statusText}`)
      const data = (await res.json()) as {
        hits: Array<{
          title?: string
          url?: string
          objectID: string
          points?: number
          num_comments?: number
          author?: string
          created_at?: string
          story_text?: string
        }>
      }

      const results = data.hits.map((h) => ({
        title: h.title,
        url: h.url ?? `https://news.ycombinator.com/item?id=${h.objectID}`,
        hn_url: `https://news.ycombinator.com/item?id=${h.objectID}`,
        points: h.points,
        comments: h.num_comments,
        author: h.author,
        created_at: h.created_at,
        snippet: h.story_text?.slice(0, 300),
      }))

      return { success: true, data: { results, total: results.length } }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── SearchRedditTool ──────────────────────────────────────────────────────────

interface SearchRedditInput extends ToolInput {
  query: string
  subreddit?: string
  limit?: number
  sort?: "relevance" | "new" | "top"
}

export class SearchRedditTool extends BaseTool<SearchRedditInput> {
  readonly name = "search_reddit"
  readonly description =
    "Search Reddit for discussions and posts about a topic, optionally within a specific subreddit."

  readonly inputSchema = {
    query: {
      type: "string" as const,
      description: "Search query",
      required: true,
    },
    subreddit: {
      type: "string" as const,
      description: "Subreddit to search within (without r/ prefix)",
    },
    limit: {
      type: "number" as const,
      description: "Maximum results",
      default: 10,
    },
    sort: {
      type: "string" as const,
      enum: ["relevance", "new", "top"],
      description: "Sort order",
      default: "relevance",
    },
  }

  async run(input: SearchRedditInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const base = input.subreddit
        ? `https://www.reddit.com/r/${input.subreddit}/search.json`
        : "https://www.reddit.com/search.json"

      const params = new URLSearchParams({
        q: input.query,
        limit: String(input.limit ?? 10),
        sort: input.sort ?? "relevance",
        type: "link",
      })

      if (input.subreddit) {
        params.set("restrict_sr", "1")
      }

      const res = await fetch(`${base}?${params}`, {
        headers: { "User-Agent": "AutoIngest/1.0" },
      })
      if (!res.ok) throw new Error(`Reddit search failed: ${res.statusText}`)
      const data = (await res.json()) as {
        data: {
          children: Array<{
            data: {
              title: string
              url: string
              permalink: string
              score: number
              num_comments: number
              author: string
              subreddit: string
              selftext?: string
              created_utc: number
            }
          }>
        }
      }

      const results = data.data.children.map((c) => ({
        title: c.data.title,
        url: c.data.url,
        reddit_url: `https://reddit.com${c.data.permalink}`,
        score: c.data.score,
        comments: c.data.num_comments,
        author: c.data.author,
        subreddit: c.data.subreddit,
        snippet: c.data.selftext?.slice(0, 300),
        created_at: new Date(c.data.created_utc * 1000).toISOString(),
      }))

      return { success: true, data: { results, total: results.length } }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

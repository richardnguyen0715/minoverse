// Knowledge Tools
// Tools for entity extraction, graph building, and memory management

import { BaseTool, type ToolInput, type ToolOutput, type ToolContext } from "./base"
import { apiClient } from "@/client/api"
import { getConfig } from "@/config/config"

// ── ExtractEntitiesTool ───────────────────────────────────────────────────────

interface ExtractEntitiesInput extends ToolInput {
  content: string
  types?: string[]
}

export class ExtractEntitiesTool extends BaseTool<ExtractEntitiesInput> {
  readonly name = "extract_entities"
  readonly description =
    "Extract named entities from text: companies, repositories, frameworks, tools, papers, people, and concepts. Returns structured entity list with types and confidence scores."

  readonly inputSchema = {
    content: {
      type: "string" as const,
      description: "Text content to extract entities from",
      required: true,
    },
    types: {
      type: "array" as const,
      description: "Entity types to extract (default: all)",
      items: { type: "string" as const, description: "Entity type" },
    },
  }

  async run(input: ExtractEntitiesInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/knowledge/extract-entities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: input.content,
          types: input.types ?? ["company", "repository", "framework", "tool", "paper", "person", "concept"],
        }),
      })
      if (!res.ok) throw new Error(`Entity extraction failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── QueryMemoryTool ───────────────────────────────────────────────────────────

interface QueryMemoryInput extends ToolInput {
  query: string
  limit?: number
  types?: string[]
}

export class QueryMemoryTool extends BaseTool<QueryMemoryInput> {
  readonly name = "query_memory"
  readonly description =
    "Query the long-term memory system for relevant knowledge. Searches across episodic (what happened), semantic (facts/concepts), and procedural (how tasks were solved) memories."

  readonly inputSchema = {
    query: {
      type: "string" as const,
      description: "Natural language query",
      required: true,
    },
    limit: {
      type: "number" as const,
      description: "Maximum memories to return",
      default: 5,
    },
    types: {
      type: "array" as const,
      description: "Memory types to search: episodic, semantic, procedural",
      items: { type: "string" as const, description: "Memory type" },
    },
  }

  async run(input: QueryMemoryInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const result = await apiClient.queryMemory({
        query: input.query,
        limit: input.limit ?? 5,
        types: (input.types as ("episodic" | "semantic" | "procedural")[]) ?? ["episodic", "semantic"],
      })
      return { success: true, data: result }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── StoreMemoryTool ───────────────────────────────────────────────────────────

interface StoreMemoryInput extends ToolInput {
  content: string
  type?: "episodic" | "semantic" | "procedural"
  title?: string
  importance?: number
  tags?: string[]
}

export class StoreMemoryTool extends BaseTool<StoreMemoryInput> {
  readonly name = "store_memory"
  readonly description =
    "Store a piece of knowledge or experience in long-term memory. Use for important insights, discoveries, or facts worth remembering."

  readonly inputSchema = {
    content: {
      type: "string" as const,
      description: "The content to memorize",
      required: true,
    },
    type: {
      type: "string" as const,
      description: "Memory type: episodic (event), semantic (fact), procedural (how-to)",
      enum: ["episodic", "semantic", "procedural"],
      default: "semantic",
    },
    title: {
      type: "string" as const,
      description: "Short title for the memory",
    },
    importance: {
      type: "number" as const,
      description: "Importance score 0.0-1.0",
      default: 0.7,
    },
    tags: {
      type: "array" as const,
      description: "Tags for categorization",
      items: { type: "string" as const, description: "Tag" },
    },
  }

  async run(input: StoreMemoryInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/memory/store`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: input.content,
          memory_type: input.type ?? "semantic",
          title: input.title,
          importance_score: input.importance ?? 0.7,
          tags: input.tags ?? [],
        }),
      })
      if (!res.ok) throw new Error(`Memory store failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── BuildGraphTool ────────────────────────────────────────────────────────────

interface BuildGraphInput extends ToolInput {
  entities: Array<{ name: string; type: string }>
  source_url?: string
  source_id?: string
}

export class BuildGraphTool extends BaseTool<BuildGraphInput> {
  readonly name = "build_graph"
  readonly description =
    "Add entities and their relationships to the knowledge graph. Used after entity extraction to persist structured knowledge."

  readonly inputSchema = {
    entities: {
      type: "array" as const,
      description: "List of entities with name and type",
      items: { type: "object" as const, description: "Entity with name and type" },
      required: true,
    },
    source_url: {
      type: "string" as const,
      description: "Source URL the entities were extracted from",
    },
    source_id: {
      type: "string" as const,
      description: "Source resource ID in the database",
    },
  }

  async run(input: BuildGraphInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const cfg = getConfig()
      const res = await fetch(`${cfg.MINOVERSE_API_URL}/graph/build`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      })
      if (!res.ok) throw new Error(`Graph build failed: ${res.statusText}`)
      const data = await res.json()
      return { success: true, data }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

// ── QueryGraphTool ────────────────────────────────────────────────────────────

interface QueryGraphInput extends ToolInput {
  entity: string
  depth?: number
}

export class QueryGraphTool extends BaseTool<QueryGraphInput> {
  readonly name = "query_graph"
  readonly description =
    "Query the knowledge graph for an entity and its connections. Returns nodes and edges showing relationships."

  readonly inputSchema = {
    entity: {
      type: "string" as const,
      description: "Entity name to query",
      required: true,
    },
    depth: {
      type: "number" as const,
      description: "Graph traversal depth (1-3)",
      default: 1,
    },
  }

  async run(input: QueryGraphInput, _ctx: ToolContext): Promise<ToolOutput> {
    try {
      const result = await apiClient.graphContext(input.entity)
      return { success: true, data: result }
    } catch (err) {
      return { success: false, error: String(err) }
    }
  }
}

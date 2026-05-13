// CLI Command: analyze
// Usage: autoingest analyze <url> [--mode quick|technical|research] [--no-store]

import type { Argv } from "yargs"
import { AgentRuntime, type AgentEvent } from "@/agent/agent"
import { apiClient } from "@/client/api"
import { UI, formatDuration } from "@/cli/ui"
import chalk from "chalk"
import { v4 as uuidv4 } from "uuid"

export interface AnalyzeArgs {
  url: string
  mode?: "quick" | "technical" | "research"
  store: boolean
  graph: boolean
  stream: boolean
  verbose: boolean
}

export function analyzeCommand(yargs: Argv): Argv {
  return yargs.command(
    "analyze <url>",
    "Analyze a URL: scrape, summarize, extract entities, store in knowledge base",
    (y) =>
      y
        .positional("url", {
          describe: "URL to analyze",
          type: "string",
          demandOption: true,
        })
        .option("mode", {
          alias: "m",
          describe: "Analysis depth",
          choices: ["quick", "technical", "research"] as const,
          default: "technical" as const,
        })
        .option("store", {
          describe: "Store result in knowledge base",
          type: "boolean",
          default: true,
        })
        .option("graph", {
          describe: "Update knowledge graph",
          type: "boolean",
          default: true,
        })
        .option("stream", {
          describe: "Stream agent thinking process",
          type: "boolean",
          default: true,
        })
        .option("verbose", {
          alias: "v",
          describe: "Show detailed output",
          type: "boolean",
          default: false,
        }),
    async (argv) => {
      const args = argv as unknown as AnalyzeArgs

      UI.header(`Analyzing ${args.url}`)
      UI.step("🔍", "Mode:", args.mode)
      UI.step("💾", "Store in KB:", String(args.store))
      UI.step("🕸️", "Update graph:", String(args.graph))
      UI.empty()

      const startTime = Date.now()

      if (args.stream) {
        // Use streaming ingest API
        try {
          let lastProgress = 0
          for await (const event of apiClient.ingestStream({
            url: args.url,
            mode: args.mode ?? "technical",
            store_memory: args.store,
            update_graph: args.graph,
          })) {
            switch (event.type) {
              case "started":
                UI.step("🚀", "Started")
                break
              case "scraping":
                UI.step("🕷️", "Scraping content...")
                break
              case "scraped":
                UI.step("✓", "Scraped", "content extracted")
                break
              case "extracting_entities":
                UI.step("🔬", "Extracting entities...")
                break
              case "entities_extracted":
                const data = event.data as { count?: number }
                UI.step("✓", "Entities extracted", `${data?.count ?? 0} found`)
                break
              case "summarizing":
                UI.step("✍️", `Summarizing (${args.mode} mode)...`)
                break
              case "summarized":
                UI.step("✓", "Summary generated")
                break
              case "storing":
                UI.step("💾", "Storing in knowledge base...")
                break
              case "stored":
                UI.step("✓", "Stored")
                break
              case "graph_updated":
                UI.step("🕸️", "Knowledge graph updated")
                break
              case "completed":
                const result = event.data as {
                  summary?: string
                  entities?: Array<{ name: string; type: string }>
                  title?: string
                  tags?: string[]
                }
                UI.empty()
                UI.answerBox(
                  `${chalk.bold(result?.title ?? "Result")}\n\n${result?.summary ?? ""}`,
                )
                if (result?.entities?.length) {
                  UI.entities(result.entities)
                }
                if (result?.tags?.length) {
                  console.log(
                    `  ${chalk.dim("Tags:")} ${result.tags.map((t) => chalk.cyan(t)).join("  ")}`,
                  )
                }
                break
              case "error":
                UI.errorBox("Ingest error", event.message)
                break
            }

            if (event.progress && event.progress > lastProgress) {
              lastProgress = event.progress
            }
          }
        } catch (err) {
          // Fall back to agent mode if streaming not available
          if (args.verbose) {
            UI.step("⚠️", "Stream not available, using agent mode", String(err))
          }
          await runAgentMode(args, startTime)
        }
      } else {
        await runAgentMode(args, startTime)
      }

      UI.stats({
        duration: formatDuration(Date.now() - startTime),
        mode: args.mode ?? "technical",
      })
    },
  )
}

async function runAgentMode(args: AnalyzeArgs, startTime: number): Promise<void> {
  const agent = new AgentRuntime((event: AgentEvent) => {
    switch (event.type) {
      case "thinking":
        if (args.verbose) process.stdout.write(chalk.dim("."))
        break
      case "stream_token":
        if (args.verbose && event.token) process.stdout.write(chalk.dim(event.token))
        break
      case "tool_call":
        UI.toolCall(event.step?.tool ?? "", event.step?.toolInput)
        break
      case "tool_result":
        UI.toolResult(
          event.step?.toolOutput?.success ?? false,
          event.step?.toolOutput?.error,
        )
        break
      case "error":
        UI.errorBox("Agent error", event.message ?? "Unknown error")
        break
    }
  })

  const result = await agent.run({
    id: uuidv4(),
    type: "analyze",
    input: args.url,
    sessionId: uuidv4(),
    mode: args.mode ?? "technical",
  })

  if (args.verbose) UI.empty()

  UI.answerBox(result.answer)

  if (result.entities.length) {
    UI.entities(result.entities)
  }

  UI.stats({
    steps: result.steps.length,
    entities: result.entities.length,
    "memories stored": result.memories_stored,
    "graph updated": result.graph_updated ? "yes" : "no",
    duration: formatDuration(result.duration_ms),
  })
}

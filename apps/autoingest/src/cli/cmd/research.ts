// CLI Command: research
// Usage: autoingest research <topic> [--depth quick|deep] [--sources reddit,hn,github]

import type { Argv } from "yargs"
import { AgentRuntime, type AgentEvent } from "@/agent/agent"
import { UI, formatDuration } from "@/cli/ui"
import chalk from "chalk"
import { v4 as uuidv4 } from "uuid"

interface ResearchArgs {
  topic: string
  depth: "quick" | "deep"
  sources: string[]
  verbose: boolean
}

export function researchCommand(yargs: Argv): Argv {
  return yargs.command(
    "research <topic>",
    "Deep research on a topic: multi-source search, compare, synthesize, generate report",
    (y) =>
      y
        .positional("topic", {
          describe: "Research topic or question",
          type: "string",
          demandOption: true,
        })
        .option("depth", {
          alias: "d",
          describe: "Research depth",
          choices: ["quick", "deep"] as const,
          default: "deep" as const,
        })
        .option("sources", {
          alias: "s",
          describe: "Sources to search (comma-separated: reddit,hn,github,web)",
          type: "string",
          default: "web,hackernews,github",
          coerce: (v: string) => v.split(",").map((s) => s.trim()),
        })
        .option("verbose", {
          alias: "v",
          type: "boolean",
          default: false,
        }),
    async (argv) => {
      const args = argv as unknown as ResearchArgs
      const startTime = Date.now()

      UI.header(`Research: ${args.topic}`)
      UI.step("📊", "Depth:", args.depth)
      UI.step("🌐", "Sources:", (args.sources as unknown as string[]).join(", "))
      UI.empty()

      const contextPrompt = `
Research task: "${args.topic}"
Depth: ${args.depth}
Sources to use: ${(args.sources as unknown as string[]).join(", ")}

Please:
1. Search for information about this topic using available tools
2. Find relevant GitHub repositories if applicable
3. Check Hacker News and Reddit for community discussion
4. Extract key entities and concepts
5. Synthesize findings into a comprehensive report
6. Store key insights in memory
7. Update the knowledge graph with discovered entities

For ${args.depth === "deep" ? "deep" : "quick"} research, ${args.depth === "deep" ? "be thorough and use multiple tools" : "focus on the most relevant sources only"}.`

      const agent = new AgentRuntime((event: AgentEvent) => {
        switch (event.type) {
          case "tool_call":
            UI.toolCall(event.step?.tool ?? "", event.step?.toolInput)
            break
          case "tool_result":
            const output = event.step?.toolOutput
            if (output?.success) {
              const data = output.data as { results?: unknown[]; total?: number }
              const summary = data?.total != null ? `${data.total} results` : "done"
              UI.toolResult(true, summary)
            } else {
              UI.toolResult(false, output?.error)
            }
            break
          case "thinking":
            if (args.verbose) process.stdout.write(chalk.dim("."))
            break
          case "stream_token":
            if (args.verbose && event.token) process.stdout.write(chalk.dim(event.token))
            break
          case "error":
            UI.errorBox("Research error", event.message ?? "Unknown")
            break
        }
      })

      const result = await agent.run({
        id: uuidv4(),
        type: "research",
        input: args.topic,
        context: contextPrompt,
        sessionId: uuidv4(),
        mode: "research",
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
    },
  )
}

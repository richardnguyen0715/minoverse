// CLI Command: memory
// Usage: autoingest memory query <text> | memory list | memory graph <entity>

import type { Argv } from "yargs"
import { apiClient } from "@/client/api"
import { UI, formatDuration } from "@/cli/ui"
import chalk from "chalk"

export function memoryCommand(yargs: Argv): Argv {
  return yargs.command("memory <subcommand>", "Query and manage the memory system", (y) => {
    memoryQueryCommand(y)
    memoryListCommand(y)
    memoryGraphCommand(y)
    return y
  })
}

function memoryQueryCommand(yargs: Argv): void {
  yargs.command(
    "query <text>",
    "Search memory for relevant knowledge",
    (y) =>
      y
        .positional("text", { type: "string", demandOption: true })
        .option("limit", { type: "number", default: 5 })
        .option("types", {
          type: "string",
          default: "episodic,semantic",
          coerce: (v: string) => v.split(","),
        }),
    async (argv) => {
      const start = Date.now()
      UI.header(`Memory Query: ${argv.text}`)

      try {
        const result = await apiClient.queryMemory({
          query: String(argv.text),
          limit: argv.limit,
          types: (argv.types as unknown as string[]) as ("episodic" | "semantic" | "procedural")[],
        })

        if (!result.memories.length) {
          UI.step("○", "No memories found")
          return
        }

        for (const mem of result.memories) {
          console.log()
          console.log(
            `  ${chalk.cyan("▸")} ${chalk.bold(mem.type.toUpperCase())} ${chalk.dim(`[score: ${mem.importance_score?.toFixed(2) ?? "?"}]`)}`,
          )
          console.log(chalk.dim(`    ${mem.content.slice(0, 200)}...`))
          console.log(chalk.dim(`    ${mem.created_at}`))
        }

        UI.empty()
        UI.stats({ found: result.total, shown: result.memories.length, duration: formatDuration(Date.now() - start) })
      } catch (err) {
        UI.errorBox("Memory query failed", String(err))
      }
    },
  )
}

function memoryListCommand(yargs: Argv): void {
  yargs.command(
    "list",
    "List recent ingest results",
    (y) => y.option("limit", { type: "number", default: 10 }),
    async (argv) => {
      UI.header("Recent Ingests")
      try {
        const items = await apiClient.listRecent(argv.limit)
        if (!items.length) {
          UI.step("○", "No items found")
          return
        }

        for (const item of items) {
          console.log()
          console.log(`  ${chalk.cyan("▸")} ${chalk.bold(item.title)}`)
          console.log(chalk.dim(`    ${item.source_url}`))
          console.log(chalk.dim(`    ${item.summary?.slice(0, 120) ?? ""}...`))
          if (item.tags?.length) {
            console.log(`    ${item.tags.map((t) => chalk.dim(`#${t}`)).join(" ")}`)
          }
        }
        UI.empty()
        UI.stats({ items: items.length })
      } catch (err) {
        UI.errorBox("List failed", String(err))
      }
    },
  )
}

function memoryGraphCommand(yargs: Argv): void {
  yargs.command(
    "graph <entity>",
    "Show knowledge graph context for an entity",
    (y) => y.positional("entity", { type: "string", demandOption: true }),
    async (argv) => {
      UI.header(`Graph: ${argv.entity}`)
      try {
        const result = await apiClient.graphContext(String(argv.entity))

        if (!result.nodes?.length) {
          UI.step("○", "No graph data found")
          return
        }

        console.log(chalk.bold(`  Nodes (${result.nodes.length}):`))
        for (const node of result.nodes.slice(0, 20)) {
          console.log(`    ${chalk.cyan(node.name)} ${chalk.dim(`[${node.type}]`)}`)
        }

        if (result.edges?.length) {
          console.log()
          console.log(chalk.bold(`  Edges (${result.edges.length}):`))
          for (const edge of result.edges.slice(0, 15)) {
            const srcNode = result.nodes.find((n) => n.id === edge.source)
            const tgtNode = result.nodes.find((n) => n.id === edge.target)
            console.log(
              `    ${chalk.white(srcNode?.name ?? edge.source)} ${chalk.dim(edge.type)} ${chalk.white(tgtNode?.name ?? edge.target)} ${chalk.dim(`[${edge.weight.toFixed(2)}]`)}`,
            )
          }
        }
        UI.empty()
      } catch (err) {
        UI.errorBox("Graph query failed", String(err))
      }
    },
  )
}

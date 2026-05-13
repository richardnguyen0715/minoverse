// CLI Command: ingest (batch)
// Usage: autoingest ingest <url|file|stdin> [--watch]

import type { Argv } from "yargs"
import { UI, formatDuration } from "@/cli/ui"
import { apiClient } from "@/client/api"
import chalk from "chalk"
import * as fs from "fs"
import * as readline from "readline"

interface IngestArgs {
  input?: string
  mode: "quick" | "technical" | "research"
  batch: boolean
  watch: boolean
}

export function ingestCommand(yargs: Argv): Argv {
  return yargs.command(
    "ingest [input]",
    "Ingest one or more URLs from a file, stdin, or argument",
    (y) =>
      y
        .positional("input", {
          describe: "URL, file path containing URLs, or - for stdin",
          type: "string",
        })
        .option("mode", {
          alias: "m",
          choices: ["quick", "technical", "research"] as const,
          default: "quick" as const,
        })
        .option("batch", {
          describe: "Process multiple URLs from file (one per line)",
          type: "boolean",
          default: false,
        })
        .option("watch", {
          describe: "Watch a file for new URLs and ingest automatically",
          type: "boolean",
          default: false,
        }),
    async (argv) => {
      const args = argv as unknown as IngestArgs

      if (!args.input || args.input === "-") {
        // Read from stdin
        const urls = await readLines(process.stdin)
        await batchIngest(urls, args.mode)
        return
      }

      // Check if it's a file
      if (fs.existsSync(args.input)) {
        if (args.watch) {
          await watchFile(args.input, args.mode)
        } else {
          const content = fs.readFileSync(args.input, "utf-8")
          const urls = content
            .split("\n")
            .map((l) => l.trim())
            .filter((l) => l.startsWith("http"))
          await batchIngest(urls, args.mode)
        }
        return
      }

      // Treat as single URL
      const url = args.input
      if (!url.startsWith("http")) {
        UI.errorBox("Invalid input", `Not a valid URL or file: ${url}`)
        process.exit(1)
      }

      await ingestSingle(url, args.mode)
    },
  )
}

async function ingestSingle(url: string, mode: "quick" | "technical" | "research"): Promise<void> {
  const start = Date.now()
  UI.step("→", `Ingesting ${url}`)

  try {
    const result = await apiClient.ingest({ url, mode, store_memory: true, update_graph: true })
    UI.step("✓", result.title ?? url, chalk.dim(`${formatDuration(Date.now() - start)}`))
    if (result.entities?.length) {
      UI.step("", `  ${result.entities.length} entities extracted`)
    }
  } catch (err) {
    UI.step("✗", url, chalk.red(String(err)))
  }
}

async function batchIngest(urls: string[], mode: "quick" | "technical" | "research"): Promise<void> {
  UI.header(`Batch Ingest — ${urls.length} URLs`)
  let success = 0
  let failed = 0

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i]
    UI.progress(i, urls.length, url.slice(0, 50))
    try {
      await apiClient.ingest({ url, mode, store_memory: true, update_graph: true })
      success++
    } catch {
      failed++
    }
    // Rate limit
    await new Promise((r) => setTimeout(r, 500))
  }

  UI.progress(urls.length, urls.length)
  UI.empty()
  UI.stats({ total: urls.length, success, failed })
}

async function watchFile(filePath: string, mode: "quick" | "technical" | "research"): Promise<void> {
  UI.header(`Watching ${filePath}`)
  UI.step("👁", "Watching for new URLs...")

  const processedUrls = new Set<string>()

  const processFile = async () => {
    const content = fs.readFileSync(filePath, "utf-8")
    const urls = content
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.startsWith("http"))

    for (const url of urls) {
      if (!processedUrls.has(url)) {
        processedUrls.add(url)
        await ingestSingle(url, mode)
      }
    }
  }

  // Initial load
  await processFile()

  // Watch for changes
  fs.watch(filePath, { persistent: true }, async (event) => {
    if (event === "change") {
      await processFile()
    }
  })

  // Keep process alive
  await new Promise(() => {})
}

async function readLines(stream: NodeJS.ReadableStream): Promise<string[]> {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: stream })
    const lines: string[] = []
    rl.on("line", (line) => {
      const trimmed = line.trim()
      if (trimmed.startsWith("http")) lines.push(trimmed)
    })
    rl.on("close", () => resolve(lines))
  })
}

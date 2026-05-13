#!/usr/bin/env bun
// AutoIngest CLI — Main Entry Point
// Personal Autonomous Research & Knowledge Operating System

import yargs from "yargs"
import { hideBin } from "yargs/helpers"
import chalk from "chalk"
import { analyzeCommand } from "@/cli/cmd/analyze"
import { researchCommand } from "@/cli/cmd/research"
import { memoryCommand } from "@/cli/cmd/memory"
import { ingestCommand } from "@/cli/cmd/ingest"
import { apiClient } from "@/client/api"
import { getConfig } from "@/config/config"
import { UI } from "@/cli/ui"

// Load tools registry (side-effect: register all tools)
import "@/tools/index"

async function launchTUI() {
  const { render } = await import("ink")
  const { default: React } = await import("react")
  const { default: App } = await import("@/tui/App")
  render(React.createElement(App))
}

async function main() {
  const args = process.argv.slice(2)

  // No args → launch interactive TUI
  if (args.length === 0) {
    await launchTUI()
    return
  }

  const y = yargs(hideBin(process.argv))
    .scriptName("autoingest")
    .usage("$0 <command> [options]  (or just: autoingest)")
    .version("0.1.0")
    .alias("version", "V")
    .help()
    .alias("help", "h")
    .epilogue(
      chalk.dim(
        "Tip: run `autoingest` with no args for the interactive TUI agent\nDocs: https://github.com/richardnguyen0715/minoverse",
      ),
    )

  // Register commands
  analyzeCommand(y)
  researchCommand(y)
  memoryCommand(y)
  ingestCommand(y)

  // Health check command
  y.command(
    "health",
    "Check system health",
    () => {},
    async () => {
      try {
        const health = await apiClient.health()
        const icon = health.status === "ok" ? "✓" : health.status === "degraded" ? "⚠" : "✗"
        const color = health.status === "ok" ? "success" : health.status === "degraded" ? "warn" : "error"
        console.log(`${UI[color](icon)} Minoverse API: ${health.status} (v${health.version})`)

        for (const [component, status] of Object.entries(health.components ?? {})) {
          const icon = status === "ok" ? "✓" : "✗"
          const fn = status === "ok" ? UI.success : UI.error
          console.log(`  ${fn(icon)} ${component}: ${status}`)
        }
      } catch (err) {
        UI.errorBox(
          "API Unreachable",
          String(err),
          `Is the API running? Run: make start  (expected at ${getConfig().MINOVERSE_API_URL})`,
        )
        process.exit(1)
      }
    },
  )

  // Tools list command
  y.command(
    "tools",
    "List all available tools",
    () => {},
    async () => {
      const { globalRegistry } = await import("@/tools/index")
      UI.header("Available Tools")
      const tools = globalRegistry.list()
      for (const tool of tools) {
        console.log(`  ${chalk.cyan("•")} ${chalk.bold(tool.name)}`)
        console.log(`    ${chalk.dim(tool.description)}`)
        console.log()
      }
      console.log(chalk.dim(`  ${tools.length} tools registered`))
    },
  )

  y.demandCommand(1, "").exitProcess(false)
  await y.parseAsync()
}

main().catch((err) => {
  console.error(chalk.red("Fatal error:"), err)
  process.exit(1)
})


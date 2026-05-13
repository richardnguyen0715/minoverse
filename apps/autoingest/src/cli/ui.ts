// CLI UI helpers — colored output, spinners, tables

import chalk from "chalk"

export const UI = {
  // Colors
  primary: (s: string) => chalk.cyan(s),
  success: (s: string) => chalk.green(s),
  warn: (s: string) => chalk.yellow(s),
  error: (s: string) => chalk.red(s),
  dim: (s: string) => chalk.dim(s),
  bold: (s: string) => chalk.bold(s),
  url: (s: string) => chalk.blue.underline(s),

  // Symbols
  bullet: "•",
  arrow: "→",
  check: "✓",
  cross: "✗",
  dot: "·",

  // Print helpers
  println: (s: string) => process.stdout.write(s + "\n"),
  print: (s: string) => process.stdout.write(s),
  empty: () => process.stdout.write("\n"),

  // Section header
  header: (title: string) => {
    console.log()
    console.log(chalk.bold.cyan(`━━━ ${title} ━━━`))
    console.log()
  },

  // Step display
  step: (icon: string, label: string, detail?: string) => {
    const d = detail ? chalk.dim(` ${detail}`) : ""
    console.log(`  ${icon} ${chalk.white(label)}${d}`)
  },

  // Tool call display
  toolCall: (name: string, input?: unknown) => {
    console.log(`  ${chalk.magenta("⚙")} ${chalk.magenta(name)}${
      input ? chalk.dim(` (${JSON.stringify(input).slice(0, 80)}...)`) : ""
    }`)
  },

  // Tool result
  toolResult: (success: boolean, summary?: string) => {
    const icon = success ? chalk.green("✓") : chalk.red("✗")
    console.log(`    ${icon} ${chalk.dim(summary ?? (success ? "ok" : "failed"))}`)
  },

  // Final answer box
  answerBox: (content: string) => {
    console.log()
    console.log(chalk.bold.green("━━━ Result ━━━"))
    console.log()
    console.log(content)
    console.log()
  },

  // Stats line
  stats: (stats: Record<string, string | number>) => {
    const parts = Object.entries(stats)
      .map(([k, v]) => `${chalk.dim(k + ":")} ${chalk.white(String(v))}`)
      .join(chalk.dim("  │  "))
    console.log(chalk.dim("  " + parts))
  },

  // Progress indicator
  progress: (current: number, total: number, label?: string) => {
    const pct = Math.round((current / total) * 100)
    const filled = Math.round(pct / 5)
    const bar = "█".repeat(filled) + "░".repeat(20 - filled)
    process.stdout.write(`\r  [${chalk.cyan(bar)}] ${pct}% ${label ?? ""}   `)
    if (current >= total) process.stdout.write("\n")
  },

  // Error display
  errorBox: (title: string, message: string, hint?: string) => {
    console.log()
    console.log(chalk.red(`✗ ${title}`))
    console.log(chalk.dim(`  ${message}`))
    if (hint) console.log(chalk.yellow(`  Hint: ${hint}`))
    console.log()
  },

  // Entity list
  entities: (entities: Array<{ name: string; type: string }>) => {
    if (!entities.length) return
    console.log(chalk.bold("  Entities discovered:"))
    for (const e of entities) {
      console.log(`    ${chalk.dim("·")} ${chalk.white(e.name)} ${chalk.dim(`[${e.type}]`)}`)
    }
  },
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
}

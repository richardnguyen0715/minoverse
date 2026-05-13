import React from "react"
import { Box, Text } from "ink"
import type { AgentStatus, Stats } from "@/tui/types"

interface Props {
  status: AgentStatus
  stats: Stats
  width: number
}

function formatDuration(ms: number): string {
  if (ms === 0) return "—"
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function StatusBar({ status, stats, width }: Props) {
  const parts = [
    stats.steps > 0 && `steps: ${stats.steps}`,
    stats.memories > 0 && `memories: ${stats.memories}`,
    stats.entities > 0 && `entities: ${stats.entities}`,
    stats.durationMs > 0 && `last: ${formatDuration(stats.durationMs)}`,
  ].filter(Boolean) as string[]

  const info = parts.length > 0 ? parts.join("  ·  ") : "No runs yet"

  return (
    <Box borderStyle="single" borderColor="gray" width={width} paddingX={1}>
      <Text dimColor>{info}</Text>
      <Text>{"  "}</Text>
      <Text dimColor>Ctrl+C exit  ·  /help</Text>
    </Box>
  )
}

import React from "react"
import { Box, Text } from "ink"
import type { ToolEvent } from "@/tui/types"

interface Props {
  events: ToolEvent[]
  width: number
  height: number
}

const STATUS_ICON: Record<ToolEvent["status"], string> = {
  running: "⟳",
  done: "✓",
  error: "✗",
}

const STATUS_COLOR: Record<ToolEvent["status"], string> = {
  running: "yellow",
  done: "green",
  error: "red",
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function ToolPanel({ events, width, height }: Props) {
  // Show most recent events that fit
  const maxVisible = Math.max(1, Math.floor((height - 4) / 3))
  const visible = events.slice(-maxVisible)

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="magenta"
      width={width}
      height={height}
      paddingX={1}
      overflow="hidden"
    >
      <Text bold color="magenta">
        🔧 Tools
      </Text>
      <Box flexDirection="column" flexGrow={1}>
        {visible.length === 0 && (
          <Text dimColor>Awaiting tool calls…</Text>
        )}
        {visible.map((ev) => (
          <Box key={ev.id} flexDirection="column" marginBottom={1}>
            <Box>
              <Text color={STATUS_COLOR[ev.status]}>{STATUS_ICON[ev.status]} </Text>
              <Text bold>{ev.tool}</Text>
              {ev.durationMs !== undefined && (
                <Text dimColor>  {formatDuration(ev.durationMs)}</Text>
              )}
            </Box>
            {ev.preview ? (
              <Text dimColor>  {ev.preview.slice(0, width - 6)}</Text>
            ) : ev.status === "running" ? (
              <Text color="yellow">  running…</Text>
            ) : null}
          </Box>
        ))}
      </Box>
    </Box>
  )
}

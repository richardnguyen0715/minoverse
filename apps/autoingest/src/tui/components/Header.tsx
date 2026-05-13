import React from "react"
import { Box, Text } from "ink"
import type { AgentStatus } from "@/tui/types"

interface Props {
  status: AgentStatus
  model: string
  width: number
}

const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: "ready",
  thinking: "thinking…",
  running: "running tools…",
  error: "error",
}

const STATUS_COLOR: Record<AgentStatus, string> = {
  idle: "green",
  thinking: "yellow",
  running: "cyan",
  error: "red",
}

export function Header({ status, model, width }: Props) {
  const label = STATUS_LABEL[status]
  const color = STATUS_COLOR[status]
  const title = " 🧠 AutoIngest  by Minoverse "
  const right = ` ${model} · ${label} `
  const pad = Math.max(0, width - title.length - right.length - 4)

  return (
    <Box borderStyle="round" borderColor="cyan" width={width} paddingX={1}>
      <Text bold color="cyan">
        {title}
      </Text>
      <Text>{" ".repeat(pad)}</Text>
      <Text dimColor>{model} · </Text>
      <Text color={color}>{label}</Text>
    </Box>
  )
}

import React from "react"
import { Box, Text } from "ink"
import type { ChatMessage } from "@/tui/types"

interface Props {
  messages: ChatMessage[]
  currentStream: string
  width: number
  height: number
}

function wrapText(text: string, width: number): string[] {
  const lines: string[] = []
  for (const line of text.split("\n")) {
    if (line.length <= width) {
      lines.push(line)
    } else {
      // word-wrap long lines
      let remaining = line
      while (remaining.length > width) {
        const cut = remaining.lastIndexOf(" ", width)
        const splitAt = cut > 0 ? cut : width
        lines.push(remaining.slice(0, splitAt))
        remaining = remaining.slice(splitAt).trimStart()
      }
      if (remaining) lines.push(remaining)
    }
  }
  return lines
}

export function ChatPanel({ messages, currentStream, width, height }: Props) {
  const innerWidth = width - 4 // account for border + padding

  // Deduplicate by ID (guards against React StrictMode double-render)
  const unique = messages.filter((m, i, arr) => arr.findIndex((x) => x.id === m.id) === i)

  // Build rendered lines for each message and fit into height
  type RenderedMsg = { lines: string[]; role: "user" | "assistant"; id: string }
  const rendered: RenderedMsg[] = unique.map((m) => ({
    id: m.id,
    role: m.role,
    lines: wrapText(m.content, innerWidth),
  }))

  // Add streaming message if active
  if (currentStream) {
    rendered.push({
      id: "__stream__",
      role: "assistant",
      lines: wrapText(currentStream + "▌", innerWidth),
    })
  }

  // Show only the last messages that fit within height (each msg = lines + 1 spacing)
  const visible: RenderedMsg[] = []
  let linesUsed = 0
  for (let i = rendered.length - 1; i >= 0; i--) {
    const cost = rendered[i].lines.length + 1
    if (linesUsed + cost > height - 2) break
    visible.unshift(rendered[i])
    linesUsed += cost
  }

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="cyan"
      width={width}
      height={height}
      paddingX={1}
      overflow="hidden"
    >
      <Text bold color="cyan">
        💬 Chat
      </Text>
      <Box flexDirection="column" flexGrow={1}>
        {visible.length === 0 && !currentStream && (
          <Text dimColor>No messages yet. Type something below.</Text>
        )}
        {visible.map((msg) => (
          <Box key={msg.id} flexDirection="column" marginTop={0} marginBottom={1}>
            <Text bold color={msg.role === "user" ? "green" : "blue"}>
              {msg.role === "user" ? "You" : "Agent"}
            </Text>
            {msg.lines.map((line, i) => (
              <Text key={i} color={msg.role === "user" ? "white" : "gray"}>
                {line}
              </Text>
            ))}
          </Box>
        ))}
      </Box>
    </Box>
  )
}

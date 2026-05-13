import React, { useState } from "react"
import { Box, Text, useInput } from "ink"
import type { AgentStatus } from "@/tui/types"

interface Props {
  onSubmit: (text: string) => void
  status: AgentStatus
  width: number
}

export function InputBar({ onSubmit, status, width }: Props) {
  const [value, setValue] = useState("")
  const [cursor, setCursor] = useState(0)
  const disabled = status !== "idle"

  useInput(
    (input, key) => {
      if (key.return) {
        if (value.trim()) {
          onSubmit(value.trim())
          setValue("")
          setCursor(0)
        }
        return
      }

      if (key.backspace || key.delete) {
        if (cursor > 0) {
          setValue((v) => v.slice(0, cursor - 1) + v.slice(cursor))
          setCursor((c) => c - 1)
        }
        return
      }

      if (key.leftArrow) {
        setCursor((c) => Math.max(0, c - 1))
        return
      }

      if (key.rightArrow) {
        setCursor((c) => Math.min(value.length, c + 1))
        return
      }

      // Home key
      if (key.ctrl && input === "a") {
        setCursor(0)
        return
      }

      // End key
      if (key.ctrl && input === "e") {
        setCursor(value.length)
        return
      }

      // Clear line
      if (key.ctrl && input === "u") {
        setValue("")
        setCursor(0)
        return
      }

      if (!key.ctrl && !key.meta && !key.escape && input) {
        setValue((v) => v.slice(0, cursor) + input + v.slice(cursor))
        setCursor((c) => c + 1)
      }
    },
    { isActive: !disabled },
  )

  const before = value.slice(0, cursor)
  const atCursor = value[cursor] ?? " "
  const after = value.slice(cursor + 1)

  const placeholder = disabled
    ? ` ${status === "thinking" ? "Thinking…" : "Running tools…"}`
    : " Type a URL or message… (/help for commands)"

  return (
    <Box borderStyle="single" borderColor={disabled ? "gray" : "green"} width={width} paddingX={1}>
      <Text color={disabled ? "gray" : "green"}>❯ </Text>
      {disabled ? (
        <Text dimColor>{placeholder}</Text>
      ) : value.length === 0 ? (
        <>
          <Text color="green" backgroundColor="green">
            {" "}
          </Text>
          <Text dimColor>{placeholder}</Text>
        </>
      ) : (
        <>
          <Text>{before}</Text>
          <Text backgroundColor="white" color="black">
            {atCursor}
          </Text>
          <Text>{after}</Text>
        </>
      )}
    </Box>
  )
}

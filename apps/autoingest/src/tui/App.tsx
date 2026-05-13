import React, { useEffect, useState } from "react"
import { Box, useApp, useInput, useStdout } from "ink"
import { Header } from "@/tui/components/Header"
import { ChatPanel } from "@/tui/components/ChatPanel"
import { ToolPanel } from "@/tui/components/ToolPanel"
import { StatusBar } from "@/tui/components/StatusBar"
import { InputBar } from "@/tui/components/InputBar"
import { useAgent } from "@/tui/hooks/useAgent"
import { getConfig } from "@/config/config"

function useTerminalSize() {
  const { stdout } = useStdout()
  const [size, setSize] = useState({
    columns: stdout?.columns ?? 120,
    rows: stdout?.rows ?? 36,
  })
  useEffect(() => {
    if (!stdout) return
    const onResize = () => setSize({ columns: stdout.columns ?? 120, rows: stdout.rows ?? 36 })
    stdout.on("resize", onResize)
    return () => { stdout.off("resize", onResize) }
  }, [stdout])
  return size
}

export default function App() {
  const { exit } = useApp()
  const { columns, rows } = useTerminalSize()
  const { messages, toolEvents, status, currentStream, stats, submit } = useAgent()

  const config = getConfig()
  const model = `${config.DEFAULT_PROVIDER}/${config.DEFAULT_MODEL}`

  // Ctrl+C to exit (only when idle; mid-run just shows a hint)
  useInput((_input, key) => {
    if (key.ctrl && _input === "c") {
      if (status === "idle") {
        exit()
      }
      // Mid-run: ignore — let the agent finish
    }
  })

  // Layout calculation
  const toolPanelWidth = Math.max(28, Math.floor(columns * 0.32))
  const chatPanelWidth = columns - toolPanelWidth - 1 // 1 for the gap
  const headerHeight = 3
  const statusHeight = 3
  const inputHeight = 3
  const mainHeight = Math.max(6, rows - headerHeight - statusHeight - inputHeight)

  return (
    <Box flexDirection="column" width={columns}>
      {/* Header */}
      <Header status={status} model={model} width={columns} />

      {/* Main panels */}
      <Box width={columns} height={mainHeight}>
        <ChatPanel
          messages={messages}
          currentStream={currentStream}
          width={chatPanelWidth}
          height={mainHeight}
        />
        <ToolPanel events={toolEvents} width={toolPanelWidth} height={mainHeight} />
      </Box>

      {/* Status bar */}
      <StatusBar status={status} stats={stats} width={columns} />

      {/* Input */}
      <InputBar onSubmit={submit} status={status} width={columns} />
    </Box>
  )
}

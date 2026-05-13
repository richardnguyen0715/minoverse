'use client'
import { useState, useRef, useEffect } from 'react'
import { useChatbotStore } from '@/store/chatbot-store'
import type { ComposerMode, ChatMessage, TimelineStep } from '@/store/chatbot-store'
import { askCopilot } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const MODE_ACTIONS: { id: ComposerMode; icon: string; label: string }[] = [
  { id: 'default', icon: '✦', label: 'Chat' },
  { id: 'deep-research', icon: '🔬', label: 'Deep Research' },
  { id: 'use-graph', icon: '🕸️', label: 'Use Graph' },
  { id: 'web-search', icon: '🌐', label: 'Web Search' },
]

export function ChatComposer() {
  const {
    activeSessionId,
    composerMode,
    setComposerMode,
    isLoading,
    addMessage,
    setLoading,
    setError,
    setRightPanelTab,
  } = useChatbotStore()

  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [text])

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
      sources: [],
      timeline: [],
      reasoningExpanded: false,
    }
    addMessage(userMsg)
    setText('')
    setLoading(true)
    setError(null)

    const timeline: TimelineStep[] = [
      { label: 'Query received', ts: new Date().toISOString() },
    ]

    try {
      timeline.push({ label: 'Retrieving relevant sources…', ts: new Date().toISOString() })
      const result = await askCopilot(trimmed, activeSessionId)
      timeline.push({ label: 'Answer synthesized', ts: new Date().toISOString() })

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.answer,
        timestamp: new Date().toISOString(),
        sources: result.sources,
        turnId: result.turn_id,
        sessionId: result.session_id,
        timeline,
        reasoningExpanded: false,
      }
      addMessage(assistantMsg)

      // Switch to sources panel when sources are available
      if (result.sources.length > 0) {
        setRightPanelTab('sources')
      } else {
        setRightPanelTab('timeline')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      timeline.push({ label: 'Request failed', ts: new Date().toISOString() })
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="border-t border-border/50 bg-background/80 backdrop-blur-sm px-4 py-3">
      {/* Mode selector */}
      <div className="flex gap-1 mb-2">
        {MODE_ACTIONS.map((mode) => (
          <button
            key={mode.id}
            onClick={() => setComposerMode(mode.id)}
            className={cn(
              'flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium transition-colors',
              composerMode === mode.id
                ? 'bg-primary/15 text-primary border border-primary/30'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent border border-transparent'
            )}
          >
            <span>{mode.icon}</span>
            <span>{mode.label}</span>
          </button>
        ))}
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="flex gap-2 items-end">
        <div className="flex-1 relative rounded-xl border border-border/60 bg-card/60 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={composerPlaceholder(composerMode)}
            rows={1}
            disabled={isLoading}
            className="w-full resize-none bg-transparent px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 max-h-[200px] overflow-y-auto"
          />
        </div>

        <Button
          type="submit"
          disabled={isLoading || !text.trim()}
          className="shrink-0 h-10 px-4"
        >
          {isLoading ? (
            <span className="inline-block w-4 h-4 rounded-full border-2 border-primary-foreground border-t-transparent animate-spin" />
          ) : (
            '↑'
          )}
        </Button>
      </form>

      <p className="text-[10px] text-muted-foreground mt-1.5 pl-1">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}

function composerPlaceholder(mode: ComposerMode): string {
  switch (mode) {
    case 'deep-research':
      return 'Ask for deep research across your vault…'
    case 'use-graph':
      return 'Ask using knowledge graph traversal…'
    case 'web-search':
      return 'Ask with web search augmentation…'
    default:
      return 'Ask your knowledge vault anything… (Enter to send)'
  }
}

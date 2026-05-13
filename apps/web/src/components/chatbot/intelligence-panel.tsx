'use client'
import { useChatbotStore } from '@/store/chatbot-store'
import type { RightPanelTab } from '@/store/chatbot-store'
import { cn } from '@/lib/utils'

const TABS: { id: RightPanelTab; label: string; icon: string }[] = [
  { id: 'sources', label: 'Sources', icon: '📚' },
  { id: 'timeline', label: 'Timeline', icon: '⏱' },
  { id: 'memory', label: 'Memory', icon: '💡' },
]

export function IntelligencePanel() {
  const { rightPanelTab, setRightPanelTab, messages } = useChatbotStore()

  const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant')

  return (
    <aside className="flex flex-col w-64 flex-shrink-0 border-l border-border/50 bg-card/20 overflow-hidden">
      {/* Tab bar */}
      <div className="flex border-b border-border/50">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setRightPanelTab(tab.id)}
            className={cn(
              'flex-1 flex items-center justify-center gap-1 py-2 text-[11px] font-medium transition-colors',
              rightPanelTab === tab.id
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Panel content */}
      <div className="flex-1 overflow-y-auto p-3">
        {rightPanelTab === 'sources' && <SourcesContent message={lastAssistant} />}
        {rightPanelTab === 'timeline' && <TimelineContent message={lastAssistant} />}
        {rightPanelTab === 'memory' && <MemoryContent />}
      </div>
    </aside>
  )
}

function SourcesContent({
  message,
}: {
  message: ReturnType<typeof useChatbotStore.getState>['messages'][number] | undefined
}) {
  if (!message || message.sources.length === 0) {
    return (
      <EmptyState
        icon="📄"
        text="Sources will appear here after you send a message."
      />
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
        Retrieved ({message.sources.length})
      </p>
      {message.sources.map((src, i) => (
        <div
          key={src.resource_id}
          className="rounded-lg border border-border/40 bg-background/50 px-3 py-2.5"
        >
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="text-xs font-medium text-foreground leading-tight line-clamp-2">
              {src.title}
            </p>
            <span className="text-[10px] text-muted-foreground shrink-0 mt-0.5">#{i + 1}</span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-3">
            {src.excerpt}
          </p>
        </div>
      ))}
    </div>
  )
}

function TimelineContent({
  message,
}: {
  message: ReturnType<typeof useChatbotStore.getState>['messages'][number] | undefined
}) {
  if (!message || message.timeline.length === 0) {
    return (
      <EmptyState
        icon="⏱"
        text="Processing timeline will appear here after you send a message."
      />
    )
  }

  return (
    <div className="flex flex-col gap-0">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
        Processing steps
      </p>
      {message.timeline.map((step, i) => (
        <div key={i} className="flex gap-2.5 pb-3">
          <div className="flex flex-col items-center">
            <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1 shrink-0" />
            {i < message.timeline.length - 1 && (
              <div className="w-px flex-1 bg-border/50 mt-1" />
            )}
          </div>
          <div className="flex-1 pb-1">
            <p className="text-xs text-foreground leading-snug">{step.label}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {formatTime(step.ts)}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

function MemoryContent() {
  return (
    <EmptyState
      icon="💡"
      text="Long-term memories extracted from your sessions will appear here."
    />
  )
}

function EmptyState({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[120px] gap-2 text-center px-2">
      <span className="text-2xl">{icon}</span>
      <p className="text-[11px] text-muted-foreground leading-relaxed">{text}</p>
    </div>
  )
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

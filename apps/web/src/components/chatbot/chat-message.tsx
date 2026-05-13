'use client'
import { useChatbotStore } from '@/store/chatbot-store'
import type { ChatMessage } from '@/store/chatbot-store'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ChatMessageProps {
  message: ChatMessage
}

export function ChatMessageItem({ message }: ChatMessageProps) {
  const { toggleReasoning } = useChatbotStore()
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5">
          <p className="text-sm text-primary-foreground leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
          <p className="text-[10px] text-primary-foreground/60 mt-1 text-right">
            {formatTime(message.timestamp)}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] flex flex-col gap-2">
        {/* Avatar + label */}
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-semibold text-primary">⬡ minoverse</span>
          {message.turnId && (
            <Badge variant="outline" className="text-[10px] h-4">
              turn {message.turnId.slice(0, 6)}
            </Badge>
          )}
        </div>

        {/* Answer layer */}
        <div className="rounded-2xl rounded-tl-sm border border-border/50 bg-card/60 px-4 py-3">
          <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
            {message.content}
          </p>
        </div>

        {/* Retrieval info + reasoning toggle */}
        {message.sources.length > 0 && (
          <div className="flex items-center gap-3 px-1">
            <span className="text-[10px] text-muted-foreground">
              📚 {message.sources.length} source{message.sources.length !== 1 ? 's' : ''} retrieved
            </span>
            <button
              onClick={() => toggleReasoning(message.id)}
              className="text-[10px] text-muted-foreground hover:text-foreground transition-colors underline-offset-2 hover:underline"
            >
              {message.reasoningExpanded ? '▲ hide details' : '▼ show sources'}
            </button>
          </div>
        )}

        {/* Sources layer (expanded) */}
        {message.reasoningExpanded && message.sources.length > 0 && (
          <div className="flex flex-col gap-1.5 px-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Retrieved Sources
            </p>
            {message.sources.map((src) => (
              <div
                key={src.resource_id}
                className="rounded-lg border border-border/40 bg-background/50 px-3 py-2"
              >
                <p className="text-xs font-medium text-foreground truncate">{src.title}</p>
                <p className="mt-0.5 text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
                  {src.excerpt}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Confidence indicator */}
        {message.confidence !== undefined && (
          <ConfidenceBar confidence={message.confidence} />
        )}

        {/* Timestamp */}
        <p className="text-[10px] text-muted-foreground px-1">{formatTime(message.timestamp)}</p>
      </div>
    </div>
  )
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const color =
    pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="flex items-center gap-2 px-1">
      <span className="text-[10px] text-muted-foreground">Confidence</span>
      <div className="flex-1 max-w-[120px] h-1.5 rounded-full bg-border overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[10px] text-muted-foreground">{pct}%</span>
    </div>
  )
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

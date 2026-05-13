'use client'
import { cn } from '@/lib/utils'
import { useChatbotStore } from '@/store/chatbot-store'
import type { ChatMessage, ChatSource } from '@/store/chatbot-store'
import type { MemorySession, MemoryTurn } from '@/lib/types'
import { createSession, getSession, deleteSession } from '@/lib/api'
import { useState } from 'react'
import { Button } from '@/components/ui/button'

interface ChatSidebarProps {
  className?: string
}

export function ChatSidebar({ className }: ChatSidebarProps) {
  const { sessions, activeSessionId, setActiveSession, addSession, removeSession, setMessages, setError } = useChatbotStore()
  const [creating, setCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!newTitle.trim()) return
    setCreating(true)
    try {
      const session = await createSession(newTitle.trim())
      addSession(session)
      useChatbotStore.getState().setActiveSession(session.id)
      useChatbotStore.getState().setMessages([])
      setNewTitle('')
      setShowForm(false)
    } catch {
      setError('Failed to create session')
    } finally {
      setCreating(false)
    }
  }

  async function handleSelectSession(id: string) {
    if (pendingDeleteId) { setPendingDeleteId(null); return }
    if (id === activeSessionId) return
    setActiveSession(id)
    try {
      const detail = await getSession(id)
      const msgs: ChatMessage[] = detail.turns.map((t) => turnToMessage(t))
      setMessages(msgs)
    } catch {
      setError('Failed to load session history')
      useChatbotStore.getState().setSessionLoading(false)
    }
  }

  function handleDeleteClick(id: string) {
    setPendingDeleteId(id === pendingDeleteId ? null : id)
  }

  async function handleDeleteConfirm(id: string) {
    setPendingDeleteId(null)
    try {
      await deleteSession(id)
      removeSession(id)
    } catch {
      setError('Failed to delete session')
    }
  }

  return (
    <aside
      className={cn(
        'flex flex-col w-56 flex-shrink-0 border-r border-border/50 bg-card/30 overflow-hidden',
        className
      )}
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-border/50">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Sessions
        </span>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          title="New session"
        >
          +
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="flex gap-1.5 px-3 py-2 border-b border-border/50">
          <input
            autoFocus
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Session name…"
            className="flex-1 min-w-0 text-xs rounded border border-border bg-background px-2 py-1 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Button type="submit" size="sm" variant="outline" disabled={creating || !newTitle.trim()}>
            ✓
          </Button>
        </form>
      )}

      <div className="flex-1 overflow-y-auto">
        <button
          onClick={() => {
            setPendingDeleteId(null)
            setActiveSession(undefined)
            setMessages([])
          }}
          className={cn(
            'w-full text-left px-3 py-2 text-xs transition-colors hover:bg-accent',
            activeSessionId === undefined
              ? 'bg-primary/10 text-primary font-medium'
              : 'text-muted-foreground'
          )}
        >
          <span className="block truncate">⚡ One-off (no session)</span>
        </button>

        {sessions.map((s) => (
          <SessionCard
            key={s.id}
            session={s}
            active={s.id === activeSessionId}
            pendingDelete={pendingDeleteId === s.id}
            onClick={() => handleSelectSession(s.id)}
            onDeleteClick={() => handleDeleteClick(s.id)}
            onDeleteConfirm={() => handleDeleteConfirm(s.id)}
            onDeleteCancel={() => setPendingDeleteId(null)}
          />
        ))}

        {sessions.length === 0 && (
          <p className="px-3 py-4 text-[11px] text-muted-foreground/60 text-center">
            No sessions yet.
            <br />
            Click + to create one.
          </p>
        )}
      </div>
    </aside>
  )
}

function SessionCard({
  session,
  active,
  pendingDelete,
  onClick,
  onDeleteClick,
  onDeleteConfirm,
  onDeleteCancel,
}: {
  session: MemorySession
  active: boolean
  pendingDelete: boolean
  onClick: () => void
  onDeleteClick: () => void
  onDeleteConfirm: () => void
  onDeleteCancel: () => void
}) {
  const ago = formatAgo(new Date(session.updated_at))

  if (pendingDelete) {
    return (
      <div className="flex flex-col border-b border-border/30 bg-destructive/10 px-3 py-2">
        <p className="text-xs text-destructive font-medium truncate mb-1.5">{session.title}</p>
        <p className="text-[10px] text-muted-foreground mb-2">Delete this session?</p>
        <div className="flex gap-1.5">
          <button
            onClick={onDeleteConfirm}
            className="flex-1 text-[11px] font-medium bg-destructive text-destructive-foreground rounded px-2 py-1 hover:bg-destructive/90 transition-colors"
          >
            Delete
          </button>
          <button
            onClick={onDeleteCancel}
            className="flex-1 text-[11px] font-medium border border-border rounded px-2 py-1 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'flex items-stretch border-b border-border/30 transition-colors hover:bg-accent group',
        active ? 'bg-primary/10' : ''
      )}
    >
      <div
        role="button"
        tabIndex={0}
        onClick={onClick}
        onKeyDown={(e) => e.key === 'Enter' && onClick()}
        className="flex-1 min-w-0 px-3 py-2.5 cursor-pointer"
      >
        <p className={cn('text-xs truncate font-medium', active ? 'text-primary' : 'text-foreground')}>
          {session.title}
        </p>
        <p className="text-[10px] text-muted-foreground mt-0.5">{ago}</p>
      </div>

      <button
        onClick={onDeleteClick}
        title="Delete session"
        className="px-2.5 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all text-xs shrink-0"
      >
        ✕
      </button>
    </div>
  )
}

function turnToMessage(turn: MemoryTurn): ChatMessage {
  return {
    id: turn.id,
    role: turn.role as 'user' | 'assistant',
    content: turn.content,
    timestamp: turn.created_at,
    sources: (turn.sources ?? []) as ChatSource[],
    timeline: [],
    reasoningExpanded: false,
  }
}

function formatAgo(date: Date): string {
  const diff = Date.now() - date.getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

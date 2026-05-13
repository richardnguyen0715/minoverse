'use client'
import { useEffect, useState } from 'react'
import { listEpisodicMemories, listSemanticMemories } from '@/lib/api'
import type { EpisodicMemory, SemanticMemory } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

type Tab = 'episodes' | 'semantic'

export function MemoryBrowser() {
  const [tab, setTab] = useState<Tab>('episodes')
  const [episodes, setEpisodes] = useState<EpisodicMemory[]>([])
  const [semantics, setSemantics] = useState<SemanticMemory[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([listEpisodicMemories(), listSemanticMemories()])
      .then(([eps, sems]) => {
        setEpisodes(eps)
        setSemantics(sems)
      })
      .catch(() => {
        setEpisodes([])
        setSemantics([])
      })
      .finally(() => setLoading(false))
  }, [])

  function toggleExpand(id: string) {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Tabs */}
      <div className="flex gap-1 border-b border-border/50 pb-0">
        {(['episodes', 'semantic'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={[
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              tab === t
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            ].join(' ')}
          >
            {t === 'episodes' ? '📼 Episodes' : '🔮 Semantic'}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      ) : tab === 'episodes' ? (
        <EpisodeList items={episodes} expandedId={expandedId} onToggle={toggleExpand} formatDate={formatDate} />
      ) : (
        <SemanticList items={semantics} expandedId={expandedId} onToggle={toggleExpand} formatDate={formatDate} />
      )}
    </div>
  )
}

interface EpisodeListProps {
  items: EpisodicMemory[]
  expandedId: string | null
  onToggle: (id: string) => void
  formatDate: (iso: string) => string
}

function EpisodeList({ items, expandedId, onToggle, formatDate }: EpisodeListProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground">
        <span className="text-3xl">📼</span>
        <p className="text-sm">No episodic memories yet. Distill a Copilot session to create one.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((ep) => (
        <button
          key={ep.id}
          onClick={() => onToggle(ep.id)}
          className="w-full text-left rounded-xl border border-border/40 bg-card/50 px-4 py-3 hover:border-primary/30 hover:bg-card/80 transition-colors"
        >
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-foreground">{ep.title}</p>
            <Badge variant="secondary" className="text-[10px] flex-shrink-0">
              {formatDate(ep.created_at)}
            </Badge>
          </div>
          <p className={['mt-1 text-xs text-muted-foreground leading-relaxed', expandedId === ep.id ? '' : 'line-clamp-2'].join(' ')}>
            {ep.content}
          </p>
          {ep.resource_ids && ep.resource_ids.length > 0 && expandedId === ep.id && (
            <p className="mt-2 text-[10px] text-muted-foreground/60">
              {ep.resource_ids.length} linked resource{ep.resource_ids.length !== 1 ? 's' : ''}
            </p>
          )}
        </button>
      ))}
    </div>
  )
}

interface SemanticListProps {
  items: SemanticMemory[]
  expandedId: string | null
  onToggle: (id: string) => void
  formatDate: (iso: string) => string
}

function SemanticList({ items, expandedId, onToggle, formatDate }: SemanticListProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground">
        <span className="text-3xl">🔮</span>
        <p className="text-sm">No semantic memories yet. Extract them from resources.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((sem) => (
        <button
          key={sem.id}
          onClick={() => onToggle(sem.id)}
          className="w-full text-left rounded-xl border border-border/40 bg-card/50 px-4 py-3 hover:border-primary/30 hover:bg-card/80 transition-colors"
        >
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-foreground">{sem.concept}</p>
            <Badge variant="secondary" className="text-[10px] flex-shrink-0">
              {formatDate(sem.created_at)}
            </Badge>
          </div>
          <p className={['mt-1 text-xs text-muted-foreground leading-relaxed', expandedId === sem.id ? '' : 'line-clamp-2'].join(' ')}>
            {sem.content}
          </p>
        </button>
      ))}
    </div>
  )
}

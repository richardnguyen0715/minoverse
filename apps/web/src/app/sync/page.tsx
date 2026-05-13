'use client'
import { useEffect, useState, useCallback } from 'react'
import { listSyncEvents, replaySyncEvents } from '@/lib/api'
import type { SyncEvent } from '@/lib/types'
import { SyncStatus } from '@/components/sync'
import { cn } from '@/lib/utils'

const EVENT_TYPES = ['all', 'resource.created', 'resource.updated', 'resource.deleted', 'enrichment.completed']
const PAGE_SIZE = 20

function eventTypeBadge(eventType: string) {
  const base = 'inline-block px-2 py-0.5 rounded text-[10px] font-semibold'
  switch (eventType) {
    case 'resource.created': return cn(base, 'bg-green-500/20 text-green-400')
    case 'resource.updated': return cn(base, 'bg-blue-500/20 text-blue-400')
    case 'resource.deleted': return cn(base, 'bg-red-500/20 text-red-400')
    case 'enrichment.completed': return cn(base, 'bg-purple-500/20 text-purple-400')
    default: return cn(base, 'bg-muted text-muted-foreground')
  }
}

function formatTs(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

export default function SyncPage() {
  const [events, setEvents] = useState<SyncEvent[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [replaying, setReplaying] = useState(false)
  const [replayMsg, setReplayMsg] = useState<string | null>(null)

  const load = useCallback(async (eventType: string, off: number) => {
    setLoading(true)
    setError(false)
    try {
      const page = await listSyncEvents({
        event_type: eventType === 'all' ? undefined : eventType,
        limit: PAGE_SIZE,
        offset: off,
      })
      setEvents(page.items)
      setTotal(page.total)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setOffset(0)
    load(filter, 0)
  }, [filter, load])

  async function handleReplay() {
    setReplaying(true)
    setReplayMsg(null)
    try {
      const since = new Date(Date.now() - 7 * 86_400_000).toISOString()
      const replayed = await replaySyncEvents({ since })
      setReplayMsg(`✅ Replayed ${replayed.length} event${replayed.length !== 1 ? 's' : ''}`)
      load(filter, offset)
    } catch {
      setReplayMsg('❌ Replay failed')
    } finally {
      setReplaying(false)
    }
  }

  const hasPrev = offset > 0
  const hasNext = offset + PAGE_SIZE < total

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">🔄 Sync Events</h1>
          <p className="text-muted-foreground mt-1">Distributed event log across devices</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <SyncStatus />
          <button
            onClick={handleReplay}
            disabled={replaying}
            className="px-3 py-1.5 text-xs rounded border border-border/60 bg-card/50 hover:bg-card/80 transition-colors disabled:opacity-50"
          >
            {replaying ? 'Replaying…' : '⏪ Replay All Pending'}
          </button>
        </div>
      </div>

      {replayMsg && (
        <div className="mb-4 px-3 py-2 rounded border border-border/40 bg-card/50 text-xs text-muted-foreground">
          {replayMsg}
        </div>
      )}

      {/* Filter */}
      <div className="mb-4 flex items-center gap-2">
        <label className="text-xs text-muted-foreground">Event type:</label>
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="text-xs bg-card border border-border/60 rounded px-2 py-1 text-foreground focus:outline-none"
        >
          {EVENT_TYPES.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border/40 overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border/40 bg-card/60">
              <th className="text-left px-4 py-2.5 text-muted-foreground font-semibold">Timestamp</th>
              <th className="text-left px-4 py-2.5 text-muted-foreground font-semibold">Event Type</th>
              <th className="text-left px-4 py-2.5 text-muted-foreground font-semibold">Resource Path</th>
              <th className="text-left px-4 py-2.5 text-muted-foreground font-semibold">Applied</th>
              <th className="text-left px-4 py-2.5 text-muted-foreground font-semibold">Device</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">
                  Loading…
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-destructive">
                  Failed to load sync events.
                </td>
              </tr>
            ) : events.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">
                  No sync events found.
                </td>
              </tr>
            ) : (
              events.map((ev, i) => (
                <tr
                  key={ev.id}
                  className={cn(
                    'border-b border-border/20 transition-colors hover:bg-card/50',
                    i % 2 === 0 ? 'bg-transparent' : 'bg-card/20',
                  )}
                >
                  <td className="px-4 py-2.5 text-muted-foreground tabular-nums whitespace-nowrap">
                    {formatTs(ev.created_at)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={eventTypeBadge(ev.event_type)}>{ev.event_type}</span>
                  </td>
                  <td className="px-4 py-2.5 text-foreground/80 font-mono max-w-xs truncate">
                    {ev.resource_path ?? <span className="text-muted-foreground/40">—</span>}
                  </td>
                  <td className="px-4 py-2.5">
                    {ev.applied ? '✅' : '⏳'}
                  </td>
                  <td className="px-4 py-2.5 text-muted-foreground font-mono">
                    {ev.device_id ?? '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
        <span>{total === 0 ? 'No results' : `${offset + 1}–${Math.min(offset + PAGE_SIZE, total)} of ${total}`}</span>
        <div className="flex gap-2">
          <button
            onClick={() => { const o = Math.max(0, offset - PAGE_SIZE); setOffset(o); load(filter, o) }}
            disabled={!hasPrev || loading}
            className="px-3 py-1 rounded border border-border/60 bg-card/40 hover:bg-card/70 transition-colors disabled:opacity-40"
          >
            ← Prev
          </button>
          <button
            onClick={() => { const o = offset + PAGE_SIZE; setOffset(o); load(filter, o) }}
            disabled={!hasNext || loading}
            className="px-3 py-1 rounded border border-border/60 bg-card/40 hover:bg-card/70 transition-colors disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  )
}

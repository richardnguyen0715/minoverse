'use client'
import { useEffect, useState } from 'react'
import { listSyncEvents } from '@/lib/api'
import type { SyncEvent } from '@/lib/types'

export function SyncStatus() {
  const [pending, setPending] = useState<number>(0)
  const [lastEvent, setLastEvent] = useState<SyncEvent | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let mounted = true
    const check = async () => {
      try {
        const page = await listSyncEvents({ applied: false, limit: 1 })
        if (!mounted) return
        setPending(page.total)
        if (page.items[0]) setLastEvent(page.items[0])
        setError(false)
      } catch {
        if (mounted) setError(true)
      }
    }
    check()
    const interval = setInterval(check, 30_000)
    return () => { mounted = false; clearInterval(interval) }
  }, [])

  if (error) return <span className="text-xs text-destructive">🔴 Sync error</span>
  if (pending === 0) return <span className="text-xs text-muted-foreground">🟢 Synced</span>
  return (
    <span className="text-xs text-yellow-600">
      🟡 {pending} pending
      {lastEvent && (
        <span className="ml-1 text-muted-foreground">
          — last: {lastEvent.event_type}
        </span>
      )}
    </span>
  )
}

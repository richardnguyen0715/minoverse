'use client'
import { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { listNotes } from '@/lib/api'
import type { Note } from '@/lib/types'
import { formatDate, cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import Link from 'next/link'

const NOTE_TYPES = ['daily_note', 'note', 'concept', 'paper']

function NotesContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const selectedType = searchParams.get('type')

  const [notes, setNotes] = useState<Note[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listNotes(selectedType ? { note_type: selectedType } : undefined)
      .then(setNotes)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedType])

  const setType = useCallback((type: string | null) => {
    const params = new URLSearchParams(searchParams.toString())
    if (type) params.set('type', type)
    else params.delete('type')
    router.push(`/notes?${params.toString()}`)
  }, [router, searchParams])

  const filtered = notes.filter((n) =>
    !query || n.title?.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-border/50 flex items-center gap-3 flex-wrap bg-background/50">
        <Input
          placeholder="Filter notes..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-64 h-8 text-sm"
        />
        <div className="flex gap-1 flex-wrap">
          <button
            onClick={() => setType(null)}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${!selectedType ? 'bg-primary text-primary-foreground' : 'bg-accent hover:bg-accent/80 text-muted-foreground'}`}
          >
            All
          </button>
          {NOTE_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setType(selectedType === t ? null : t)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${selectedType === t ? 'bg-primary text-primary-foreground' : 'bg-accent hover:bg-accent/80 text-muted-foreground'}`}
            >
              {t.replace('_', ' ')}
            </button>
          ))}
        </div>
        <span className="text-xs text-muted-foreground ml-auto">{filtered.length} notes</span>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {loading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-16 rounded-lg bg-accent/20 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-muted-foreground gap-2">
            <span className="text-3xl">📭</span>
            <p className="text-sm">No notes found</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filtered.map((note) => (
              <Link key={note.id} href={`/notes/${note.id}`} className="block">
                <div className="p-3 border border-border/50 rounded-lg bg-card hover:bg-accent/30 transition-colors">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span>{note.note_type === 'daily_note' ? '📅' : '📝'}</span>
                      <span className="font-medium text-sm truncate">{note.title ?? 'Untitled'}</span>
                    </div>
                    <span className="text-xs text-muted-foreground flex-shrink-0">{formatDate(note.updated_at)}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={cn('text-xs px-1.5 py-0.5 rounded bg-accent text-muted-foreground')}>
                      {note.note_type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function NotesPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-48 text-muted-foreground"><p className="text-sm">Loading...</p></div>}>
      <NotesContent />
    </Suspense>
  )
}

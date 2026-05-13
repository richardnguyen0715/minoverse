'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { getNote, getNoteBacklinks } from '@/lib/api'
import type { Note, WikiLink } from '@/lib/types'
import { formatDate, cn } from '@/lib/utils'
import Link from 'next/link'

export default function NotePage() {
  const { id } = useParams<{ id: string }>()
  const [note, setNote] = useState<Note | null>(null)
  const [backlinks, setBacklinks] = useState<WikiLink[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      getNote(id),
      getNoteBacklinks(id).catch(() => [] as WikiLink[]),
    ])
      .then(([n, bl]) => {
        setNote(n)
        setBacklinks(bl)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Loading...</p>
        </div>
      </div>
    )
  }

  if (!note) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p>Note not found</p>
      </div>
    )
  }

  const frontmatterEntries = Object.entries(note.frontmatter).filter(([, v]) => v !== null && v !== undefined)

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <span>{note.note_type === 'daily_note' ? '📅' : '📝'}</span>
          <span className={cn('text-xs px-1.5 py-0.5 rounded bg-accent text-muted-foreground')}>
            {note.note_type.replace('_', ' ')}
          </span>
        </div>
        <h1 className="text-2xl font-bold mb-2">{note.title ?? 'Untitled'}</h1>
        <div className="text-xs text-muted-foreground">
          Updated {formatDate(note.updated_at)} · Created {formatDate(note.created_at)}
        </div>
      </div>

      {frontmatterEntries.length > 0 && (
        <div className="mb-6 p-4 rounded-lg bg-card border border-border/50">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Frontmatter</h3>
          <div className="grid grid-cols-2 gap-2">
            {frontmatterEntries.map(([key, value]) => (
              <div key={key} className="text-xs">
                <span className="text-muted-foreground">{key}: </span>
                <span className="text-foreground/80">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {backlinks.length > 0 && (
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Referenced by ({backlinks.length})
          </h3>
          <div className="flex flex-col gap-2">
            {backlinks.map((link) => (
              <Link key={link.id} href={`/notes/${link.source_note_id}`} className="block">
                <div className="p-2 rounded border border-border/30 bg-card/30 hover:bg-accent/30 transition-colors text-xs">
                  📝 {link.anchor_text ?? link.target_raw}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      <div className="pt-4 border-t border-border/30 text-xs text-muted-foreground">
        ID: {note.id}
      </div>
    </div>
  )
}

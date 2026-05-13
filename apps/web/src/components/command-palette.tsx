'use client'
import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { listResources } from '@/lib/api'
import type { Resource } from '@/lib/types'
import { resourceTypeEmoji, resourceTypeLabel, cn } from '@/lib/utils'

interface CommandPaletteProps {
  onClose: () => void
}

export function CommandPalette({ onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Resource[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }
    setLoading(true)
    const timer = setTimeout(async () => {
      try {
        const all = await listResources()
        const q = query.toLowerCase()
        const filtered = all.filter(
          (r) =>
            r.title?.toLowerCase().includes(q) ||
            r.author?.toLowerCase().includes(q) ||
            r.resource_type.includes(q)
        ).slice(0, 8)
        setResults(filtered)
        setSelectedIndex(0)
      } finally {
        setLoading(false)
      }
    }, 200)
    return () => clearTimeout(timer)
  }, [query])

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      navigate(results[selectedIndex])
    }
  }

  function navigate(resource: Resource) {
    router.push(`/resources/${resource.id}`)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-xl bg-card border border-border rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <span className="text-muted-foreground">🔍</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search resources, notes, concepts..."
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          {loading && <span className="text-xs text-muted-foreground animate-pulse">...</span>}
        </div>
        {results.length > 0 && (
          <ul className="max-h-80 overflow-y-auto py-1">
            {results.map((r, i) => (
              <li key={r.id}>
                <button
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
                    i === selectedIndex ? 'bg-accent' : 'hover:bg-accent/50'
                  )}
                  onClick={() => navigate(r)}
                >
                  <span className="text-base">{resourceTypeEmoji(r.resource_type)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{r.title ?? 'Untitled'}</p>
                    <p className="text-xs text-muted-foreground">{resourceTypeLabel(r.resource_type)}{r.author ? ` · ${r.author}` : ''}</p>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
        {!loading && query && results.length === 0 && (
          <div className="px-4 py-6 text-center text-sm text-muted-foreground">
            No results for &ldquo;{query}&rdquo;
          </div>
        )}
        {!query && (
          <div className="px-4 py-4 text-xs text-muted-foreground">
            <p>Type to search · <kbd className="px-1 py-0.5 bg-muted rounded">↑↓</kbd> navigate · <kbd className="px-1 py-0.5 bg-muted rounded">↵</kbd> open · <kbd className="px-1 py-0.5 bg-muted rounded">Esc</kbd> close</p>
          </div>
        )}
      </div>
    </div>
  )
}

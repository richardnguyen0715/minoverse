'use client'
import { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { listResources } from '@/lib/api'
import type { Resource, ResourceType } from '@/lib/types'
import { ResourceCard } from '@/components/knowledge/resource-card'
import { resourceTypeLabel } from '@/lib/utils'
import { Input } from '@/components/ui/input'

const RESOURCE_TYPES: ResourceType[] = ['paper', 'note', 'concept', 'daily_note', 'github_repo', 'article', 'youtube_video', 'documentation']

function ResourcesContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const selectedType = (searchParams.get('type') as ResourceType | null)

  const [resources, setResources] = useState<Resource[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listResources(selectedType ? { resource_type: selectedType } : undefined)
      .then(setResources)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedType])

  const setType = useCallback((type: ResourceType | null) => {
    const params = new URLSearchParams(searchParams.toString())
    if (type) params.set('type', type)
    else params.delete('type')
    router.push(`/resources?${params.toString()}`)
  }, [router, searchParams])

  const filtered = resources.filter((r) =>
    !query || r.title?.toLowerCase().includes(query.toLowerCase()) || r.author?.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="flex flex-col gap-0 h-full">
      <div className="px-4 py-3 border-b border-border/50 flex items-center gap-3 flex-wrap bg-background/50">
        <Input
          placeholder="Filter resources..."
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
          {RESOURCE_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setType(selectedType === t ? null : t)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${selectedType === t ? 'bg-primary text-primary-foreground' : 'bg-accent hover:bg-accent/80 text-muted-foreground'}`}
            >
              {resourceTypeLabel(t)}
            </button>
          ))}
        </div>
        <span className="text-xs text-muted-foreground ml-auto">{filtered.length} resources</span>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-24 rounded-lg bg-accent/20 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-muted-foreground gap-2">
            <span className="text-3xl">📭</span>
            <p className="text-sm">No resources found</p>
            {selectedType && <p className="text-xs">Try removing the type filter</p>}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map((r) => (
              <ResourceCard key={r.id} resource={r} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ResourcesPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-48 text-muted-foreground"><p className="text-sm">Loading...</p></div>}>
      <ResourcesContent />
    </Suspense>
  )
}

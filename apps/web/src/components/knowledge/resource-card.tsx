import Link from 'next/link'
import type { Resource } from '@/lib/types'
import { resourceTypeLabel, resourceTypeColor, resourceTypeEmoji, formatDate, cn } from '@/lib/utils'

interface ResourceCardProps {
  resource: Resource
}

export function ResourceCard({ resource }: ResourceCardProps) {
  const tags = (resource.extra_metadata?.aliases ?? []).slice(0, 3)
  const wordCount = resource.extra_metadata?.word_count

  return (
    <Link href={`/resources/${resource.id}`} className="block">
      <div className="p-4 border border-border/50 rounded-lg bg-card hover:bg-accent/30 transition-colors group">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-lg flex-shrink-0">{resourceTypeEmoji(resource.resource_type)}</span>
            <h3 className="font-medium text-sm truncate group-hover:text-primary transition-colors">
              {resource.title ?? 'Untitled'}
            </h3>
          </div>
          <span className={cn('text-xs px-2 py-0.5 rounded-full flex-shrink-0 font-medium', resourceTypeColor(resource.resource_type))}>
            {resourceTypeLabel(resource.resource_type)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
          {resource.author && <span>{resource.author}</span>}
          {wordCount && <span>· {wordCount.toLocaleString()} words</span>}
          <span>· {formatDate(resource.updated_at)}</span>
        </div>
        {resource.url && (
          <p className="text-xs text-primary/60 truncate mt-1">{resource.url}</p>
        )}
        {tags.length > 0 && (
          <div className="flex gap-1 mt-2 flex-wrap">
            {tags.map((tag) => (
              <span key={tag} className="text-xs border border-border/50 px-1.5 py-0.5 rounded text-muted-foreground">{tag}</span>
            ))}
          </div>
        )}
      </div>
    </Link>
  )
}

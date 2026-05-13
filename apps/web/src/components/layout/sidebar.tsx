'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useKnowledgeStore } from '@/store/knowledge-store'
import { resourceTypeEmoji, resourceTypeLabel, cn } from '@/lib/utils'
import type { ResourceType } from '@/lib/types'

const NAV_TYPES: ResourceType[] = ['paper', 'note', 'concept', 'daily_note', 'github_repo', 'article', 'youtube_video', 'documentation']

interface SidebarProps {
  collapsed: boolean
}

export function Sidebar({ collapsed }: SidebarProps) {
  const pathname = usePathname()
  const { recentResources } = useKnowledgeStore()

  return (
    <aside className={cn(
      'flex flex-col border-r border-border/50 bg-card/30 flex-shrink-0 transition-all duration-200 overflow-hidden',
      collapsed ? 'w-0' : 'w-56'
    )}>
      <div className="p-3 flex flex-col gap-4 overflow-y-auto flex-1">
        <nav className="flex flex-col gap-0.5">
          <SidebarLink href="/" active={pathname === '/'} label="🏠 Home" />
          <SidebarLink href="/resources" active={pathname.startsWith('/resources')} label="📂 All Resources" />
          <SidebarLink href="/notes" active={pathname.startsWith('/notes')} label="📝 All Notes" />
          <SidebarLink href="/graph" active={pathname.startsWith('/graph')} label="🕸️ Knowledge Graph" />
          <SidebarLink href="/chatbot" active={pathname.startsWith('/chatbot')} label="💬 Chatbot" />
          <SidebarLink href="/memory" active={pathname.startsWith('/memory')} label="💡 Memory" />
          <SidebarLink href="/sync" active={pathname.startsWith('/sync')} label="🔄 Sync" />
        </nav>

        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1 px-2">Library</p>
          <nav className="flex flex-col gap-0.5">
            {NAV_TYPES.map((type) => (
              <SidebarLink
                key={type}
                href={`/resources?type=${type}`}
                active={false}
                label={`${resourceTypeEmoji(type)} ${resourceTypeLabel(type)}s`}
              />
            ))}
          </nav>
        </div>

        {recentResources.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1 px-2">Recent</p>
            <nav className="flex flex-col gap-0.5">
              {recentResources.map((r) => (
                <SidebarLink
                  key={r.id}
                  href={`/resources/${r.id}`}
                  active={pathname === `/resources/${r.id}`}
                  label={`${resourceTypeEmoji(r.resource_type)} ${r.title ?? 'Untitled'}`}
                />
              ))}
            </nav>
          </div>
        )}
      </div>
    </aside>
  )
}

function SidebarLink({ href, active, label }: { href: string; active: boolean; label: string }) {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors truncate',
        active
          ? 'bg-primary/10 text-primary font-medium'
          : 'text-muted-foreground hover:text-foreground hover:bg-accent'
      )}
    >
      {label}
    </Link>
  )
}

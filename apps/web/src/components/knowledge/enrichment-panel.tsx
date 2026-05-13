'use client'
import { useEffect, useState } from 'react'
import { listEnrichments, triggerEnrichment } from '@/lib/api'
import type { EnrichmentOutput, AiTagsContent, EntitiesContent, KeyInsightsContent, SummaryContent } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

interface EnrichmentPanelProps {
  resourceId: string
}

const ENTITY_ICONS: Record<string, string> = {
  tools: '🔧',
  frameworks: '⚙️',
  papers: '📄',
  methodologies: '🔬',
}

export function EnrichmentPanel({ resourceId }: EnrichmentPanelProps) {
  const [enrichments, setEnrichments] = useState<EnrichmentOutput[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)

  useEffect(() => {
    setLoading(true)
    listEnrichments(resourceId)
      .then(setEnrichments)
      .catch(() => setEnrichments([]))
      .finally(() => setLoading(false))
  }, [resourceId])

  async function handleTrigger() {
    setTriggering(true)
    try {
      await triggerEnrichment(resourceId)
      setTimeout(() => {
        listEnrichments(resourceId).then(setEnrichments)
        setTriggering(false)
      }, 3000)
    } catch {
      setTriggering(false)
    }
  }

  const byType = Object.fromEntries(enrichments.map((e) => [e.enrichment_type, e]))
  const concise = byType['summary_concise']?.content as unknown as SummaryContent | undefined
  const detailed = byType['summary_detailed']?.content as unknown as SummaryContent | undefined
  const insights = byType['key_insights']?.content as unknown as KeyInsightsContent | undefined
  const tags = byType['ai_tags']?.content as unknown as AiTagsContent | undefined
  const entities = byType['entities']?.content as unknown as EntitiesContent | undefined
  const summaryMeta = byType['summary_concise']

  if (loading) {
    return (
      <div className="flex flex-col gap-3 p-1">
        <Skeleton className="h-4 w-24 mb-1" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-4 w-20 mb-1" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    )
  }

  if (enrichments.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-8 text-center">
        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-2xl">🤖</div>
        <div>
          <p className="text-sm font-medium">No AI enrichments yet</p>
          <p className="text-xs text-muted-foreground mt-0.5">Generate summaries, tags and entities</p>
        </div>
        <Button size="sm" onClick={handleTrigger} disabled={triggering}>
          {triggering ? '⏳ Queued...' : '✨ Generate AI Enrichments'}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5 text-sm">

      {/* ── Summary ─────────────────────────────────────────────────────── */}
      {(concise || detailed) && (
        <div>
          <SectionLabel icon="✦" label="Summary" />
          <div className="mt-2 rounded-xl border border-primary/15 bg-gradient-to-br from-primary/5 to-primary/[0.02] overflow-hidden">
            {concise?.text && (
              <div className="px-3.5 py-3 border-b border-primary/10">
                <p className="text-xs text-primary/70 font-medium uppercase tracking-wider mb-1.5">TL;DR</p>
                <p className="text-sm leading-relaxed text-foreground/85 font-medium">{concise.text}</p>
              </div>
            )}
            {detailed?.text && detailed.text !== concise?.text && (
              <div className="px-3.5 py-3">
                <p className="text-xs text-muted-foreground/60 font-medium uppercase tracking-wider mb-1.5">Full</p>
                <p className="text-xs leading-relaxed text-foreground/70">{detailed.text}</p>
              </div>
            )}
            {summaryMeta && (
              <div className="px-3.5 py-1.5 bg-muted/30 flex gap-2 text-[10px] text-muted-foreground/60 border-t border-border/20">
                <span>{summaryMeta.model_name}</span>
                <span>·</span>
                <span>{summaryMeta.processing_ms}ms</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Key Insights ─────────────────────────────────────────────────── */}
      {insights && insights.items.length > 0 && (
        <div>
          <SectionLabel icon="💡" label="Key Insights" />
          <ul className="mt-2 flex flex-col gap-1.5">
            {insights.items.map((item, i) => (
              <li key={i} className="flex gap-2.5 text-xs leading-relaxed text-foreground/80 bg-card/40 rounded-lg px-3 py-2 border border-border/30">
                <span className="text-amber-500 flex-shrink-0 mt-0.5 font-bold">#{i + 1}</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── AI Tags ──────────────────────────────────────────────────────── */}
      {tags && tags.tags.length > 0 && (
        <div>
          <SectionLabel icon="🏷" label="AI Tags" />
          <div className="mt-2 flex flex-wrap gap-1.5">
            {tags.tags.map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="text-xs px-2 py-0.5 cursor-pointer hover:bg-primary/20 hover:text-primary transition-colors"
              >
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* ── Entities ─────────────────────────────────────────────────────── */}
      {entities && Object.values(entities).some((arr) => arr.length > 0) && (
        <div>
          <SectionLabel icon="🔍" label="Entities" />
          <div className="mt-2 flex flex-col gap-2">
            {(Object.entries(entities) as [keyof EntitiesContent, string[]][])
              .filter(([, arr]) => arr.length > 0)
              .map(([key, items]) => (
                <div key={key} className="rounded-lg border border-border/30 bg-card/30 p-2.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                    {ENTITY_ICONS[key]} {key}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {items.map((item) => (
                      <span key={item} className="text-xs bg-background/60 border border-border/40 rounded-md px-1.5 py-0.5 text-foreground/75">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      <div className="pt-1 border-t border-border/20">
        <Button variant="ghost" size="sm" className="text-xs w-full hover:bg-primary/10 hover:text-primary" onClick={handleTrigger} disabled={triggering}>
          {triggering ? '⏳ Queued...' : '↺ Re-run AI Enrichment'}
        </Button>
      </div>
    </div>
  )
}

function SectionLabel({ icon, label }: { icon: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-sm">{icon}</span>
      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{label}</h4>
    </div>
  )
}



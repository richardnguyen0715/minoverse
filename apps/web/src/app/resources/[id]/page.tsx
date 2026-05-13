'use client'
import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import { getResource, getResourceContent, listEnrichments, getNoteBacklinks } from '@/lib/api'
import type { Resource, ResourceContent, EnrichmentOutput, WikiLink } from '@/lib/types'
import { resourceTypeLabel, resourceTypeColor, resourceTypeEmoji, formatDate, cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EnrichmentPanel } from '@/components/knowledge/enrichment-panel'
import { KnowledgeGraph } from '@/components/graph/knowledge-graph'
import { useKnowledgeStore } from '@/store/knowledge-store'

export default function ResourcePage() {
  const { id } = useParams<{ id: string }>()
  const [resource, setResource] = useState<Resource | null>(null)
  const [content, setContent] = useState<ResourceContent | null>(null)
  const [enrichments, setEnrichments] = useState<EnrichmentOutput[]>([])
  const [backlinks, setBacklinks] = useState<WikiLink[]>([])
  const [loading, setLoading] = useState(true)
  const { addRecentResource } = useKnowledgeStore()

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      getResource(id),
      listEnrichments(id).catch(() => [] as EnrichmentOutput[]),
      getResourceContent(id).catch(() => null as ResourceContent | null),
    ]).then(([res, enr, cnt]) => {
      setResource(res)
      setEnrichments(enr)
      setContent(cnt)
      addRecentResource(res)
      getNoteBacklinks(id).then(setBacklinks).catch(() => {})
    }).finally(() => setLoading(false))
  }, [id, addRecentResource])

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

  if (!resource) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p>Resource not found</p>
      </div>
    )
  }

  const headings = resource.extra_metadata?.headings ?? []
  const wordCount = resource.extra_metadata?.word_count
  const aliases = resource.extra_metadata?.aliases ?? []
  const urls = resource.extra_metadata?.urls ?? []
  const aiTagsEnrichment = enrichments.find((e) => e.enrichment_type === 'ai_tags')
  const aiTags = aiTagsEnrichment ? (aiTagsEnrichment.content as { tags: string[] }).tags : []
  const summaryEnrichment = enrichments.find((e) => e.enrichment_type === 'summary_concise')
  const summaryText = summaryEnrichment ? (summaryEnrichment.content as { text: string }).text : null
  // Only show the summary card if text is clean (not raw JSON / code blocks)
  const cleanSummary = summaryText && !summaryText.includes('```') && !summaryText.startsWith('{') ? summaryText : null

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── Main content column ── */}
      <div className="flex-1 overflow-auto p-6 min-w-0">

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-start gap-3 mb-3">
            <span className="text-3xl mt-0.5">{resourceTypeEmoji(resource.resource_type)}</span>
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold leading-tight mb-1.5">{resource.title ?? 'Untitled'}</h1>
              <div className="flex items-center gap-2 flex-wrap text-xs text-muted-foreground">
                <span className={cn('px-2 py-0.5 rounded-full font-medium', resourceTypeColor(resource.resource_type))}>
                  {resourceTypeLabel(resource.resource_type)}
                </span>
                {resource.author && <span>by {resource.author}</span>}
                {wordCount && <><span>·</span><span>{wordCount.toLocaleString()} words</span></>}
                <span>·</span>
                <span>updated {formatDate(resource.updated_at)}</span>
              </div>
            </div>
          </div>

          {resource.url && (
            <a href={resource.url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline break-all">
              {resource.url}
            </a>
          )}

          {aiTags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3">
              {aiTags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">🏷 {tag}</Badge>
              ))}
            </div>
          )}

          {aliases.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {aliases.map((a) => (
                <span key={a} className="text-xs text-muted-foreground border border-border/50 px-1.5 py-0.5 rounded">{a}</span>
              ))}
            </div>
          )}
        </div>

        {/* AI Summary card */}
        {cleanSummary && (
          <div className="mb-6 rounded-xl border border-primary/20 bg-gradient-to-br from-primary/8 to-primary/[0.02] overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-primary/10 bg-primary/5">
              <span className="text-sm">✦</span>
              <span className="text-xs font-semibold text-primary">AI Summary</span>
              {summaryEnrichment && (
                <span className="text-[10px] text-muted-foreground/60 ml-auto">
                  {summaryEnrichment.model_name} · {summaryEnrichment.processing_ms}ms
                </span>
              )}
            </div>
            <div className="px-4 py-3">
              <p className="text-sm leading-relaxed text-foreground/85">{cleanSummary}</p>
            </div>
          </div>
        )}

        {/* Markdown body content */}
        {content?.raw_markdown && (
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Content</h3>
            <MarkdownBody markdown={content.raw_markdown} />
          </div>
        )}

        {/* Table of contents */}
        {headings.length > 0 && !content?.raw_markdown && (
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Contents</h3>
            <nav className="flex flex-col gap-1">
              {headings.map((h, i) => (
                <div
                  key={i}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  style={{ paddingLeft: `${(h.level - 1) * 12}px` }}
                >
                  <span className="text-muted-foreground/50 mr-1">{'#'.repeat(h.level)}</span>
                  {h.text}
                </div>
              ))}
            </nav>
          </div>
        )}

        {/* Links */}
        {urls.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Links in Document</h3>
            <div className="flex flex-col gap-1">
              {urls.slice(0, 5).map((url, i) => (
                <a key={i} href={url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline truncate">
                  {url}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Backlinks */}
        {backlinks.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Referenced by ({backlinks.length})
            </h3>
            <div className="flex flex-col gap-1.5">
              {backlinks.map((link) => (
                <div key={link.id} className="text-xs text-muted-foreground p-2 rounded border border-border/30 bg-card/30">
                  📝 {link.anchor_text ?? link.target_raw}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer meta */}
        <div className="mt-8 pt-4 border-t border-border/30 text-xs text-muted-foreground flex flex-wrap gap-4">
          <span>Created: {formatDate(resource.created_at)}</span>
          <span>Updated: {formatDate(resource.updated_at)}</span>
          {resource.language && <span>Language: {resource.language}</span>}
          <span className="text-muted-foreground/40">ID: {resource.id}</span>
        </div>
      </div>

      {/* ── Right panel ── */}
      <aside className="w-72 border-l border-border/50 flex-shrink-0 overflow-auto bg-card/20">
        <Tabs defaultValue="ai" className="flex flex-col h-full">
          <TabsList className="w-full rounded-none border-b border-border/50 bg-transparent h-9 flex-shrink-0">
            <TabsTrigger value="ai" className="flex-1 text-xs rounded-none">🤖 AI</TabsTrigger>
            <TabsTrigger value="graph" className="flex-1 text-xs rounded-none">⬡ Graph</TabsTrigger>
            <TabsTrigger value="meta" className="flex-1 text-xs rounded-none">ℹ Info</TabsTrigger>
          </TabsList>
          <TabsContent value="ai" className="flex-1 p-3 mt-0 overflow-auto">
            <EnrichmentPanel resourceId={resource.id} />
          </TabsContent>
          <TabsContent value="graph" className="flex-1 p-3 mt-0 overflow-auto">
            <KnowledgeGraph
              resourceId={resource.id}
              resourceTitle={resource.title ?? 'Untitled'}
              resourceType={resource.resource_type}
              backlinks={backlinks}
              enrichments={enrichments}
            />
            <p className="text-xs text-muted-foreground mt-2 text-center">Local knowledge neighborhood</p>
          </TabsContent>
          <TabsContent value="meta" className="flex-1 p-3 mt-0 overflow-auto">
            <div className="flex flex-col gap-3 text-xs">
              <MetaRow label="Type" value={resourceTypeLabel(resource.resource_type)} />
              {resource.author && <MetaRow label="Author" value={resource.author} />}
              {resource.language && <MetaRow label="Language" value={resource.language} />}
              {wordCount && <MetaRow label="Word count" value={wordCount.toLocaleString()} />}
              {headings.length > 0 && <MetaRow label="Headings" value={String(headings.length)} />}
              {urls.length > 0 && <MetaRow label="Links" value={String(urls.length)} />}
              {aliases.length > 0 && <MetaRow label="Aliases" value={aliases.join(', ')} />}
              <MetaRow label="Created" value={formatDate(resource.created_at)} />
              <MetaRow label="Updated" value={formatDate(resource.updated_at)} />
              <MetaRow label="AI enrichments" value={String(enrichments.length)} />
            </div>
          </TabsContent>
        </Tabs>
      </aside>
    </div>
  )
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-muted-foreground text-[10px] uppercase tracking-wider">{label}</span>
      <span className="text-foreground/80">{value}</span>
    </div>
  )
}

function MarkdownBody({ markdown }: { markdown: string }) {
  const processed = markdown.replace(/\[\[([^\]]+)\]\]/g, '$1')

  return (
    <div className="max-w-none text-foreground/85 space-y-2">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          h1: ({ children }) => <h1 className="text-xl font-bold mt-6 mb-2 text-foreground">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-bold mt-5 mb-2 text-foreground border-b border-border/30 pb-1">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-bold mt-4 mb-1.5 text-foreground/90">{children}</h3>,
          h4: ({ children }) => <h4 className="text-sm font-semibold mt-4 mb-1 text-foreground/90">{children}</h4>,
          h5: ({ children }) => <h5 className="text-sm font-semibold mt-3 mb-1 text-foreground/80">{children}</h5>,
          h6: ({ children }) => <h6 className="text-xs font-semibold mt-3 mb-1 text-foreground/80">{children}</h6>,
          p: ({ children }) => <p className="text-sm leading-relaxed my-1.5 text-foreground/85">{children}</p>,
          strong: ({ children }) => <strong className="font-bold text-foreground">{children}</strong>,
          em: ({ children }) => <em className="italic text-foreground/80">{children}</em>,
          ul: ({ children }) => <ul className="my-2 space-y-1 pl-4">{children}</ul>,
          ol: ({ children }) => <ol className="my-2 space-y-1 pl-4 list-decimal">{children}</ol>,
          li: ({ children }) => <li className="text-sm text-foreground/85 list-disc">{children}</li>,
          blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/40 pl-3 italic text-foreground/70 my-2">{children}</blockquote>,
          code: ({ className, children }) => {
            if (className?.startsWith('language-')) {
              return <code className={cn('block text-sm font-mono', className)}>{children}</code>
            }
            return <code className="text-xs bg-muted px-1 py-0.5 rounded font-mono text-primary">{children}</code>
          },
          pre: ({ children }) => <pre className="bg-muted/50 border border-border/40 rounded-lg p-3 overflow-x-auto text-sm my-3">{children}</pre>,
          table: ({ children }) => <div className="overflow-x-auto my-3"><table className="w-full text-sm border-collapse border border-border/40 rounded">{children}</table></div>,
          thead: ({ children }) => <thead className="bg-muted/40">{children}</thead>,
          th: ({ children }) => <th className="text-left py-2 px-3 font-semibold text-foreground text-xs uppercase tracking-wider border-b border-border/50">{children}</th>,
          td: ({ children }) => <td className="py-2 px-3 text-foreground/80 border-b border-border/20">{children}</td>,
          a: ({ href, children }) => <a href={href ?? '#'} target="_blank" rel="noreferrer" className="text-primary underline hover:text-primary/80">{children}</a>,
          hr: () => <hr className="border-border/40 my-4" />,
        }}
      >
        {processed}
      </ReactMarkdown>
    </div>
  )
}



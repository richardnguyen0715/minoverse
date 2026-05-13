'use client'
import { useEffect, useCallback } from 'react'
import { ReactFlow, Background, Controls, useNodesState, useEdgesState, MarkerType } from '@xyflow/react'
import type { Node, Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { WikiLink, EnrichmentOutput, RelatedContent } from '@/lib/types'
import { resourceTypeEmoji } from '@/lib/utils'
import { useRouter } from 'next/navigation'

interface KnowledgeGraphProps {
  resourceId: string
  resourceTitle: string
  resourceType: string
  backlinks?: WikiLink[]
  enrichments?: EnrichmentOutput[]
}

export function KnowledgeGraph({ resourceId, resourceTitle, resourceType, backlinks = [], enrichments = [] }: KnowledgeGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const router = useRouter()

  useEffect(() => {
    const relatedEnrichment = enrichments.find((e) => e.enrichment_type === 'related')
    const _relatedIds = relatedEnrichment ? (relatedEnrichment.content as unknown as RelatedContent).resource_ids : []

    const centerNode: Node = {
      id: resourceId,
      position: { x: 250, y: 200 },
      data: { label: `${resourceTypeEmoji(resourceType as Parameters<typeof resourceTypeEmoji>[0])} ${resourceTitle ?? 'Current'}` },
      style: {
        background: 'hsl(var(--primary))',
        color: 'hsl(var(--primary-foreground))',
        border: 'none',
        borderRadius: '8px',
        padding: '8px 12px',
        fontSize: '12px',
        fontWeight: 600,
      },
    }

    const backlinkNodes: Node[] = backlinks.slice(0, 6).map((link, i) => {
      const angle = (i / Math.min(backlinks.length, 6)) * 2 * Math.PI
      return {
        id: `bl-${link.source_note_id}`,
        position: {
          x: 250 + 180 * Math.cos(angle),
          y: 200 + 130 * Math.sin(angle),
        },
        data: { label: `📝 ${link.anchor_text ?? link.target_raw}` },
        style: {
          background: 'hsl(var(--card))',
          border: '1px solid hsl(var(--border))',
          borderRadius: '8px',
          padding: '6px 10px',
          fontSize: '11px',
          color: 'hsl(var(--foreground))',
          cursor: 'pointer',
        },
      }
    })

    const backlinkEdges: Edge[] = backlinks.slice(0, 6).map((link) => ({
      id: `e-bl-${link.source_note_id}`,
      source: `bl-${link.source_note_id}`,
      target: resourceId,
      style: { stroke: 'hsl(var(--muted-foreground))', strokeWidth: 1 },
      markerEnd: { type: MarkerType.ArrowClosed },
    }))

    setNodes([centerNode, ...backlinkNodes])
    setEdges([...backlinkEdges])
  }, [resourceId, resourceTitle, resourceType, backlinks, enrichments, setNodes, setEdges])

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    if (node.id !== resourceId && !node.id.startsWith('bl-')) {
      router.push(`/resources/${node.id}`)
    }
  }, [resourceId, router])

  return (
    <div style={{ height: '280px' }} className="rounded-lg overflow-hidden border border-border/50 bg-card/30">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
      >
        <Background color="hsl(var(--muted))" gap={16} />
        <Controls showInteractive={false} className="!bg-card !border-border" />
      </ReactFlow>
    </div>
  )
}

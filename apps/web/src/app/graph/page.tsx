'use client'
import { useEffect, useState, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react'
import type { Node, Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { ConceptEntity, GraphData } from '@/lib/types'
import { fetchFullGraph } from '@/lib/api'
import { entityTypeColor } from '@/lib/utils'

const LOADING_SKELETON = (
  <div className="flex items-center justify-center h-full text-muted-foreground text-sm animate-pulse">
    Loading knowledge graph…
  </div>
)

const EMPTY_STATE = (
  <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-2">
    <span className="text-4xl">🕸️</span>
    <p className="text-sm">No entities yet. Index some vault files and trigger enrichment first.</p>
  </div>
)

function buildFlow(data: GraphData): { nodes: Node[]; edges: Edge[] } {
  const cols = Math.max(Math.ceil(Math.sqrt(data.nodes.length)), 1)
  const nodes: Node[] = data.nodes.map((entity, i) => ({
    id: entity.id,
    position: {
      x: (i % cols) * 220,
      y: Math.floor(i / cols) * 120,
    },
    data: {
      label: entity.name,
      entity,
    },
    style: {
      background: entityTypeColor(entity.entity_type),
      color: '#fff',
      border: 'none',
      borderRadius: '6px',
      padding: '6px 10px',
      fontSize: '12px',
      fontWeight: 600,
      minWidth: '100px',
      textAlign: 'center',
    },
  }))

  const edges: Edge[] = data.edges.map((rel) => ({
    id: `${rel.source}-${rel.target}-${rel.relation_type}`,
    source: rel.source,
    target: rel.target,
    label: rel.relation_type.replace('_', ' '),
    style: { stroke: 'hsl(var(--muted-foreground))', strokeWidth: 1 },
    markerEnd: { type: MarkerType.ArrowClosed },
    labelStyle: { fontSize: 9, fill: 'hsl(var(--muted-foreground))' },
    labelBgStyle: { fill: 'hsl(var(--card))', opacity: 0.85 },
  }))

  return { nodes, edges }
}

export default function GraphPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<ConceptEntity | null>(null)
  const [empty, setEmpty] = useState(false)
  const [groupByType, setGroupByType] = useState(false)

  useEffect(() => {
    fetchFullGraph()
      .then((data) => {
        if (data.nodes.length === 0) {
          setEmpty(true)
        } else {
          const { nodes: n, edges: e } = buildFlow(data)
          setNodes(n)
          setEdges(e)
        }
      })
      .catch(() => setEmpty(true))
      .finally(() => setLoading(false))
  }, [setNodes, setEdges])

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelected((node.data as { entity: ConceptEntity }).entity)
  }, [])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/50">
        <h1 className="text-sm font-semibold flex items-center gap-2">🕸️ Knowledge Graph</h1>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={groupByType}
              onChange={(e) => setGroupByType(e.target.checked)}
              className="rounded"
            />
            Group by type
          </label>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
          {loading && LOADING_SKELETON}
          {!loading && empty && EMPTY_STATE}
          {!loading && !empty && (
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
              <Controls className="!bg-card !border-border" />
              <MiniMap
                nodeColor={(n) => {
                  const entity = (n.data as { entity: ConceptEntity }).entity
                  return entity ? entityTypeColor(entity.entity_type) : '#6b7280'
                }}
                className="!bg-card !border-border"
              />
            </ReactFlow>
          )}
        </div>

        {selected && (
          <aside className="w-64 border-l border-border/50 bg-card/30 p-4 flex flex-col gap-2 overflow-y-auto">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Entity</span>
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                ✕
              </button>
            </div>
            <div
              className="inline-block rounded px-2 py-0.5 text-xs font-semibold text-white w-fit"
              style={{ background: entityTypeColor(selected.entity_type) }}
            >
              {selected.entity_type}
            </div>
            <p className="text-sm font-semibold">{selected.name}</p>
            {selected.description && (
              <p className="text-xs text-muted-foreground leading-relaxed">{selected.description}</p>
            )}
          </aside>
        )}
      </div>
    </div>
  )
}

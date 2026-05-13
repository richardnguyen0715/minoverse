# Phase 4 — Knowledge Graph: Usage Guide

## Quick Start

1. **Start the stack**: `make start`
2. **Index vault files**: `make index`
3. **Start the worker** (if not already): `make worker`
4. **Visit the graph UI**: [http://localhost:3000/graph](http://localhost:3000/graph)

---

## How It Works

```
Vault file → parse → ingest → [enrichment worker] → entities AI enrichment
                                          ↓
                              [graph worker] → entity_promotion_service
                                                       ↓
                                         upsert concept_entities + resource_entities
                                                       ↓
                                         relation_generation_service (Ollama)
                                                       ↓
                                         upsert concept_relations
```

The graph worker runs automatically after every vault file ingestion.

---

## API Reference

All endpoints are under `http://localhost:8000/graph`.

### List all entities
```
GET /graph/entities
GET /graph/entities?entity_type=technology
```

Response:
```json
[
  {
    "id": "...",
    "name": "Transformer",
    "entity_type": "technology",
    "canonical_name": "transformer",
    "description": null
  }
]
```

### Get entity by ID
```
GET /graph/entities/{entity_id}
```

### Get entity neighbors
```
GET /graph/entities/{entity_id}/neighbors?depth=1
```

### Get full knowledge graph
```
GET /graph/full
```

Response:
```json
{
  "nodes": [{ "id": "...", "name": "...", "entity_type": "...", "description": null }],
  "edges": [{ "source": "...", "target": "...", "relation_type": "related_to", "weight": 1.0 }]
}
```

### Get resource-scoped graph
```
GET /graph/resource/{resource_id}
```

### Trigger graph build manually
```
POST /graph/resource/{resource_id}/build
```

---

## Web UI

Visit [http://localhost:3000/graph](http://localhost:3000/graph).

**Node colours by entity type:**
| Type | Colour |
|------|--------|
| concept | Blue |
| person | Green |
| technology | Orange |
| framework | Purple |
| organization | Red |
| place | Teal |

**Interactions:**
- Click a node → see entity details in the side panel
- Zoom in/out with scroll wheel or Controls panel
- Fit view with the fit button in Controls
- Minimap shows overview of all entities

---

## Demo Steps

1. Add a markdown file to your vault with content about AI papers.
2. Run `make index` to ingest it.
3. The enrichment worker extracts entities (e.g. "Transformer", "Vaswani").
4. The graph worker promotes those entities and calls Ollama to generate relations.
5. Visit `/graph` in the web UI to see the semantic graph.

---

## Debugging

**No entities shown:**
- Check that the enrichment worker ran: `make logs-worker`
- Verify `entities` enrichment exists: `GET /enrichment/{resource_id}`
- Check graph worker logs for errors

**Relations missing:**
- Requires at least 2 entities for a resource
- Ollama must be reachable: `curl http://localhost:11434/api/tags`
- Relations are skipped gracefully if Ollama is unavailable (warning logged)

**Re-trigger graph build:**
```
POST /graph/resource/{resource_id}/build
```

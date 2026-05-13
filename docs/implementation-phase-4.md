# Phase 4 — Knowledge Graph: Implementation Record

## Overview

Phase 4 adds a semantic knowledge graph layer to Minoverse. Named entities extracted by the Phase 3 AI enrichment pipeline are promoted into a deduplicated concept graph, and Ollama infers directed semantic relations between them. The graph is queryable via FastAPI REST endpoints and visualised in the Next.js web UI.

---

## New Database Tables

### `concept_entities`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | gen_random_uuid() |
| name | TEXT | Display name |
| entity_type | VARCHAR(50) | concept/person/technology/framework/organization/place |
| canonical_name | TEXT | Lowercased, normalised for dedup |
| description | TEXT | Optional |
| metadata | JSONB | Extra metadata (ORM field: `extra_metadata`) |
| created_at / updated_at | TIMESTAMPTZ | Auto-managed |

UNIQUE(canonical_name, entity_type)

### `resource_entities`
Junction table linking resources to concept entities.

| Column | Type | Notes |
|--------|------|-------|
| resource_id | UUID FK → resources | CASCADE |
| entity_id | UUID FK → concept_entities | CASCADE |

Composite primary key.

### `concept_relations`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| source_entity_id | UUID FK → concept_entities | CASCADE |
| target_entity_id | UUID FK → concept_entities | CASCADE |
| relation_type | VARCHAR(50) | related_to/inspired_by/references/extends |
| weight | FLOAT | Default 1.0 |
| source_resource_id | UUID FK → resources | SET NULL |
| generated_by | VARCHAR(50) | ollama/wiki_link/tag_overlap |
| metadata | JSONB | |
| created_at | TIMESTAMPTZ | |

UNIQUE(source_entity_id, target_entity_id, relation_type)

---

## New Backend Files

### ORM Entities
- `src/graph/entities/concept_entity.py` — ConceptEntity
- `src/graph/entities/resource_entity.py` — ResourceEntity junction
- `src/graph/entities/concept_relation.py` — ConceptRelation

### Schemas
- `src/graph/schemas/graph_schemas.py` — EntityType, RelationType, ConceptEntityOut, ConceptRelationOut, GraphNode, GraphEdge, GraphOut

### Repositories
- `src/graph/repositories/concept_entity_repository.py` — upsert, link, list, get
- `src/graph/repositories/concept_relation_repository.py` — upsert, list_neighbors, get_full_graph, get_resource_graph

### Services
- `src/graph/services/entity_promotion_service.py` — reads `entities` AiEnrichment → upserts ConceptEntity + link
- `src/graph/services/relation_generation_service.py` — calls Ollama to infer relations, upserts ConceptRelation
- `src/graph/services/graph_traversal_service.py` — composes GraphOut for routes

### Worker
- `src/graph/workers/graph_worker.py` — `build_graph_for_resource` Dramatiq actor

### Routes
- `src/graph/routes.py` — registered under `/graph` prefix

### Migration
- `apps/api/alembic/versions/004_add_knowledge_graph.py`

---

## Modified Files

| File | Change |
|------|--------|
| `src/main.py` | Register `graph_router` |
| `src/workers.py` | Import `graph_worker` for actor discovery |
| `src/ingestion/services/ingestion_service.py` | Enqueue `build_graph_for_resource` after commit |
| `alembic/env.py` | Import new ORM models |

---

## Frontend Changes

| File | Change |
|------|--------|
| `apps/web/src/lib/types.ts` | Add ConceptEntity, ConceptRelation, GraphData |
| `apps/web/src/lib/api.ts` | Add fetchFullGraph, fetchResourceGraph, fetchEntityNeighbors, fetchGraphEntities |
| `apps/web/src/lib/utils.ts` | Add entityTypeColor() |
| `apps/web/src/app/graph/page.tsx` | New full-graph page |
| `apps/web/src/components/layout/sidebar.tsx` | Add 🕸️ Knowledge Graph nav link |
| `apps/web/src/__tests__/lib/graph.test.ts` | 13 new unit tests |

---

## Tests

- 15 new backend unit tests in `src/graph/tests/test_phase4.py`
- 13 new frontend tests in `apps/web/src/__tests__/lib/graph.test.ts`
- All 45 backend tests pass; all 31 web tests pass

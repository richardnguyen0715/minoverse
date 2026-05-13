# Phase 3 — AI Enrichment: Implementation Record

> **Status:** Complete  
> **Completed:** 2026-05-09  
> **Commit:** `94ffd50` (`feat(enrichment): implement Phase 3 AI enrichment pipeline`)  
> **Tests:** 30 / 30 passed (11 new + 19 existing)  
> **Migration applied:** `003_add_ai_enrichments`

---

## Overview

Phase 3 delivers the AI enrichment backbone: every resource indexed into the vault automatically gets enriched with AI-generated summaries, tags, named entities, and related-resource links — all powered by a local Ollama instance and processed asynchronously via a Dramatiq worker.

### Goals

| Goal | Outcome |
|---|---|
| Async AI job system | Dramatiq actor backed by Redis broker |
| Summary generation | Concise, detailed, and key-insights summaries via Ollama |
| Auto-tagging | Up to 10 normalized AI-generated tags per resource |
| Entity extraction | Tools, frameworks, papers, and methodologies extracted from content |
| Related resources | Tag-overlap similarity (pre-Phase-2 approach) |
| AI artifact storage | `ai_enrichments` table — versioned, typed, idempotent |
| Graceful degradation | Ollama unavailable → log warning, skip enrichment, ingestion succeeds |

---

## Task 3.0 — Dependencies

**Files changed:** `apps/api/pyproject.toml`

Two new runtime dependencies added:

| Package | Version | Purpose |
|---|---|---|
| `ollama` | `>=0.4.0` | Official Ollama Python async client |
| `httpx` | `>=0.27` | HTTP transport (used transitively by ollama) |

`dramatiq[redis]` was already present from Phase 0 schema planning.

---

## Task 3.1 — New Exceptions

**File modified:** `apps/api/src/core/exceptions.py`

Two new domain exceptions added to the hierarchy:

```python
class OllamaUnavailableError(MinoverseError):
    """Raised when the Ollama service is unreachable or times out."""

class EnrichmentError(MinoverseError):
    """Raised when an AI enrichment step fails non-transiently."""
```

---

## Task 3.2 — AI Enrichment ORM Entity

**File created:** `apps/api/src/enrichment/entities/ai_enrichment.py`

```python
class AiEnrichment(Base):
    __tablename__ = "ai_enrichments"

    id: Mapped[uuid.UUID]            # PRIMARY KEY
    resource_id: Mapped[uuid.UUID]   # FK → resources.id ON DELETE CASCADE
    enrichment_type: Mapped[str]     # VARCHAR(50) — see EnrichmentType
    content: Mapped[dict]            # JSONB — AI output
    model_name: Mapped[str]          # e.g. "qwen3"
    model_version: Mapped[str | None]
    prompt_version: Mapped[str]      # "v1", "v2", ...
    processing_ms: Mapped[int | None]
    is_current: Mapped[bool]         # True for the latest record per type
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**Unique constraint:** `(resource_id, enrichment_type)` — enables the `ON CONFLICT DO UPDATE` upsert pattern used throughout Phase 3.

---

## Task 3.3 — Enrichment Schemas

**File created:** `apps/api/src/enrichment/schemas/enrichment_schemas.py`

### `EnrichmentType` (StrEnum)

```python
class EnrichmentType(StrEnum):
    SUMMARY_CONCISE  = "summary_concise"
    SUMMARY_DETAILED = "summary_detailed"
    KEY_INSIGHTS     = "key_insights"
    AI_TAGS          = "ai_tags"
    ENTITIES         = "entities"
    RELATED          = "related"
```

### Result Models (Pydantic)

| Model | Fields |
|---|---|
| `SummaryResult` | `concise: str`, `detailed: str`, `key_insights: list[str]` |
| `TaggingResult` | `tags: list[str]` (normalized, deduplicated, max 10) |
| `EntityResult` | `tools`, `frameworks`, `papers`, `methodologies`: `list[str]` |
| `RelatedResult` | `resource_ids: list[str]` (UUIDs as strings) |
| `EnrichmentOutput` | Unified API boundary model (all fields, incl. `processing_ms`) |

---

## Task 3.4 — OllamaClient Service

**File created:** `apps/api/src/enrichment/services/ollama_client.py`

### Design

- **`OllamaClientProtocol`** — `typing.Protocol` defining two methods:
  - `async generate(model, prompt, system="") -> str`
  - `async is_available() -> bool`
- **`AsyncOllamaClient`** — concrete implementation backed by `ollama.AsyncClient`
- **`get_ollama_client()`** — factory function reading `settings.ollama_base_url`

Services depend on `OllamaClientProtocol`, not the concrete class — this keeps all services unit-testable via `AsyncMock`.

### Error Handling

```
ollama.AsyncClient.generate() fails
  → OllamaUnavailableError raised
  → Caller (pipeline) catches → logs warning → marks step failed
  → Ingestion pipeline continues
```

---

## Task 3.5 — Summary Service

**File created:** `apps/api/src/enrichment/services/summary_service.py`

```python
async def generate_summary(
    content: str,
    client: OllamaClientProtocol,
    *,
    model: str = "qwen3",
) -> SummaryResult:
```

- Sends a single prompt requesting JSON with `concise`, `detailed`, `key_insights` keys
- Content is truncated to 4 000 characters before sending to avoid context overflow
- On `json.JSONDecodeError`: returns `SummaryResult(concise=response[:200], detailed=response, key_insights=[])` — graceful degradation, never raises
- On `OllamaUnavailableError` or any other exception: returns empty `SummaryResult`

---

## Task 3.6 — Tagging Service

**File created:** `apps/api/src/enrichment/services/tagging_service.py`

```python
async def generate_ai_tags(
    content: str,
    client: OllamaClientProtocol,
    *,
    model: str = "qwen3",
    max_tags: int = 10,
) -> TaggingResult:
```

- Prompts for a JSON list of `tags` (topics, concepts, domains)
- Normalization pipeline: lowercase → strip whitespace → remove empty strings → deduplicate → slice to `max_tags`
- On any error: returns `TaggingResult(tags=[])`

---

## Task 3.7 — Entity Extraction Service

**File created:** `apps/api/src/enrichment/services/entity_service.py`

```python
async def extract_entities(
    content: str,
    client: OllamaClientProtocol,
    *,
    model: str = "qwen3",
) -> EntityResult:
```

- Prompts for JSON with four keys: `tools`, `frameworks`, `papers`, `methodologies`
- Missing keys default to `[]` (Pydantic validation with `default_factory`)
- On any error: returns `EntityResult(tools=[], frameworks=[], papers=[], methodologies=[])`

---

## Task 3.8 — Related Resources Service

**File created:** `apps/api/src/enrichment/services/related_service.py`

```python
async def find_related_resources(
    resource_id: uuid.UUID,
    session: AsyncSession,
    *,
    limit: int = 5,
) -> RelatedResult:
```

Finds related resources by **tag-overlap similarity** (Jaccard-style):

```sql
SELECT rt2.resource_id, COUNT(*) AS overlap
FROM   resource_tags rt1
JOIN   resource_tags rt2
       ON rt1.tag_id = rt2.tag_id AND rt2.resource_id != rt1.resource_id
WHERE  rt1.resource_id = :resource_id
GROUP  BY rt2.resource_id
ORDER  BY overlap DESC
LIMIT  :limit
```

> **Phase-2 note:** This implementation uses tag overlap as a proxy for semantic similarity. It will be replaced by vector cosine similarity (pgvector) in Phase 2 once embeddings are stored.

---

## Task 3.9 — Enrichment Repository

**File created:** `apps/api/src/enrichment/repositories/enrichment_repository.py`

```python
async def upsert_enrichment(
    session: AsyncSession,
    *,
    resource_id: uuid.UUID,
    enrichment_type: str,
    content: dict,
    model_name: str,
    processing_ms: int,
    prompt_version: str = "v1",
) -> AiEnrichment:

async def list_enrichments_for_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
) -> list[AiEnrichment]:
```

`upsert_enrichment` uses PostgreSQL `ON CONFLICT (resource_id, enrichment_type) DO UPDATE SET ...` to ensure idempotency. Calling it twice for the same resource + type overwrites the previous result.

---

## Task 3.10 — Enrichment Pipeline

**File created:** `apps/api/src/enrichment/pipelines/enrichment_pipeline.py`

The central orchestrator for a single resource's enrichment run.

### Pipeline Steps

```
run_enrichment_for_resource(resource_id, session, ollama_client)
  0. Check ollama_client.is_available()
       → False: return early with skipped_ollama_unavailable=True
  1. Fetch resource content from resource_contents (or title fallback)
  2. generate_summary() → upsert SUMMARY_CONCISE, SUMMARY_DETAILED, KEY_INSIGHTS
  3. generate_ai_tags() → upsert AI_TAGS
  4. extract_entities() → upsert ENTITIES
  5. find_related_resources() → upsert RELATED
  → Return EnrichmentPipelineResult(succeeded=[...], failed=[...])
```

### Failure Isolation

Each of steps 2–5 is wrapped in an independent `try/except`. A failure in one step does not prevent the others from running. Failed steps are logged as `warning` and recorded in `result.failed`.

### Idempotency

All upserts use `ON CONFLICT DO UPDATE`, so calling the pipeline twice for the same resource produces identical DB state.

### Session Contract

The pipeline does **not** call `session.commit()`. The caller (Dramatiq worker) is responsible for committing after the pipeline returns.

---

## Task 3.11 — Dramatiq Enrichment Worker

**Files created:**
- `apps/api/src/enrichment/workers/enrichment_worker.py`
- `apps/api/src/workers.py` (actor discovery entry point)

```python
broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(broker)

@dramatiq.actor(max_retries=3, min_backoff=5000, time_limit=300_000)
def enrich_resource(resource_id: str) -> None:
    asyncio.run(_enrich_resource_async(resource_id))
```

| Actor option | Value | Meaning |
|---|---|---|
| `max_retries` | 3 | Retry failed jobs up to 3 times |
| `min_backoff` | 5 000 ms | Minimum wait between retries |
| `time_limit` | 300 000 ms | 5-minute wall-clock limit per job |

The actor is synchronous (Dramatiq requirement). `asyncio.run()` drives the async pipeline inside each worker invocation.

The worker process is started with:
```bash
python -m dramatiq src.workers
```

---

## Task 3.12 — Ingestion Hook

**File modified:** `apps/api/src/ingestion/services/ingestion_service.py`

After `await session.commit()` in `ingest_vault_file()`, the ingestion service now enqueues an enrichment job:

```python
try:
    from src.enrichment.workers.enrichment_worker import enrich_resource
    enrich_resource.send(str(resource.id))
    logger.info("enrichment_job_enqueued", resource_id=str(resource.id))
except Exception as exc:
    logger.warning("enrichment_enqueue_failed", error=str(exc), resource_id=str(resource.id))
```

The `try/except` ensures that if Redis is unavailable, ingestion still succeeds — the enrichment job is simply skipped for that run.

---

## Task 3.13 — FastAPI Routes

**File created:** `apps/api/src/enrichment/routes.py`  
**File modified:** `apps/api/src/main.py`

Three new endpoints registered at `/enrichment`:

| Method | Path | Description |
|---|---|---|
| `GET` | `/enrichment/{resource_id}` | List all current enrichments for a resource |
| `GET` | `/enrichment/{resource_id}/{enrichment_type}` | Get one specific enrichment type |
| `POST` | `/enrichment/{resource_id}/trigger` | Manually enqueue an enrichment job |

---

## Task 3.14 — Alembic Migration 003

**File created:** `apps/api/alembic/versions/003_add_ai_enrichments.py`

```sql
CREATE TABLE ai_enrichments (
    id              UUID PRIMARY KEY,
    resource_id     UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    enrichment_type VARCHAR(50) NOT NULL,
    content         JSONB NOT NULL DEFAULT '{}',
    model_name      VARCHAR(100) NOT NULL,
    model_version   VARCHAR(50),
    prompt_version  VARCHAR(20) NOT NULL DEFAULT 'v1',
    processing_ms   INTEGER,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_ai_enrichments_resource_type
    ON ai_enrichments (resource_id, enrichment_type);

CREATE INDEX ix_ai_enrichments_resource_id
    ON ai_enrichments (resource_id);
```

---

## Task 3.15 — Worker Lifecycle Integration

**Files modified:** `scripts/start.sh`, `scripts/stop.sh`, `scripts/status.sh`, `Makefile`

### start.sh — Step 9

```bash
_info "Starting enrichment worker..."
nohup "$API_DIR/.venv/bin/python" -m dramatiq src.enrichment.workers.enrichment_worker \
  > "$WORKER_LOG" 2>&1 &
echo $! > "$WORKER_PID_FILE"
_ok "Enrichment worker started (PID $(cat "$WORKER_PID_FILE"))"
```

### stop.sh — Step 0

Stops the worker by PID before stopping watcher and API.

### New Makefile targets

```makefile
make worker        # start worker in foreground (for development)
make logs-worker   # tail .minoverse/worker.log
```

---

## Tests

**11 pure unit tests — no DB, no network, mocked OllamaClientProtocol.**

| Test file | Tests | What it covers |
|---|---|---|
| `enrichment/tests/test_summary_service.py` | 3 | Parsed result, malformed JSON graceful degradation, Ollama unavailable |
| `enrichment/tests/test_tagging_service.py` | 3 | Normalization, max_tags limit, empty response |
| `enrichment/tests/test_entity_service.py` | 2 | Structured result, missing JSON keys default to `[]` |
| `enrichment/tests/test_enrichment_pipeline.py` | 3 | Ollama unavailable skip, step-failure isolation, idempotency |

All tests use `AsyncMock(spec=OllamaClientProtocol)` for the client and run in under 100 ms.

```bash
cd apps/api
uv run pytest src/enrichment/tests/ -v
# 11 passed in 0.30s

uv run pytest src/ -v
# 30 passed in 0.27s
```

---

## Architecture Notes

### Domain Isolation

The `enrichment` domain owns everything AI-enrichment-related:

```
enrichment/
  entities/      ← AiEnrichment ORM
  schemas/       ← EnrichmentType enum, result models, API output
  services/      ← OllamaClient, summary, tagging, entity, related
  repositories/  ← upsert_enrichment, list_enrichments_for_resource
  pipelines/     ← run_enrichment_for_resource (orchestrator)
  workers/       ← enrich_resource Dramatiq actor
  events/        ← (reserved for Phase 4 event emission)
  routes.py      ← FastAPI router
  tests/         ← unit tests
```

No other domain imports from `enrichment` — all coupling is outward (enrichment imports from `core`, `knowledge`).

### Protocol-Based Testability

`OllamaClientProtocol` is a `typing.Protocol` — services accept it as a type annotation, and tests pass `AsyncMock(spec=OllamaClientProtocol)`. No monkey-patching or `unittest.mock.patch` paths needed.

### Graceful Degradation Layers

```
Ollama unreachable
  → pipeline.is_available() → False → entire enrichment skipped
  → worker retries (up to 3×) if transient

Redis unreachable (during ingestion hook)
  → try/except → warning logged → ingestion succeeds without enrichment

Individual step failure (e.g. JSON parse error)
  → step try/except → warning logged → remaining steps continue
  → result.failed records which step(s) failed
```

### Related Resources — Pre-Phase-2 Note

The `find_related_resources()` function uses tag-overlap similarity. This is an intentional interim implementation: it requires no additional infrastructure and produces reasonable results for tag-rich vaults. Phase 2 will replace it with vector cosine similarity using `pgvector` + `bge-m3` embeddings stored in `chunk_embeddings`.

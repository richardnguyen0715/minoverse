# Phase 0 — Foundation: Implementation Record

> **Status:** Complete  
> **Commit:** `9600455`  
> **Branch:** `main`

---

## Overview

Phase 0 establishes the full infrastructure foundation for minoverse — an AI-native, local-first Personal Knowledge Operating System. Nothing in this phase is application logic; everything here is the platform that all future phases build on top of.

Deliverables:
- Monorepo directory structure
- FastAPI backend skeleton with domain-organized source
- SQLAlchemy 2 async ORM models for all Phase 0 tables
- Alembic migration `001` — 10 tables + pgvector + ivfflat index
- Docker Compose infrastructure (postgres/pgvector, redis, ollama, api, worker)
- Vault directory structure
- Shared event bus (Redis pub/sub, typed events, Pydantic payloads)

---

## 0.1 Repository Structure

The monorepo follows a domain/context-first layout (not technical-layer grouping).

```
minoverse/
├── apps/
│   ├── api/          ← FastAPI backend (Python, uv)
│   ├── web/          ← Next.js frontend (Phase 1+)
│   └── desktop/      ← Tauri desktop shell (Phase 6+)
├── services/
│   ├── ingestion/    ← Standalone ingestion service (Phase 1+)
│   ├── retrieval/    ← Standalone retrieval service (Phase 2+)
│   └── ai/           ← AI pipeline service (Phase 3+)
├── packages/
│   ├── shared/       ← Shared primitives + event bus (Python)
│   ├── schemas/      ← Shared JSON/Pydantic schemas (Phase 1+)
│   └── prompts/      ← Versioned prompt library (Phase 3+)
├── vault/            ← Markdown vault — canonical source of truth
│   ├── resources/
│   │   ├── papers/
│   │   ├── youtube/
│   │   ├── github/
│   │   ├── articles/
│   │   ├── docs/
│   │   └── social/
│   ├── notes/
│   ├── concepts/
│   ├── daily/
│   ├── assets/
│   └── templates/
└── infra/
    ├── docker-compose.yml
    ├── .env.example
    ├── postgres/
    │   └── init.sql
    └── api/
        └── Dockerfile
```

**Design decision:** `apps/` contains deployable applications; `services/` contains background microservices. Both start as stubs — only `apps/api` has code in Phase 0.

---

## 0.2 FastAPI Backend (`apps/api/`)

### Package Management

Uses `uv` (not pip/poetry). Build backend: `hatchling`.

```toml
# apps/api/pyproject.toml
[project]
name = "minoverse-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "alembic>=1.13",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "asyncpg>=0.29",
    "psycopg2-binary>=2.9",
    "redis>=5.0",
    "dramatiq[redis]>=1.17",
    "structlog>=24.0",
    "python-dotenv>=1.0",
]
```

Dev dependencies: `pytest`, `pytest-asyncio`, `mypy` (strict), `ruff`.

### Source Structure

`src/` is organized by bounded domain context — never by technical layer.

```
apps/api/src/
├── core/                   ← Cross-cutting infrastructure
│   ├── config.py           ← pydantic-settings Settings
│   ├── logging.py          ← structlog configuration
│   ├── exceptions.py       ← Domain exception hierarchy
│   ├── database.py         ← Async SQLAlchemy engine + session
│   └── main.py             ← FastAPI app factory
├── knowledge/              ← VaultFile + Resource domain
├── retrieval/              ← ResourceContent + ResourceChunk domain
├── embedding/              ← ChunkEmbedding domain (pgvector)
├── graph/                  ← WikiLink domain
├── notes/                  ← Note domain
├── tagging/                ← Tag + ResourceTag domain
├── ingestion/              ← IngestionJob domain
├── memory/                 ← AI memory domain (Phase 3+)
└── search/                 ← Hybrid retrieval domain (Phase 2+)
```

Each domain contains exactly:

```
{domain}/
├── entities/       ← SQLAlchemy ORM models
├── services/       ← Business logic orchestration
├── repositories/   ← Persistence layer only
├── schemas/        ← Pydantic I/O models
├── events/         ← Domain event handlers
└── tests/          ← Domain-scoped tests
```

### Core Layer

#### `config.py` — Settings

All configuration via environment variables, loaded by `pydantic-settings`. No hardcoded values anywhere in the codebase.

| Setting | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://minoverse:minoverse@localhost:5432/minoverse` | Async DB URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Event bus + worker queue |
| `VAULT_PATH` | `../../vault` | Filesystem path to vault |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local LLM runtime |
| `EMBEDDING_MODEL` | `bge-m3` | Default embedding model |
| `CHAT_MODEL` | `qwen3` | Default chat model |
| `DEBUG` | `false` | Enables SQLAlchemy echo + dev logging |

#### `logging.py` — Structured Logging

Uses `structlog` with two output modes:
- **Debug mode:** Pretty colored console output
- **Production mode:** JSON lines to stdout

All log entries carry: `logger_name`, `log_level`, `timestamp` (ISO 8601), plus any context bound via `structlog.contextvars`. `print()` is forbidden throughout the codebase.

#### `exceptions.py` — Domain Exception Hierarchy

```
MinoverseError (base)
├── ResourceNotFoundError
├── VaultFileNotFoundError
├── EmbeddingModelUnavailableError
├── EmbeddingTimeoutError
├── IngestionError
├── ChunkingError
└── EventPublishError
```

All exceptions accept a `context: dict[str, object]` kwarg for structured error metadata. `except Exception: pass` is forbidden.

#### `database.py` — Async SQLAlchemy

- `Base` — `DeclarativeBase` shared by all ORM models
- `engine` — `create_async_engine` with pool config from settings
- `AsyncSessionFactory` — `async_sessionmaker` with `expire_on_commit=False`
- `get_async_session()` — FastAPI dependency, yields `AsyncSession`

All database access goes through `get_async_session()`. Raw SQL is forbidden outside Alembic migrations and repository methods.

### ORM Models

| Model | Table | Domain | Description |
|---|---|---|---|
| `VaultFile` | `vault_files` | `knowledge` | Filesystem index — one row per vault `.md` file |
| `Resource` | `resources` | `knowledge` | Universal knowledge object (paper, video, note, etc.) |
| `ResourceContent` | `resource_contents` | `retrieval` | Normalized parsed content (markdown, clean text, HTML) |
| `ResourceChunk` | `resource_chunks` | `retrieval` | Semantic chunk unit for RAG and retrieval |
| `ChunkEmbedding` | `chunk_embeddings` | `embedding` | pgvector embedding per chunk (1536 dims) |
| `Note` | `notes` | `notes` | Obsidian-compatible note record with frontmatter |
| `WikiLink` | `wiki_links` | `graph` | Directed `[[Link]]` edge between notes |
| `Tag` | `tags` | `tagging` | Hierarchical tag node (supports parent-child) |
| `ResourceTag` | `resource_tags` | `tagging` | Resource ↔ Tag junction (manual + AI tagging) |
| `IngestionJob` | `ingestion_jobs` | `ingestion` | Async ingestion pipeline job tracker |

---

## 0.3 Docker Compose (`infra/`)

### Services

| Service | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | `5432` | Primary database with pgvector extension |
| `redis` | `redis:7-alpine` | `6379` | Event bus pub/sub + Dramatiq worker queue |
| `ollama` | `ollama/ollama:latest` | `11434` | Local LLM runtime (embeddings + chat) |
| `api` | Custom (python:3.12-slim + uv) | `8000` | FastAPI application server |
| `worker` | Same as `api` | — | Dramatiq background worker |

### Startup Order

```
postgres (healthy) ─┐
                     ├→ api
redis    (healthy) ─┘
                     └→ worker
```

`ollama` starts independently. Models must be pulled manually after startup.

### Init SQL

`infra/postgres/init.sql` runs once on first container creation:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

This is separate from Alembic migrations — it prepares the database instance before the application migration runs.

---

## 0.4 Vault Structure

```
vault/
├── resources/          ← External knowledge (imported content)
│   ├── papers/         ← Academic papers
│   ├── youtube/        ← YouTube videos / transcripts
│   ├── github/         ← GitHub repos / READMEs
│   ├── articles/       ← Web articles / blog posts
│   ├── docs/           ← Documentation pages
│   └── social/         ← Tweets, posts, threads
├── notes/              ← Personal atomic / permanent notes
├── concepts/           ← Concept definitions
├── daily/              ← Daily notes (YYYY-MM-DD.md)
├── assets/             ← Images, PDFs, attachments
└── templates/          ← Note templates
```

**Invariant:** The vault filesystem is the canonical source of truth. The database is a projection. No canonical content is stored only in the database.

Each resource file uses YAML frontmatter:

```markdown
---
id: <uuid>
type: paper
tags:
  - rag
  - llm
url: https://arxiv.org/abs/1706.03762
---

# Attention Is All You Need
```

---

## 0.5 Core Database Schema

### Alembic Migration `001_initial_schema`

File: `apps/api/alembic/versions/001_initial_schema.py`

**Revision chain:** `None → 001` (initial)

The migration creates 10 tables in dependency order and then applies vector indexing:

#### Table Creation Order

```
vault_files
    └── resources (FK → vault_files)
            ├── resource_contents (FK → resources, CASCADE)
            ├── resource_chunks   (FK → resources, CASCADE)
            │       └── chunk_embeddings (FK → resource_chunks, CASCADE)
            ├── wiki_links (resolved_resource_id → resources)
            └── resource_tags (FK → resources, CASCADE)
    └── notes (FK → vault_files)
            └── wiki_links (source/target → notes)
tags
    ├── tags.parent_tag_id (self-ref FK)
    └── resource_tags (FK → tags, CASCADE)
ingestion_jobs (independent)
```

#### Vector Column

`chunk_embeddings.embedding` is created as `TEXT` by Alembic then immediately altered:

```sql
ALTER TABLE chunk_embeddings
  ALTER COLUMN embedding TYPE vector(1536)
  USING embedding::vector(1536);
```

This pattern is required because SQLAlchemy's DDL layer doesn't natively emit `VECTOR(n)` types; the `pgvector` extension handles the cast.

#### Indexes Created

| Index | Table | Type | Purpose |
|---|---|---|---|
| `ix_resources_resource_type` | `resources` | B-tree | Filter by resource type |
| `ix_resources_is_archived` | `resources` | B-tree | Filter archived resources |
| `ix_resources_metadata_gin` | `resources` | GIN | JSONB metadata queries |
| `ix_resource_chunks_resource_id` | `resource_chunks` | B-tree | Chunks by resource |
| `chunk_embedding_idx` | `chunk_embeddings` | ivfflat | ANN vector similarity search |
| `ix_wiki_links_source_note_id` | `wiki_links` | B-tree | Outgoing links from note |
| `ix_wiki_links_target_note_id` | `wiki_links` | B-tree | Incoming links (backlinks) |
| `ix_ingestion_jobs_status` | `ingestion_jobs` | B-tree | Queue status polling |

#### ivfflat Configuration

```sql
CREATE INDEX chunk_embedding_idx
ON chunk_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

`lists = 100` is appropriate for up to ~1M vectors. Tune upward as the dataset grows (rule of thumb: `lists ≈ sqrt(n_rows)`).

### Alembic Async Setup

`alembic/env.py` uses `async_engine_from_config` to run migrations over an async SQLAlchemy engine. All ORM models are imported at the top of `env.py` so Alembic's autogenerate can detect schema drift in future migrations.

---

## 0.6 Shared Event Bus (`packages/shared/`)

### Architecture

Events flow over Redis pub/sub channels. Channel names follow the pattern:

```
minoverse:{event_type}
```

Example: `minoverse:resource_created`, `minoverse:embedding_completed`

### Event Types

Defined in `packages/shared/src/events/types.py` as a `StrEnum`:

| EventType | Channel | Trigger |
|---|---|---|
| `RESOURCE_CREATED` | `minoverse:resource_created` | New resource persisted to DB |
| `RESOURCE_UPDATED` | `minoverse:resource_updated` | Resource content/metadata changed |
| `NOTE_UPDATED` | `minoverse:note_updated` | Vault note file modified on disk |
| `EMBEDDING_COMPLETED` | `minoverse:embedding_completed` | All chunks of a resource embedded |
| `SUMMARY_COMPLETED` | `minoverse:summary_completed` | AI summary generation complete |

### Payload Models

All events carry a typed Pydantic payload inheriting from `EventPayload`:

```python
class EventPayload(BaseModel):
    event_id: uuid.UUID        # auto-generated
    occurred_at: datetime      # UTC, auto-generated
```

| Payload Class | Extra Fields |
|---|---|
| `ResourceCreatedPayload` | `resource_id`, `resource_type`, `vault_file_path?` |
| `ResourceUpdatedPayload` | `resource_id`, `changed_fields: list[str]` |
| `NoteUpdatedPayload` | `note_id`, `vault_file_path` |
| `EmbeddingCompletedPayload` | `resource_id`, `chunk_count`, `embedding_model` |
| `SummaryCompletedPayload` | `resource_id`, `artifact_id`, `model_name` |

### API

**Publish:**
```python
from packages.shared.src.events.bus import publish_event
from packages.shared.src.events.types import EventType
from packages.shared.src.events.payloads import ResourceCreatedPayload

await publish_event(redis_client, EventType.RESOURCE_CREATED, payload)
```

**Subscribe:**
```python
from packages.shared.src.events.bus import subscribe_to_event

async for message in subscribe_to_event(redis_client, EventType.RESOURCE_CREATED):
    payload = ResourceCreatedPayload(**message)
    # handle event
```

### Design Constraints

- Publishers must not embed business logic — they only emit events.
- Each subscriber handles exactly one event type.
- All messages are JSON-serialized via `model_dump_json()`.
- Publish failures raise `EventPublishError` (never silent).

---

## Engineering Standards Applied

| Standard | Implementation |
|---|---|
| Strict typing | `mypy strict = true` in `pyproject.toml`; all models fully typed |
| No `Any` / bare `dict` | All collections typed: `list[ResourceChunk]`, `dict[str, object]` |
| Google-style docstrings | All public classes and functions |
| Structured logging | `structlog` everywhere; `print()` forbidden |
| Domain organization | 9 domains, each with 6 internal layers |
| No framework leakage | `Base`, `engine` are in `core/`; domains are framework-agnostic |
| Repository pattern | ORM models hold only data; no business logic |
| Pydantic boundaries | All event payloads and future API I/O go through Pydantic |
| Explicit exceptions | 7 domain exception types; bare `except Exception: pass` forbidden |
| Idempotent migrations | `CREATE EXTENSION IF NOT EXISTS vector`; `upgrade()`/`downgrade()` paired |

---

## What Phase 0 Does NOT Include

These are intentionally deferred to later phases:

- **Markdown parser** — Phase 1 (`markdown-it-py`, `python-frontmatter`)
- **File watcher** — Phase 1 (`watchfiles`)
- **Any API routes** — Phase 1 (knowledge CRUD) and Phase 2 (retrieval)
- **Embedding generation** — Phase 3 (sentence-transformers / Ollama)
- **AI pipelines** — Phase 3 (summarization, entity extraction)
- **Next.js frontend** — Phase 1+
- **Tauri desktop** — Phase 6
- **Graph visualization** — Phase 4

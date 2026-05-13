# minoverse

> **Personal Autonomous Research & Knowledge Operating System** — ingest anything, remember everything.

Minoverse is an AI-native knowledge infrastructure platform. It combines a local-first Markdown vault, a FastAPI backend with AI enrichment, a CLI agent runtime, and Telegram integration — enabling autonomous research, knowledge extraction, and long-term memory.

```
Telegram / CLI / Mobile
      ↓
Ingestion Gateway  ←→  Event Queue (Redis / NATS)
      ↓
Agent Runtime (AutoIngest CLI)
observe → plan → tool_call → reflect → store_memory
      ↓
Scraping Service → Summarization → Entity Extraction
      ↓
PostgreSQL + pgvector + Knowledge Graph
      ↓
Notification (Telegram streaming)
```

---

## Architecture at a Glance

| Layer | Technology | Status |
|---|---|---|
| Canonical storage | Markdown filesystem (`vault/`) | ✅ Phase 0 |
| Backend API | FastAPI (Python 3.12, uv) | ✅ Phase 0 |
| Database | PostgreSQL 16 + pgvector (ivfflat) | ✅ Phase 0 |
| ORM / migrations | SQLAlchemy 2 async + Alembic | ✅ Phase 0 |
| Event bus | Redis pub/sub | ✅ Phase 0 |
| Markdown parser | markdown-it-py + python-frontmatter | ✅ Phase 1 |
| File watcher | watchfiles async | ✅ Phase 1 |
| Vault indexing CLI | Typer (`minoverse index`, `watch`, `graph`) | ✅ Phase 1 |
| Wiki link graph | Forward + backlink resolution | ✅ Phase 1 |
| Full-text search | PostgreSQL FTS | Phase 2 |
| Hybrid retrieval | BM25 + semantic + graph | Phase 2 |
| Background workers | Dramatiq + Redis | ✅ Phase 3 |
| AI enrichment | Summaries, tagging, entities, related (Ollama) | ✅ Phase 3 |
| LLM runtime | Layered AI infrastructure: Provider/Runtime/Prompts/Skills | ✅ Phase 3 |
| Embeddings | pgvector + bge-m3 vector similarity | Phase 2 |
| **Knowledge Graph** | **Concept entities, semantic relations, graph UI** | **✅ Phase 4** |
| **Conversational memory** | **Session + turn storage, persistent chat history** | **✅ Phase 5** |
| **Episodic memory** | **AI-distilled research sessions** | **✅ Phase 5** |
| **Semantic memory** | **Durable knowledge concepts extracted by AI** | **✅ Phase 5** |
| **AI Copilot** | **Ask vault, contextual retrieval, sourced answers** | **✅ Phase 5** |
| **Event Sourcing** | **sync_events audit log, replay, CRDT-ready fields** | **✅ Phase 6** |
| **Desktop shell** | **Tauri v2 — native OS wrapper for web UI** | **✅ Phase 6** |
| **AutoIngest CLI** | **TypeScript/Bun agent CLI — URL ingestion, research, memory** | **✅ Phase AI** |
| **Telegram Bot** | **Python Telegram bot — /analyze, /research, /memory, /graph** | **✅ Phase AI** |
| **Scraping Service** | **YouTube, GitHub, generic web — trafilatura + yt-dlp** | **✅ Phase AI** |
| **Mobile structure** | **React Native/Expo scaffold — thin client** | **✅ Phase AI** |
| Frontend | Next.js 15 + Tailwind + shadcn/ui + Zustand + React Flow | ✅ Web UI |

---

## Project Structure

```
minoverse/
├── apps/
│   ├── api/          ← FastAPI backend (Python, uv)
│   ├── autoingest/   ← AutoIngest CLI (TypeScript, Bun) ← main app
│   ├── web/          ← Next.js frontend
│   ├── desktop/      ← Tauri v2 desktop shell
│   ├── telegram/     ← Telegram bot (Python)
│   └── mobile/       ← React Native/Expo (structure)
├── services/
│   ├── scraping/     ← Scraping microservice (Python, port 8001)
│   ├── ingestion/    ← Ingestion pipeline
│   ├── retrieval/    ← Retrieval service
│   └── ai/           ← AI pipeline service
├── packages/
│   ├── shared/       ← Event bus + shared primitives
│   ├── schemas/      ← Shared schemas
│   └── prompts/      ← Versioned prompts
├── vault/            ← Your knowledge vault (Markdown files)
├── infra/            ← Docker Compose + Dockerfiles
├── docs/             ← Implementation records
└── standards/        ← Architecture standards + policies
```

---

## Quick Start

### 1. Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker + Docker Compose | v24+ | https://docs.docker.com/get-docker/ |
| Python | 3.12+ | https://python.org |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Bun | latest | `curl -fsSL https://bun.sh/install \| bash` |
| Git | any | — |

### 2. Clone

```bash
git clone https://github.com/richardnguyen0715/minoverse.git
cd minoverse
```

### 3. Start everything

```bash
make start
```

That's it. This one command handles the entire startup sequence:

| Step | What happens |
|---|---|
| ① | Docker Compose starts Postgres, Redis, NATS, Ollama |
| ② | Waits for Postgres to be healthy |
| ③ | `uv sync` — installs Python dependencies |
| ④ | `alembic upgrade head` — applies DB migrations |
| ⑤ | API server starts in background → `http://localhost:8000` |
| ⑥ | Waits for `/health` to respond |
| ⑦ | `minoverse index` — indexes all vault markdown files |
| ⑧ | Vault watcher starts in background (auto-indexes on save) |
| ⑨ | Dramatiq enrichment worker starts (AI jobs in background) |
| ⑩ | **Next.js web UI starts** → `http://localhost:3000` |

### 4. Stop everything

```bash
make stop
```

---

## AutoIngest CLI — Quick Start

The AutoIngest CLI (`apps/autoingest/`) is the primary interface for autonomous research and knowledge ingestion.

```bash
# Install
make ingest-install

# Configure LLM provider
cp apps/autoingest/.env.example apps/autoingest/.env
# Edit: choose Ollama (default), OpenAI, or Anthropic

# Analyze a URL
cd apps/autoingest
bun run src/index.ts analyze https://github.com/qdrant/qdrant

# Or via make
make ingest URL=https://github.com/qdrant/qdrant
```

**Example output:**
```
━━━ Analyzing https://github.com/qdrant/qdrant ━━━

  🔍 Mode: technical
  💾 Store in KB: true

  ⚙ scrape_url
    ✓ content extracted
  ⚙ extract_entities
    ✓ 12 entities found
  ⚙ summarize_technical
    ✓ summary generated
  ⚙ store_memory
    ✓ stored

━━━ Result ━━━

## Overview
Qdrant is a vector similarity search engine written in Rust...

  Entities: Qdrant [framework]  HNSW [algorithm]  Rust [language]
  steps: 6  entities: 12  memories stored: 1  duration: 4.2s
```

### Available CLI Commands

```bash
bun run src/index.ts analyze <url>            # Full pipeline
bun run src/index.ts analyze <url> --mode quick|technical|research
bun run src/index.ts research <topic>         # Multi-source research
bun run src/index.ts memory query <text>      # Search memory
bun run src/index.ts memory list              # Recent ingests
bun run src/index.ts memory graph <entity>    # Knowledge graph
bun run src/index.ts ingest <url|file|->      # Batch ingest
bun run src/index.ts health                   # System health
bun run src/index.ts tools                    # List all tools
```

---

## Telegram Bot — Quick Start

```bash
# 1. Create bot via @BotFather → copy token
# 2. Configure
cp apps/telegram/.env.example apps/telegram/.env
# Edit: TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USERS

# 3. Install + start
make telegram-install
make telegram

# Or with Docker (opt-in profile):
TELEGRAM_BOT_TOKEN=... docker compose --profile telegram up -d
```

**Bot commands:**
```
/analyze https://github.com/...   → Full analysis with streaming progress
/quick https://...                → Quick TLDR
/research RAG architectures 2024  → Deep research report
/memory vector databases          → Search knowledge base
/graph LangChain                  → Knowledge graph connections
/status                           → System health
```

---
Stops the watcher, API server, and all Docker services.

---

## Make Commands

```bash
# Core infrastructure
make start       # start everything (infra + API + watcher + worker + web UI)
make stop        # stop everything
make restart     # stop + start in one shot
make status      # show what is running
make logs-api    # tail API server log
make logs-watch  # tail vault watcher log
make logs-worker # tail enrichment worker log
make logs-web    # tail web UI log

# Web UI
make web-install # install web UI npm dependencies
make web-dev     # run web UI dev server (foreground)
make web-build   # build web UI for production
make web-test    # run web UI tests (Vitest)

# Vault
make index       # re-index vault manually
make worker      # start enrichment worker in foreground (dev mode)

# Database
make migrate     # apply pending DB migrations

# AutoIngest CLI (Phase AI)
make ingest-install           # bun install in apps/autoingest/
make ingest URL=https://...   # analyze a single URL
make research-topic TOPIC=... # deep multi-source research

# Telegram Bot (Phase AI)
make telegram-install  # uv sync in apps/telegram/
make telegram          # start Telegram bot (foreground)

# Scraping Service (Phase AI)
make scraping-install  # uv sync in services/scraping/
make scraping          # start scraping service on :8001

# Docker
make docker-up     # start all services (including scraping)
make docker-down   # stop all containers
make docker-logs   # stream all container logs

# Quality
make test        # run all tests (API pytest + web Vitest)
make lint        # ruff + mypy
make help        # list all commands
```

### `make status` output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Minoverse Status

  🟢 API server    http://localhost:8000   (PID 22146)
  🟢 Vault watcher running             (PID 22156)
  🟢 Enrich worker running             (PID 22167)

  Docker services:
    🟢 minoverse_ollama     Up 2 minutes
    🟢 minoverse_postgres   Up 2 minutes (healthy)
    🟢 minoverse_redis      Up 2 minutes (healthy)
    🟢 minoverse_nats       Up 2 minutes
    🟢 minoverse_scraping   Up 2 minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## CLI — Vault Operations (Phase 1)

The `minoverse` CLI is the primary tool for vault management. All commands run from `apps/api/`.

```bash
cd apps/api
uv run minoverse --help
```

### `minoverse index` — Index the Vault

Scans all `*.md` files and ingests them into the database. **Idempotent** — safe to re-run any time.

```bash
uv run minoverse index
# 📚 Indexing vault: .../vault
# ✅ Indexed 42/42 files

# Override vault path
uv run minoverse index --vault /path/to/other/vault
```

### `minoverse watch` — Live Watcher Daemon

Watches for filesystem changes and auto-ingests new/modified files. Soft-deletes removed files.

```bash
uv run minoverse watch
# 👁  Watching vault: .../vault  (Ctrl+C to stop)
```

### `minoverse graph` — Knowledge Graph Stats

```bash
uv run minoverse graph
# 📊 Knowledge Graph Stats
#    Vault files : 42
#    Resources   : 42
#    Notes       : 38
#    Wiki links  : 127
```

### Phase 2 Stubs

```bash
uv run minoverse rebuild   # Phase 2 — rebuild embeddings
uv run minoverse search "transformers attention"  # Phase 2 — hybrid search
```

---

## REST API Endpoints (Phase 1 + Phase 3 + Phase 4 + Phase 5)

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Redirect to `/docs` |
| `GET` | `/health` | `{"status":"ok","version":"0.1.0"}` |
| `GET` | `/knowledge/vault-files` | List indexed vault files |
| `GET` | `/knowledge/resources` | List resources (filter: `?resource_type=paper`) |
| `GET` | `/knowledge/resources/{id}` | Fetch single resource |
| `GET` | `/notes` | List notes (filter: `?note_type=daily_note`) |
| `GET` | `/notes/{id}` | Fetch single note with frontmatter |
| `GET` | `/notes/{id}/backlinks` | List all wiki links pointing to this note |
| `GET` | `/enrichment/{id}` | List all AI enrichments for a resource |
| `GET` | `/enrichment/{id}/{type}` | Get one enrichment type (`summary_concise`, `ai_tags`, etc.) |
| `POST` | `/enrichment/{id}/trigger` | Manually enqueue an AI enrichment job |
| `GET` | `/graph/full` | Full knowledge graph (all entities + relations) |
| `GET` | `/graph/resource/{id}` | Per-resource concept graph |
| `GET` | `/graph/entities` | List concept entities (filter: `?entity_type=technology`) |
| `GET` | `/graph/entities/{id}` | Get single concept entity |
| `GET` | `/graph/entities/{id}/neighbors` | Entity neighbor subgraph |
| `POST` | `/graph/resource/{id}/build` | Manually trigger graph build job |
| `POST` | **`/copilot/ask`** | **Ask the vault a question — returns sourced AI answer** |
| `POST` | **`/copilot/sessions`** | **Create a new memory session** |
| `GET` | **`/copilot/sessions`** | **List all memory sessions** |
| `GET` | **`/copilot/sessions/{id}`** | **Get session with full turn history** |
| `POST` | **`/copilot/sessions/{id}/distill`** | **Distill session into an episodic memory (AI)** |
| `GET` | **`/memory/episodes`** | **List episodic memories** |
| `GET` | **`/memory/episodes/{id}`** | **Get episodic memory** |
| `GET` | **`/memory/semantic`** | **List semantic memories** |
| `GET` | **`/memory/semantic/{id}`** | **Get semantic memory** |
| `POST` | **`/memory/extract/{resource_id}`** | **Extract semantic memory from a resource (AI)** |
| `GET` | **`/sync/events`** | **Paginated event log (filter: `?event_type=`, `?applied=`)** |
| `POST` | **`/sync/emit`** | **Manually emit a sync event** |
| `POST` | **`/sync/replay`** | **Replay unapplied events since a timestamp** |

---

## Services

| Service | URL | Notes |
|---|---|---|
| FastAPI | http://localhost:8000 | Started by `make start` |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| **Web UI** | **http://localhost:3000** | **Next.js — started by `make start`** |
| **Knowledge Graph** | **http://localhost:3000/graph** | **Phase 4 — interactive semantic graph** |
| **AI Copilot** | **http://localhost:3000/copilot** | **Phase 5 — ask your vault anything** |
| **Memory Browser** | **http://localhost:3000/memory** | **Phase 5 — episodic + semantic memories** |
| **Sync Event Log** | **http://localhost:3000/sync** | **Phase 6 — event audit log, replay, CRDT status** |
| Ollama | http://localhost:11434 | Local LLM runtime (optional — used when `AI_PROVIDER=ollama`) |
| LM Studio | http://localhost:1234 | Local LLM runtime (optional — used when `AI_PROVIDER=lmstudio`) |
| PostgreSQL | localhost:5432 | pgvector enabled |
| Redis | localhost:6379 | Job queue (Dramatiq) + event bus |

### Configure AI Provider (first time)

**Option A — Google Gemini (default, no GPU needed):**

```bash
# apps/api/.env
AI_PROVIDER=gemini
GEMINI_API_KEYS=AIzaSy_key1,AIzaSy_key2,...  # up to 5 keys, round-robin rotation
GEMINI_CHAT_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

Get free API keys at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
Full setup guide: [`docs/gemini-setup.md`](docs/gemini-setup.md).

**Option B — Ollama (local, no internet):**

```bash
# apps/api/.env
AI_PROVIDER=ollama

# Pull models first:
docker exec -it minoverse_ollama ollama pull bge-m3       # embedding model
docker exec -it minoverse_ollama ollama pull qwen3:0.6b   # chat model (522 MB)
```

**Option C — LM Studio (local, no internet):**

```bash
# apps/api/.env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234      # default port
LMSTUDIO_CHAT_MODEL=your-loaded-model-name   # must match model loaded in LM Studio
LMSTUDIO_EMBEDDING_MODEL=your-embedding-model
# LMSTUDIO_API_KEY=lms-...                   # optional, only if configured in LM Studio
```

1. Download [LM Studio](https://lmstudio.ai/) and load a chat model + embedding model.
2. Start the LM Studio server (default: `http://localhost:1234`).
3. Set the model names in `.env` to match what's loaded in LM Studio.

See [`docs/lmstudio-setup.md`](docs/lmstudio-setup.md) for details.

---

## AI Architecture

Minoverse uses a layered, provider-agnostic AI infrastructure under `apps/api/src/ai/`:

```
Skills (summarize / extract_entities / generate_tags / generate_relations)
    ↓
LLMRuntime  (prompt loading · model resolution · telemetry)
    ↓
PromptLoader (YAML files)   ModelRegistry (logical → physical models)
    ↓
LLMProvider Protocol  →  GeminiProvider (API key rotation, service account)
                      →  OllamaProvider (local, exponential-backoff retry)
                      →  LMStudioProvider (local, OpenAI-compatible API)
    ↓
Google Gemini API  —or—  Ollama local inference  —or—  LM Studio local inference
```

Key principles:
- **Provider-agnostic**: business logic only knows `LLMRuntime`; switch Gemini↔Ollama↔LMStudio via `AI_PROVIDER` env var
- **Config-driven**: model names resolved from `src/ai/configs/models.yaml` via `settings`
- **Prompts as files**: all prompts live in `src/ai/prompts/tasks/*.yaml`, never inlined in Python
- **Observable**: every AI call logs `ai_call` with prompt, version, model, provider, latency
- **Retryable**: Gemini rotates API keys on 429/quota; Ollama retries with exponential backoff; LMStudio retries with backoff

See [`docs/implementation-ai-standard.md`](docs/implementation-ai-standard.md) for full architecture details.
See [`docs/gemini-setup.md`](docs/gemini-setup.md) for Gemini API key and service account setup.

---

## Development Workflow

### Daily routine

```bash
make start    # morning — start everything
make stop     # evening — stop everything
```

### Create a new Alembic migration

```bash
cd apps/api
uv run alembic revision --autogenerate -m "describe your change"
uv run alembic upgrade head
```

### Roll back last migration

```bash
uv run alembic downgrade -1
```

---

## Testing

### Run all tests

```bash
make test
```

Or directly:

```bash
cd apps/api && uv run pytest src/ -v
```

### Run with coverage

```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Run a specific domain's tests

```bash
uv run pytest src/knowledge/tests/
uv run pytest src/retrieval/tests/
```

### Integration tests (requires running postgres + redis)

```bash
# Start infra first
cd infra && docker compose up -d postgres redis

# Run integration tests
cd ../apps/api
uv run pytest -m integration
```

### Coverage targets (per `.standards/coding-policies.md`)

| Layer | Minimum |
|---|---|
| Domain logic | 95% |
| Services | 90% |
| Pipelines | 90% |

---

## Static Analysis

### Run all quality gates

```bash
make lint
```

Or individually:

### Type checking (mypy strict)

```bash
cd apps/api
uv run mypy src/
```

### Linting (ruff)

```bash
uv run ruff check src/
uv run ruff format src/        # auto-format
```

### Run all quality gates

```bash
uv run ruff check src/ && uv run mypy src/ && uv run pytest
```

---

## Vault Usage

Your knowledge vault lives in `vault/`. It is the **canonical source of truth** — the database is only a projection.

### Vault File Format

```markdown
---
title: My Note Title
tags: [ai, research, transformers]
author: Jane Doe
url: https://example.com
aliases: [short-name, alt-title]
---

# My Note Title

Body content here. Link to other notes with [[wiki links]].
Use [[Note Name|Display Text]] for aliased links.
```

| Frontmatter key | Stored in |
|---|---|
| `title` | `resources.title` |
| `tags` | `tags` table (normalized, deduplicated) |
| `url` | `resources.url` |
| `author` | `resources.author` |
| `aliases` | `resources.extra_metadata.aliases` |
| Any other key | `notes.frontmatter` (JSONB) |

### Vault directory → Resource type mapping

| Path prefix | Resource type |
|---|---|
| `vault/resources/papers/` | `paper` |
| `vault/resources/youtube/` | `youtube_video` |
| `vault/resources/github/` | `github_repo` |
| `vault/resources/articles/` | `article` |
| `vault/resources/docs/` | `documentation` |
| `vault/resources/social/` | `tweet` |
| `vault/notes/` | `note` |
| `vault/concepts/` | `concept` |
| `vault/daily/` | `daily_note` |
| (anywhere else) | `note` (default) |

### Add a resource

Create a Markdown file in the appropriate folder:

```bash
# Example: save a paper
cat > vault/resources/papers/attention-is-all-you-need.md << 'EOF'
---
id: 550e8400-e29b-41d4-a716-446655440000
type: paper
tags:
  - transformers
  - attention
  - llm
url: https://arxiv.org/abs/1706.03762
author: Vaswani et al.
published_at: 2017-06-12
---

# Attention Is All You Need

The Transformer architecture introduced in this paper...
EOF
```

```bash
# Example: daily note
cat > vault/daily/$(date +%Y-%m-%d).md << 'EOF'
---
type: daily_note
---

# $(date +%Y-%m-%d)

## Today's focus
- ...
EOF
```

Then index it:

```bash
cd apps/api && uv run minoverse index
```

Or if the watcher is running (started by `make start`), just save the file — it auto-indexes.

### Supported resource types

```
paper          youtube_video    github_repo    article
documentation  tweet            note           concept          daily_note
```

---

## Event Bus Demo

The event bus is available via `packages/shared`. To test it manually:

```bash
# Terminal 1 — start a subscriber
cd apps/api
uv run python - << 'EOF'
import asyncio
import redis.asyncio as aioredis
import sys
sys.path.insert(0, "../../packages/shared/src")

from events.bus import subscribe_to_event
from events.types import EventType

async def main():
    client = aioredis.from_url("redis://localhost:6379/0")
    print("Listening for RESOURCE_CREATED events...")
    async for msg in subscribe_to_event(client, EventType.RESOURCE_CREATED):
        print("Received:", msg)

asyncio.run(main())
EOF
```

```bash
# Terminal 2 — publish a test event
cd apps/api
uv run python - << 'EOF'
import asyncio, uuid, sys
sys.path.insert(0, "../../packages/shared/src")
import redis.asyncio as aioredis
from events.bus import publish_event
from events.types import EventType
from events.payloads import ResourceCreatedPayload

async def main():
    client = aioredis.from_url("redis://localhost:6379/0")
    payload = ResourceCreatedPayload(
        resource_id=uuid.uuid4(),
        resource_type="paper",
        vault_file_path="vault/resources/papers/attention-is-all-you-need.md",
    )
    await publish_event(client, EventType.RESOURCE_CREATED, payload)
    print("Event published.")
    await client.aclose()

asyncio.run(main())
EOF
```

You should see the event appear in Terminal 1.

---

## Database Demo

Verify the schema was created correctly:

```bash
# Connect to postgres
docker exec -it minoverse_postgres psql -U minoverse -d minoverse

# List all tables
\dt

# Check pgvector is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

# Check chunk_embeddings column type
\d chunk_embeddings

# Exit
\q
```

Expected tables:

```
 vault_files         resources           resource_contents
 resource_chunks     chunk_embeddings    notes
 wiki_links          tags                resource_tags
 ingestion_jobs      ai_enrichments
 concept_entities    resource_entities   concept_relations
 memory_sessions     memory_turns
 episodic_memories   semantic_memories
 sync_events
```

---

## Implementation Phases

| Phase | Status | Description |
|---|---|---|
| **Phase 0** | ✅ Complete | Foundation: infra, DB schema, event bus |
| **Phase 1** | ✅ Complete | Knowledge Core: markdown parser, file watcher, CLI, vault indexing, wiki links |
| **Phase 3** | ✅ Complete | AI Enrichment: async job system, summaries, auto-tagging, entity extraction, related resources |
| **Web UI** | ✅ Complete | Next.js 15 UI: resource browser, viewer, notes, ⌘K palette, AI panel, React Flow graph |
| **Phase 4** | ✅ Complete | Knowledge Graph: concept entities, semantic relations, traversal engine, global graph UI |
| **AI Standard** | ✅ Complete | Layered AI infrastructure: LLMProvider/LLMRuntime/Prompts/Skills per `.standards/ai-llm-standard-architecture.md` |
| **Phase 5** | ✅ Complete | AI-native Workflows: conversational memory, episodic memory, semantic memory, AI copilot |
| **Phase 6** | ✅ Complete | Sync & Desktop: event sourcing, sync_events, replay, CRDT prep, Tauri v2 desktop scaffold |
| Phase 2 | Planned | Retrieval: hybrid BM25 + semantic + graph reranking |

Implementation records:
- [`docs/implemtentation-phase-0.md`](docs/implemtentation-phase-0.md) — Phase 0 full record
- [`docs/implementation-phase-1.md`](docs/implementation-phase-1.md) — Phase 1 full record
- [`docs/implementation-phase-3.md`](docs/implementation-phase-3.md) — Phase 3 full record
- [`docs/implementation-web.md`](docs/implementation-web.md) — Web UI full record
- [`docs/implementation-phase-4.md`](docs/implementation-phase-4.md) — Phase 4 full record
- [`docs/implementation-ai-standard.md`](docs/implementation-ai-standard.md) — AI Infrastructure Standard full record
- [`docs/implementation-phase-5.md`](docs/implementation-phase-5.md) — Phase 5 full record
- [`docs/implementation-phase-6.md`](docs/implementation-phase-6.md) — Phase 6 full record

Usage guides:
- [`docs/quick-start.md`](docs/quick-start.md) — **start here** (make start/stop/status)
- [`docs/phase-0-usage.md`](docs/phase-0-usage.md) — infrastructure detail
- [`docs/phase-1-usage.md`](docs/phase-1-usage.md) — CLI, API, demo, debugging
- [`docs/phase-3-usage.md`](docs/phase-3-usage.md) — AI enrichment, worker, demo
- [`docs/gemini-setup.md`](docs/gemini-setup.md) — **Gemini API keys, service account, key rotation**
- [`docs/lmstudio-setup.md`](docs/lmstudio-setup.md) — **LM Studio setup and model configuration**
- [`docs/web-usage.md`](docs/web-usage.md) — Web UI: pages, demo, testing, debugging
- [`docs/phase-4-usage.md`](docs/phase-4-usage.md) — Knowledge Graph: entities, relations, graph UI, debugging
- [`docs/ai-standard-usage.md`](docs/ai-standard-usage.md) — AI layer: swap models, add prompts, add skills, debug telemetry
- [`docs/phase-5-usage.md`](docs/phase-5-usage.md) — AI Copilot + Memory: ask vault, sessions, episodes, semantic
- [`docs/phase-6-usage.md`](docs/phase-6-usage.md) — Sync & Desktop: event log, replay, Tauri setup

---

## Engineering Standards

This project is governed by `.standards/`:

- `coding-policies.md` — code organization, typing, testing, error handling
- `database-design.md` — schema philosophy, table contracts
- `techstack-definitions.md` — technology choices and constraints
- `implementation-plan.md` — phase-by-phase roadmap

Key principles:
- **Markdown vault is canonical.** DB is a projection, never the source of truth.
- **Domain-organized code.** Not layer-organized. Each domain owns its entities, services, repos, schemas, events, and tests.
- **Strict typing everywhere.** `mypy strict` is enforced; `Any` is forbidden.
- **Event-driven by default.** Long-running operations are async, queued, retryable, and idempotent.
- **Structured logging always.** `structlog` only; `print()` is forbidden.

---

## Contributing

1. Read `.standards/coding-policies.md` before writing any code
2. Follow the commit format: `<type>(<scope>): <summary>` (e.g. `feat(retrieval): add hybrid reranking`)
3. All PRs must pass: `ruff` + `mypy` + `pytest` + coverage gates
4. No business logic in routes, workers, or ORM models

---

## License

Private — all rights reserved.

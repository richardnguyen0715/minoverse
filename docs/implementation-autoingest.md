# AutoIngest System — Implementation Record

> **Status:** Complete (Phase AI)
> **Completed:** 2026-05-13
> **Builds on:** Phases 0–6 (Foundation → Desktop/Sync)

---

## Overview

The AutoIngest phase transforms Minoverse from a vault-centric knowledge OS into a fully autonomous research and ingestion platform. It adds:

| Component | Location | Purpose |
|---|---|---|
| **AutoIngest CLI** | `apps/autoingest/` | TypeScript/Bun CLI — main interface, forked from OpenCode |
| **Telegram Bot** | `apps/telegram/` | Python bot for mobile/Telegram ingestion |
| **Scraping Service** | `services/scraping/` | Multi-source content extraction microservice |
| **Ingest API Routes** | `apps/api/src/ingest/` | `/ingest/url`, `/ingest/url/stream`, `/research/*` |
| **Mobile App Structure** | `apps/mobile/` | React Native/Expo skeleton for future expansion |

---

## Architecture

```
Telegram / Mobile / CLI (autoingest)
              ↓
    Ingestion Gateway
    POST /ingest/url
    POST /ingest/url/stream (SSE)
              ↓
    Event Queue (Redis / NATS)
              ↓
    Agent Runtime (autoingest)
    observe → plan → tool_call → reflect → store_memory
              ↓
    ┌─────────────────────────────────────┐
    │ Scraping Service (:8001)            │
    │  YouTubeScraper  GitHubScraper      │
    │  GenericScraper  (trafilatura)      │
    └─────────────────────────────────────┘
              ↓
    Summarization (Ollama / OpenAI / Anthropic)
              ↓
    PostgreSQL + pgvector + Neo4j (graph)
              ↓
    Notification (Telegram streaming)
```

---

## Component Details

### apps/autoingest/ — CLI Application

**Language:** TypeScript (Bun runtime)
**Based on:** OpenCode CLI patterns (execution loop, streaming, model abstraction)
**Removed from OpenCode:** filesystem assumptions, coding-only prompts, code editing flows
**Added:** research tools, knowledge tools, summarization tools, Minoverse API client

#### Key Files

| File | Purpose |
|---|---|
| `src/index.ts` | CLI entry point (yargs) |
| `src/agent/agent.ts` | Autonomous research agent loop |
| `src/provider/provider.ts` | LLM provider abstraction (Ollama/OpenAI/Anthropic) |
| `src/client/api.ts` | Typed Minoverse API client with SSE streaming |
| `src/tools/base.ts` | BaseTool interface + ToolRegistry |
| `src/tools/scrape.ts` | ScrapeUrlTool, ExtractArticleTool, ExtractVideoTool, ExtractRepoTool |
| `src/tools/research.ts` | SearchWebTool, FindRepoTool, SearchHackerNewsTool, SearchRedditTool |
| `src/tools/knowledge.ts` | ExtractEntitiesTool, QueryMemoryTool, StoreMemoryTool, BuildGraphTool |
| `src/tools/summarize.ts` | SummarizeShortTool, SummarizeTechnicalTool, SummarizeResearchTool |

#### CLI Commands

```
autoingest analyze <url>       # Full analysis pipeline
autoingest research <topic>    # Multi-source deep research
autoingest memory query <text> # Search memory
autoingest memory list         # List recent ingests
autoingest memory graph <ent>  # Knowledge graph context
autoingest ingest [url|file|-] # Batch ingest URLs
autoingest health              # Check system health
autoingest tools               # List all tools
```

#### Agent Loop

```
while not done:
  1. observe(task)
  2. retrieve_memory()      → query_memory tool
  3. plan() → stream LLM    → emit thinking tokens
  4. parse tool_call
  5. execute(tool, input)   → ToolRegistry.execute()
  6. feed result to LLM
  7. reflect()
  8. update_memory()        → store_memory tool
  repeat until <final_answer> tag
```

---

### apps/telegram/ — Telegram Bot

**Language:** Python 3.12
**Framework:** python-telegram-bot v21 (async)

#### Commands

| Command | Handler | Description |
|---|---|---|
| `/analyze <url>` | `analyze_handler` | Full pipeline with SSE streaming |
| `/quick <url>` | `quick_handler` | TLDR summary only |
| `/research <topic>` | `research_handler` | Deep research |
| `/memory <query>` | `memory_handler` | Search knowledge base |
| `/graph <entity>` | `graph_handler` | Knowledge graph context |
| `/update <url>` | `analyze_handler` | Re-analyze existing entry |
| `/status` | `status_handler` | System health check |
| `<bare url>` | `url_message_handler` | Auto-routes to analyze |

#### Auth

- Allowlist via `TELEGRAM_ALLOWED_USERS` env var (comma-separated user IDs)
- Empty = open access (NOT recommended for production)
- Get user ID from @userinfobot on Telegram

#### Deployment

- **Dev:** polling mode (no webhook needed)
- **Production:** webhook mode (`TELEGRAM_WEBHOOK_URL` set)
- Docker: `docker compose --profile telegram up -d`

---

### services/scraping/ — Scraping Service

**Language:** Python 3.12
**Framework:** FastAPI (separate microservice on :8001)

#### Source Adapters

| Adapter | Handles | Technology |
|---|---|---|
| `YouTubeScraper` | youtube.com, youtu.be | yt-dlp |
| `GitHubScraper` | github.com repos | GitHub REST API |
| `GenericScraper` | any web URL | trafilatura + BeautifulSoup |

#### Normalized Document Schema

All scrapers return `NormalizedDocument`:
```python
{
  "source_url": "...",
  "source_type": "youtube|github|article|...",
  "title": "...",
  "author": "...",
  "content": "...",  # main text/transcript
  "tags": [...],
  "metadata": {...},  # source-specific
  "scraped_at": "...",
}
```

---

### apps/api/src/ingest/ — Ingest API Routes

**New routes added to existing FastAPI:**

| Method | Path | Description |
|---|---|---|
| POST | `/ingest/url` | Ingest URL (sync) |
| POST | `/ingest/url/stream` | Ingest URL with SSE streaming |
| GET | `/ingest/recent` | List recent ingests |
| POST | `/research/search` | Multi-source web search |
| POST | `/research/find-repo` | GitHub repo discovery |

#### SSE Event Types (stream endpoint)

```
started → scraping → scraped → extracting_entities → entities_extracted
→ summarizing → summarized → storing → stored → graph_updated → completed
```

---

### apps/mobile/ — Mobile App Structure

**Framework:** React Native + Expo + Expo Router
**Status:** Directory structure + scaffolding only

```
apps/mobile/
├── src/
│   ├── app/           # Expo Router pages
│   │   └── (tabs)/    # Tab navigation
│   ├── screens/       # Screen components (stubs)
│   ├── services/      # API client
│   ├── store/         # Zustand state
│   ├── components/    # Shared components
│   └── hooks/         # Custom hooks
├── assets/            # Images, fonts
└── package.json
```

The mobile app is designed as a **thin client** — all processing happens in the cloud backend.

---

## Infrastructure Changes

### Docker Compose — New Services

| Service | Image | Port | Profile |
|---|---|---|---|
| `nats` | nats:2-alpine | 4222, 8222 | default |
| `scraping` | local build | 8001 | default |
| `telegram` | local build | — | `telegram` |

### Deployment Commands

```bash
# Start core stack
make docker-up

# Start with Telegram bot
make docker-up-telegram
# or: docker compose --profile telegram up -d

# View logs
make docker-logs
```

---

## Testing

### AutoIngest CLI

```bash
cd apps/autoingest
bun install
bun run src/index.ts health       # verify API connection
bun run src/index.ts analyze https://github.com/openai/openai-python
bun run src/index.ts research "vector database comparison 2024"
bun run src/index.ts memory query "RAG architecture"
```

### Telegram Bot

```bash
cd apps/telegram
cp .env.example .env  # fill in TELEGRAM_BOT_TOKEN
uv sync
uv run python -m src.main
```

### Scraping Service

```bash
cd services/scraping
uv sync
uv run uvicorn src.main:app --port 8001 --reload
# Test:
curl -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/openai/openai-python"}'
```

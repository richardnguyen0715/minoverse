# AutoIngest — Usage Guide

> Personal Autonomous Research & Knowledge CLI — practical examples

---

## Quick Start

```bash
# 1. Install CLI dependencies
make ingest-install

# 2. Configure (copy and edit)
cp apps/autoingest/.env.example apps/autoingest/.env

# 3. Start the backend
make start

# 4. Check health
make ingest-health
# ✓ Minoverse API: ok (v0.1.0)
#   ✓ redis: ok
#   ✓ ollama: ok
```

---

## CLI Reference

### Analyze a URL

```bash
# Technical analysis (default) — architecture, performance, use cases
autoingest analyze https://github.com/qdrant/qdrant

# Quick TLDR
autoingest analyze https://arxiv.org/abs/2312.10997 --mode quick

# Research depth — novelty, comparison, future directions
autoingest analyze https://huggingface.co/blog/rlhf --mode research

# Don't store in knowledge base
autoingest analyze https://example.com --no-store

# Skip agent, just use direct API
autoingest analyze https://example.com --no-stream
```

**Output example:**
```
━━━ Analyzing https://github.com/qdrant/qdrant ━━━

  🔍 Mode: technical
  💾 Store in KB: true
  🕸️ Update graph: true

  🕷️ Scraping content...
  ✓ Scraped                        (content extracted)
  🔬 Extracting entities...
  ✓ Entities extracted             (12 found)
  ✍️ Summarizing (technical mode)...
  ✓ Summary generated
  💾 Storing in knowledge base...
  ✓ Stored
  🕸️ Knowledge graph updated

━━━ Result ━━━

## Overview
Qdrant is a vector similarity search engine written in Rust...

## Architecture / Design
- Segment-based storage with HNSW indexing
- Supports filtering with payload conditions
...

  Entities discovered:
    · Qdrant [framework]
    · HNSW [algorithm]
    · Rust [language]

  duration: 4.2s  mode: technical
```

---

### Research a Topic

```bash
# Deep multi-source research
autoingest research "RAG architectures 2024"

# Quick research
autoingest research "vector database comparison" --depth quick

# Specific sources
autoingest research "LLM fine-tuning" --sources github,hackernews
```

**Output example:**
```
━━━ Research: RAG architectures 2024 ━━━

  📊 Depth: deep
  🌐 Sources: web, hackernews, github

  ⚙ search_hackernews   (query: RAG architectures 2024)
    ✓ 15 results
  ⚙ find_repo           (query: RAG python framework)
    ✓ 5 results
  ⚙ extract_entities
    ✓ 8 entities
  ⚙ store_memory
    ✓ ok

━━━ Result ━━━

## Problem Statement
RAG (Retrieval Augmented Generation) has evolved significantly in 2024...

## Key Findings
1. Advanced RAG introduces re-ranking and query decomposition...
2. Graph RAG from Microsoft Research uses knowledge graphs for retrieval...
...
```

---

### Memory Queries

```bash
# Search your knowledge base
autoingest memory query "vector database performance"

# List recent ingests
autoingest memory list

# List recent with limit
autoingest memory list --limit 20

# Knowledge graph for an entity
autoingest memory graph "LangChain"
```

---

### Batch Ingest

```bash
# Ingest a single URL
autoingest ingest https://arxiv.org/abs/2312.10997

# Ingest from a file (one URL per line)
autoingest ingest urls.txt

# Ingest from stdin
cat urls.txt | autoingest ingest -

# Watch a file for new URLs
autoingest ingest urls.txt --watch

# Batch with mode
autoingest ingest urls.txt --mode research
```

---

## Telegram Bot

### Setup

```bash
# 1. Create a bot via @BotFather on Telegram
#    Copy the token

# 2. Configure
cp apps/telegram/.env.example apps/telegram/.env
# Edit: TELEGRAM_BOT_TOKEN=your-token
#       TELEGRAM_ALLOWED_USERS=your-user-id

# 3. Get your Telegram user ID from @userinfobot

# 4. Start
make telegram
```

### Bot Commands

```
/analyze https://github.com/openai/openai-python
  → Full technical analysis with streaming progress

/analyze https://arxiv.org/abs/2312.10997 research
  → Research-depth analysis

/quick https://medium.com/some-article
  → Quick TLDR only

/research RAG architectures 2024
  → Multi-source research report

/memory vector database performance
  → Search your knowledge base

/graph LangChain
  → Explore knowledge graph connections

/status
  → Check all system components

Just send any URL and I'll analyze it automatically!
```

### Example Bot Session

```
You: https://github.com/qdrant/qdrant

Bot: ⏳ 🕷️ Scraping content...

     [after ~4s]

     🔧 *qdrant/qdrant*
     `github`

     Qdrant is a vector similarity search engine...

     🏷️ `vector-search`  `rust`  `similarity`

     🔬 *Entities:* Qdrant `[framework]`, HNSW `[algorithm]`, Rust `[language]`

     🔗 Source
     _Processed in 4234ms_
```

---

## Scraping Service API

The scraping service runs on port 8001 and can be used directly:

```bash
# Generic URL scrape
curl -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/openai/openai-python"}'

# Article extraction
curl -X POST http://localhost:8001/scrape/article \
  -H "Content-Type: application/json" \
  -d '{"url": "https://medium.com/some-article"}'

# YouTube video
curl -X POST http://localhost:8001/scrape/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "include_transcript": true}'

# GitHub repo
curl -X POST http://localhost:8001/scrape/repo \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/qdrant/qdrant"}'
```

---

## Ingest API (FastAPI)

```bash
# Sync ingest
curl -X POST http://localhost:8000/ingest/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/qdrant/qdrant", "mode": "technical"}'

# Streaming ingest (SSE)
curl -N -X POST http://localhost:8000/ingest/url/stream \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/qdrant/qdrant", "mode": "technical"}'

# Research search
curl -X POST http://localhost:8000/research/search \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG architectures 2024", "limit": 10}'

# Find GitHub repos
curl -X POST http://localhost:8000/research/find-repo \
  -H "Content-Type: application/json" \
  -d '{"query": "vector database rust", "min_stars": 1000, "limit": 5}'
```

---

## Configuration

### LLM Provider Selection

The AutoIngest CLI supports three providers:

| Provider | Speed | Quality | Cost | Setup |
|---|---|---|---|---|
| Ollama (default) | Fast | Good | Free | Local |
| OpenAI | Fast | Excellent | Paid | API key |
| Anthropic | Fast | Excellent | Paid | API key |

```bash
# In apps/autoingest/.env:

# Use Ollama (local, default)
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=llama3.2

# Use OpenAI
OPENAI_API_KEY=sk-...
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini

# Use Anthropic
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-5-haiku-20241022
```

---

## Docker Deployment

```bash
# Start core services (Postgres, Redis, NATS, Ollama, API, Worker, Scraping)
make docker-up

# Start with Telegram bot
make docker-up-telegram

# Stop everything
make docker-down

# View logs
make docker-logs

# Just API + infra (no ML services)
cd infra && docker compose up postgres redis api -d
```

---

## Extending with New Tools

Tools are plug-and-play. Add a new tool in `apps/autoingest/src/tools/`:

```typescript
// Example: PaperTool — extract from arXiv
import { BaseTool, type ToolInput, type ToolOutput, type ToolContext } from "./base"

export class ExtractPaperTool extends BaseTool<{ url: string }> {
  readonly name = "extract_paper"
  readonly description = "Extract a research paper from arXiv or similar"
  readonly inputSchema = {
    url: { type: "string" as const, description: "Paper URL", required: true },
  }

  async run(input: { url: string }, ctx: ToolContext): Promise<ToolOutput> {
    // implementation
    return { success: true, data: { ... } }
  }
}
```

Then register in `tools/index.ts`:

```typescript
import { ExtractPaperTool } from "./paper"
globalRegistry.register(new ExtractPaperTool())
```

The agent will automatically discover and use the new tool.

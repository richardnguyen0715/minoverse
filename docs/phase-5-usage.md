# Phase 5 — AI-native Workflows: Usage Guide

## Quick Start

1. **Start the stack**: `make start`
2. **Apply migrations**: `make migrate`
3. **Index vault**: `make index`
4. **Open copilot**: [http://localhost:3000/copilot](http://localhost:3000/copilot)
5. **Open memory browser**: [http://localhost:3000/memory](http://localhost:3000/memory)

---

## How It Works

```
User question
    ↓
POST /copilot/ask
    ↓
contextual_retrieval_service
  → ILIKE search across resource_contents + enrichment summaries
  → ranked [{resource_id, title, excerpt, score}]
    ↓
copilot_ask skill (LLMRuntime → Gemini / Ollama)
  → {answer, confidence, cited_resources}
    ↓
Save to memory_sessions + memory_turns
    ↓
AskResponse → UI
```

**Distillation (on demand):**
```
POST /copilot/sessions/{id}/distill
    ↓
Read all turns → format as conversation
    ↓
synthesize_episode skill → {title, content}
    ↓
Save to episodic_memories
```

**Semantic extraction (on demand):**
```
POST /memory/extract/{resource_id}
    ↓
Read resource content / summary
    ↓
synthesize_semantic skill → {concept, content}
    ↓
Save to semantic_memories
```

---

## API Reference

All endpoints: `http://localhost:8000`

### Copilot

#### Ask the vault
```
POST /copilot/ask
Content-Type: application/json

{
  "question": "What is the difference between RAG and fine-tuning?",
  "session_id": null        ← optional: provide to continue an existing session
}
```

Response:
```json
{
  "answer": "RAG retrieves external context at inference time...",
  "sources": [
    {"resource_id": "...", "title": "Attention Is All You Need", "excerpt": "..."}
  ],
  "session_id": "...",
  "turn_id": "..."
}
```

#### Create a session
```
POST /copilot/sessions
{"title": "Research on embeddings"}
```

#### List sessions
```
GET /copilot/sessions
```

#### Get session with full history
```
GET /copilot/sessions/{session_id}
```

Response includes `turns` array with all user/assistant turns.

#### Distill session to episodic memory
```
POST /copilot/sessions/{session_id}/distill
```

Calls the AI to summarise the session and saves an `EpisodicMemory`.

---

### Memory

#### List episodic memories
```
GET /memory/episodes
```

#### Get episode
```
GET /memory/episodes/{episode_id}
```

#### List semantic memories
```
GET /memory/semantic
```

#### Get semantic memory
```
GET /memory/semantic/{memory_id}
```

#### Extract semantic memory from a resource
```
POST /memory/extract/{resource_id}
```

Extracts the most reusable knowledge concept from the resource's content/summary.

---

## Web UI

### Copilot page — [http://localhost:3000/copilot](http://localhost:3000/copilot)

- **Question input** — type any question about your vault
- **Session selector** — continue an existing session or start a new one
- **Answer panel** — AI response with confidence level badge (`high / medium / low`)
- **Sources** — the vault resources that informed the answer (title + excerpt)

### Memory page — [http://localhost:3000/memory](http://localhost:3000/memory)

- **Episodes tab** — AI-distilled research sessions; click to expand full content
- **Semantic tab** — durable knowledge concepts; click to expand

---

## Demo Steps

1. Add a few markdown files to `vault/resources/papers/`.
2. Run `make index` to ingest them.
3. Wait for the enrichment worker to extract entities and summaries (`make logs-worker`).
4. Go to [http://localhost:3000/copilot](http://localhost:3000/copilot).
5. Ask: *"What are the main ideas in my papers about transformers?"*
6. You'll get an AI answer with cited resources from your vault.
7. After a few turns, click **Distill Session** to save an episodic memory.
8. Visit [http://localhost:3000/memory](http://localhost:3000/memory) to browse all memories.

---

## Debugging

**No answer / empty sources:**
- Ensure enrichment worker ran (`make logs-worker`) — contextual retrieval uses `clean_text` from `resource_contents` and AI enrichment summaries
- Check `POST /copilot/ask` response for error details
- Verify `AI_PROVIDER` env var is set correctly in `apps/api/.env`

**AI returns empty answer:**
- Tail the worker/API log: `make logs-api`
- If using Gemini: check quota (see `fixed-issues/011-gemini-free-tier-quota-exhausted.md`)
- If using Ollama: verify it is reachable: `curl http://localhost:11434/api/tags`

**Distill session fails:**
- Session must have at least 1 turn
- The AI call goes through `synthesize_episode` prompt — same provider requirements apply

**Re-run extraction manually:**
```bash
curl -X POST http://localhost:8000/memory/extract/{resource_id}
```

---

## Contextual Retrieval Notes

Phase 5 uses **keyword-based retrieval** (ILIKE search on `resource_contents.clean_text`):
- Query is split into words (≥4 chars) and each is searched independently
- Resources are ranked by number of matching words
- Short words and stop-words are filtered

**Phase 2** (planned) will replace this with full pgvector hybrid retrieval (BM25 + semantic + graph scores). The `copilot_service` already accepts the retrieval results as a list of dicts, so the swap will be transparent to the copilot layer.

# Phase 3 — AI Enrichment: Usage Guide

> **Prerequisites:** Phase 0 and Phase 1 are running (Postgres, Redis, Ollama, API server).  
> The simplest way to start everything is `make start` from the repo root.  
> See [`docs/quick-start.md`](./quick-start.md) if the stack is not yet running.

---

## Quick Reference

| Task | Command |
|---|---|
| Start everything (incl. worker) | `make start` |
| Stop everything | `make stop` |
| Apply Phase 3 migration | `cd apps/api && uv run alembic upgrade head` |
| Tail enrichment worker log | `make logs-worker` |
| Manually trigger enrichment | `curl -X POST http://localhost:8000/enrichment/{resource_id}/trigger` |
| List enrichments for a resource | `curl http://localhost:8000/enrichment/{resource_id}` |
| Get one enrichment type | `curl http://localhost:8000/enrichment/{resource_id}/summary_concise` |
| Run Phase 3 tests | `cd apps/api && uv run pytest src/enrichment/tests/ -v` |
| Run all tests | `make test` |

---

## 1. First-Time Setup

### 1.1 Install Ollama Models

Phase 3 requires two Ollama models. Pull them once after `make start` brings Ollama up:

```bash
# Pull the chat model (used for summaries, tagging, entity extraction)
docker exec -it minoverse_ollama ollama pull qwen3

# Pull the embedding model (used in Phase 2 — pull now for future use)
docker exec -it minoverse_ollama ollama pull bge-m3
```

Verify models are loaded:

```bash
docker exec -it minoverse_ollama ollama list
# NAME          ID            SIZE    MODIFIED
# qwen3:latest  ...           4.7 GB  ...
# bge-m3:latest ...           1.2 GB  ...
```

### 1.2 Apply the Migration

Migration `003` creates the `ai_enrichments` table. Run it once:

```bash
cd apps/api
uv run alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003, add ai_enrichments table
```

Verify:
```bash
uv run alembic current
# 003 (head)
```

### 1.3 Install Phase 3 Dependencies

```bash
cd apps/api
uv sync
```

This installs `ollama>=0.4.0` and `httpx>=0.27`.

---

## 2. Start the Full Stack

From the repo root:

```bash
make start
```

`make start` now includes a **9th step** that starts the Dramatiq enrichment worker:

| Step | What happens |
|---|---|
| ① | Docker Compose starts Postgres, Redis, Ollama |
| ② | Waits for Postgres to be healthy |
| ③ | `uv sync` — installs Python dependencies |
| ④ | `alembic upgrade head` — applies DB migrations |
| ⑤ | API server starts → `http://localhost:8000` |
| ⑥ | Waits for `/health` to respond |
| ⑦ | `minoverse index` — indexes all vault files |
| ⑧ | Vault watcher starts (auto-indexes on save) |
| **⑨** | **Dramatiq enrichment worker starts** → `.minoverse/worker.log` |

Stop everything with:
```bash
make stop
```

---

## 3. How Enrichment Works

### Automatic Enrichment

Every time a vault file is ingested (on `minoverse index` or when the watcher detects a change), the ingestion service **automatically enqueues an enrichment job** after committing to the database:

```
Vault file saved / created
  → watchfiles detects change
  → ingest_vault_file() runs
  → vault_files + resources + notes committed
  → enrich_resource.send(resource_id)   ← Dramatiq job enqueued
  → enrichment worker picks up the job
  → run_enrichment_for_resource() runs all 4 steps
  → ai_enrichments rows upserted
```

### Enrichment Types

Each resource gets up to 6 enrichment records, one per type:

| Enrichment type | Content shape | Description |
|---|---|---|
| `summary_concise` | `{"text": "..."}` | 2–3 sentence overview |
| `summary_detailed` | `{"text": "..."}` | Comprehensive paragraph |
| `key_insights` | `{"items": ["...", "..."]}` | Bullet-point insights |
| `ai_tags` | `{"tags": ["...", "..."]}` | Up to 10 auto-generated tags |
| `entities` | `{"tools": [], "frameworks": [], "papers": [], "methodologies": []}` | Named entity extraction |
| `related` | `{"resource_ids": ["...", "..."]}` | Related resource UUIDs |

### Graceful Degradation

| Failure scenario | Outcome |
|---|---|
| Ollama is not running | Enrichment job skipped, logged as warning. Ingestion still succeeds. |
| Ollama returns unparseable JSON | That specific step degrades gracefully; other steps still run. |
| Redis is down during ingestion | Job not enqueued. Ingestion still succeeds. Use manual trigger later. |
| Worker crashes mid-job | Dramatiq retries up to 3 times with 5-second backoff. |

---

## 4. Monitoring and Logs

### Check Status

```bash
make status
```

Output includes the enrichment worker:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Minoverse Status

  🟢 API server      http://localhost:8000   (PID 1234)
  🟢 Vault watcher   running                 (PID 1235)
  🟢 Enrich worker   running                 (PID 1236)

  Docker services:
    🟢 minoverse_ollama     Up 2 minutes
    🟢 minoverse_postgres   Up 2 minutes (healthy)
    🟢 minoverse_redis      Up 2 minutes (healthy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Tail Worker Logs

```bash
make logs-worker
```

What to look for when a job succeeds:
```
2026-05-09 23:00:01 [info] enrichment_job_enqueued  resource_id=abc-123
2026-05-09 23:00:04 [info] summary_enrichment_done  resource_id=abc-123  ms=2840
2026-05-09 23:00:06 [info] tagging_enrichment_done  resource_id=abc-123  ms=1650
2026-05-09 23:00:09 [info] entity_enrichment_done   resource_id=abc-123  ms=2910
2026-05-09 23:00:09 [info] related_enrichment_done  resource_id=abc-123  ms=3
2026-05-09 23:00:09 [info] enrichment_worker_completed  resource_id=abc-123
    succeeded=['summary_concise','summary_detailed','key_insights','ai_tags','entities','related']
    failed=[]  skipped_ollama_unavailable=false
```

What to look for when Ollama is unavailable:
```
2026-05-09 23:00:01 [warning] ollama_unavailable_skipping_enrichment  resource_id=abc-123
```

---

## 5. REST API — Enrichment Endpoints

The API server must be running. Interactive docs: http://localhost:8000/docs

### List All Enrichments for a Resource

```bash
curl http://localhost:8000/enrichment/{resource_id} | python3 -m json.tool
```

```json
[
  {
    "resource_id": "550e8400-e29b-41d4-a716-446655440000",
    "enrichment_type": "summary_concise",
    "content": {"text": "This paper introduces the Transformer architecture..."},
    "model_name": "qwen3",
    "prompt_version": "v1",
    "processing_ms": 2840
  },
  {
    "resource_id": "550e8400-e29b-41d4-a716-446655440000",
    "enrichment_type": "ai_tags",
    "content": {"tags": ["transformers", "attention", "nlp", "deep learning"]},
    "model_name": "qwen3",
    "prompt_version": "v1",
    "processing_ms": 1650
  }
]
```

### Get a Specific Enrichment Type

```bash
# Get concise summary
curl http://localhost:8000/enrichment/{resource_id}/summary_concise

# Get AI tags
curl http://localhost:8000/enrichment/{resource_id}/ai_tags

# Get extracted entities
curl http://localhost:8000/enrichment/{resource_id}/entities

# Get related resources
curl http://localhost:8000/enrichment/{resource_id}/related
```

Valid `enrichment_type` values: `summary_concise`, `summary_detailed`, `key_insights`, `ai_tags`, `entities`, `related`.

Returns `404` if the enrichment for that type has not been generated yet.

### Manually Trigger Enrichment

If a resource was indexed before the worker was running, or if you want to re-run enrichment:

```bash
curl -X POST http://localhost:8000/enrichment/{resource_id}/trigger
```

```json
{"status": "queued", "resource_id": "550e8400-e29b-41d4-a716-446655440000"}
```

The job is enqueued in Redis and picked up by the worker within seconds.

---

## 6. End-to-End Demo

This demo creates a vault note, indexes it, waits for enrichment, and reads the results.

**Step 1: Start the full stack**
```bash
make start
```

**Step 2: Pull Ollama models (first time only)**
```bash
docker exec -it minoverse_ollama ollama pull qwen3
```

**Step 3: Create a sample note**
```bash
cat > vault/resources/papers/attention-is-all-you-need.md << 'EOF'
---
title: Attention Is All You Need
tags: [transformers, attention, nlp, deep-learning]
author: Vaswani et al.
url: https://arxiv.org/abs/1706.03762
---

# Attention Is All You Need

The Transformer architecture, introduced in this paper, relies solely on
attention mechanisms, dispensing with recurrence and convolutions entirely.

Key contributions:
- Multi-head self-attention mechanism
- Positional encoding scheme
- Encoder-decoder architecture without RNNs

Used in: PyTorch, TensorFlow, HuggingFace Transformers, BERT, GPT.

See also: [[BERT - Pre-training of Deep Bidirectional Transformers]]
EOF
```

**Step 4: Index the vault (or wait — watcher auto-detects the new file)**
```bash
make index
# 📚 Indexing vault: .../vault
# ✅ Indexed X/X files
```

Check the API log for the enqueued job:
```bash
make logs-api | grep enrichment_job_enqueued
```

**Step 5: Watch the worker process the job**
```bash
make logs-worker
# 2026-05-09 23:00:04 [info] summary_enrichment_done  ms=3120
# 2026-05-09 23:00:06 [info] tagging_enrichment_done  ms=1440
# 2026-05-09 23:00:09 [info] entity_enrichment_done   ms=2980
# 2026-05-09 23:00:09 [info] enrichment_worker_completed  succeeded=[...]  failed=[]
```

**Step 6: Find the resource ID**
```bash
curl -s "http://localhost:8000/knowledge/resources?resource_type=paper" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    if 'Attention' in (r.get('title') or ''):
        print(r['id'])
"
# 550e8400-e29b-41d4-a716-446655440000
```

**Step 7: Read the enrichments**
```bash
RESOURCE_ID=550e8400-e29b-41d4-a716-446655440000

# Concise summary
curl -s http://localhost:8000/enrichment/$RESOURCE_ID/summary_concise \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['content']['text'])"

# AI tags
curl -s http://localhost:8000/enrichment/$RESOURCE_ID/ai_tags \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['content']['tags'])"

# Entities
curl -s http://localhost:8000/enrichment/$RESOURCE_ID/entities \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d['content'], indent=2))"
```

Expected entity output:
```json
{
  "tools": ["PyTorch", "TensorFlow", "HuggingFace Transformers"],
  "frameworks": ["BERT", "GPT"],
  "papers": ["Attention Is All You Need"],
  "methodologies": ["multi-head self-attention", "positional encoding"]
}
```

---

## 7. Running Tests

```bash
# Phase 3 tests only
cd apps/api
uv run pytest src/enrichment/tests/ -v
```

Expected output:
```
collected 11 items

src/enrichment/tests/test_enrichment_pipeline.py::test_pipeline_skips_when_ollama_unavailable PASSED
src/enrichment/tests/test_enrichment_pipeline.py::test_pipeline_continues_when_one_step_fails PASSED
src/enrichment/tests/test_enrichment_pipeline.py::test_pipeline_is_idempotent PASSED
src/enrichment/tests/test_entity_service.py::test_extract_entities_returns_structured_result PASSED
src/enrichment/tests/test_entity_service.py::test_extract_entities_handles_missing_keys PASSED
src/enrichment/tests/test_summary_service.py::test_generate_summary_returns_parsed_result PASSED
src/enrichment/tests/test_summary_service.py::test_generate_summary_handles_malformed_json PASSED
src/enrichment/tests/test_summary_service.py::test_generate_summary_handles_ollama_unavailable PASSED
src/enrichment/tests/test_tagging_service.py::test_generate_ai_tags_normalizes_output PASSED
src/enrichment/tests/test_tagging_service.py::test_generate_ai_tags_respects_max_tags PASSED
src/enrichment/tests/test_tagging_service.py::test_generate_ai_tags_handles_empty_response PASSED

11 passed in 0.30s
```

Run all tests across all phases:
```bash
make test
# 30 passed in 0.27s
```

---

## 8. Debugging

### Database: Inspect Enrichment Data

```bash
docker exec -it minoverse_postgres psql -U minoverse -d minoverse
```

```sql
-- Check which resources have been enriched
SELECT r.title, ae.enrichment_type, ae.model_name, ae.processing_ms, ae.updated_at
FROM ai_enrichments ae
JOIN resources r ON r.id = ae.resource_id
ORDER BY ae.updated_at DESC
LIMIT 20;

-- Check enrichment content for one resource
SELECT enrichment_type, content
FROM ai_enrichments
WHERE resource_id = 'your-resource-uuid-here'
ORDER BY enrichment_type;

-- Check pending enrichments (resources without any enrichment)
SELECT r.id, r.title, r.resource_type
FROM resources r
WHERE r.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM ai_enrichments ae WHERE ae.resource_id = r.id
  )
LIMIT 20;
```

### Worker Not Processing Jobs

1. Check the worker is running:
   ```bash
   make status
   ```

2. Check the worker log for errors:
   ```bash
   make logs-worker | tail -50
   ```

3. Check Redis has queued messages:
   ```bash
   docker exec -it minoverse_redis redis-cli LLEN dramatiq:default
   ```

4. Restart just the worker:
   ```bash
   # Stop and restart everything
   make restart
   
   # Or start just the worker in foreground for debugging
   cd apps/api && .venv/bin/python -m dramatiq src.enrichment.workers.enrichment_worker
   ```

### Ollama Not Generating Good Results

Check Ollama is healthy and the model is loaded:
```bash
# Check service status
curl http://localhost:11434/api/tags | python3 -m json.tool

# Test generation manually
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "qwen3", "prompt": "Hello", "stream": false}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['response'])"
```

If the model is not listed:
```bash
docker exec -it minoverse_ollama ollama pull qwen3
```

### Re-enrich All Resources

To re-run enrichment for every resource (e.g., after updating prompts or switching models):

```bash
# Get all resource IDs and trigger enrichment for each
curl -s http://localhost:8000/knowledge/resources \
  | python3 -c "
import sys, json, subprocess
for r in json.load(sys.stdin):
    subprocess.run([
        'curl', '-s', '-X', 'POST',
        f'http://localhost:8000/enrichment/{r[\"id\"]}/trigger'
    ])
    print(f'Queued: {r[\"title\"]}')
"
```

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| Worker exits immediately after start | Redis not running | `make status` → check Redis; `make restart` |
| `OllamaUnavailableError` in logs | Ollama container not started or model not pulled | `docker exec -it minoverse_ollama ollama list` |
| `404` on enrichment endpoint | Enrichment not generated yet | Check worker logs; use `/trigger` endpoint |
| `column "..." does not exist` in worker | Migration not applied | `cd apps/api && uv run alembic upgrade head` |
| JSON parse errors in worker log | LLM returned non-JSON text | Normal — services degrade gracefully; check prompt version |

---

## 9. Environment Variables

All Phase 3 behavior is controlled via `apps/api/.env`:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service URL |
| `CHAT_MODEL` | `qwen3` | Model used for summaries, tagging, entity extraction |
| `EMBEDDING_MODEL` | `bge-m3` | Embedding model (Phase 2) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Dramatiq job queue |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Postgres connection |

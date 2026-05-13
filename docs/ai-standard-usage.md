# AI Infrastructure Standard — Usage Guide

This guide covers day-to-day usage of the layered AI infrastructure in `apps/api/src/ai/`.

---

## Architecture Overview

```
Skills (run_summarize / run_extract_entities / run_generate_tags / run_generate_relations)
    ↓
LLMRuntime  (prompt loading · model resolution · telemetry)
    ↓
PromptLoader (YAML files)     ModelRegistry (logical → physical models)
    ↓
LLMProvider Protocol  →  OllamaProvider (with exponential-backoff retry)
    ↓
Ollama local inference (qwen3:0.6b, bge-m3)
```

---

## 1. Setup — Pull Required Models

Before first use, pull the Ollama models used by the registry:

```bash
docker exec -it minoverse_ollama ollama pull qwen3:0.6b   # 522 MB — chat/reasoning
docker exec -it minoverse_ollama ollama pull bge-m3        # embedding model
```

Verify:

```bash
docker exec -it minoverse_ollama ollama list
# NAME           ID              SIZE      MODIFIED
# qwen3:0.6b     7df6b6e09427    522 MB    ...
# bge-m3         ...             ...       ...
```

---

## 2. Configuration — Changing Models

Model names are **never hardcoded**. Change them in `apps/api/.env`:

```bash
# apps/api/.env
CHAT_MODEL=qwen3:0.6b        # or qwen3:7b, llama3.2:3b, etc.
EMBEDDING_MODEL=bge-m3
OLLAMA_BASE_URL=http://localhost:11434
```

The model registry (`src/ai/configs/models.yaml`) resolves these at runtime:

```yaml
models:
  chat_model:
    provider: ollama
    physical_model: "${CHAT_MODEL}"   # ← resolved from .env
    temperature: 0.3
    max_tokens: 2048
  embedding_model:
    provider: ollama
    physical_model: "${EMBEDDING_MODEL}"
```

After changing `.env`, restart the API and worker:

```bash
make restart
```

---

## 3. Observing AI Calls

Every AI call logs a structured `ai_call` event. View live:

```bash
make logs-api
# ...
# 2026-05-10 02:00:00 [info] ai_call  prompt=summarize  prompt_version=v1  model=qwen3:0.6b  provider=ollama  latency_ms=7671  success=True
# 2026-05-10 02:00:08 [info] ai_call  prompt=generate_tags  prompt_version=v1  model=qwen3:0.6b  provider=ollama  latency_ms=3840  success=True
```

Or for the enrichment worker:

```bash
make logs-worker
```

---

## 4. Triggering AI Enrichment Manually

```bash
# Get resource IDs
curl -s http://localhost:8000/knowledge/resources | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    print(r['id'], r['title'])
"

# Trigger enrichment for a specific resource
RESOURCE_ID="c8bf5bdb-6119-4d12-8c10-1128fa21ddd5"
curl -s -X POST http://localhost:8000/enrichment/$RESOURCE_ID/trigger

# Check enrichment results
curl -s http://localhost:8000/enrichment/$RESOURCE_ID | python3 -c "
import sys, json
for e in json.load(sys.stdin):
    print(e['enrichment_type'], '->', json.dumps(e['content'])[:100])
"
```

---

## 5. Triggering Graph Build Manually

After enrichment completes, build the knowledge graph:

```bash
RESOURCE_ID="c8bf5bdb-6119-4d12-8c10-1128fa21ddd5"
curl -s -X POST http://localhost:8000/graph/resource/$RESOURCE_ID/build

# Check graph
curl -s http://localhost:8000/graph/full | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Nodes:', len(d['nodes']))
print('Edges:', len(d['edges']))
for n in d['nodes']:
    print(' -', n['name'], '(', n['entity_type'], ')')
"
```

---

## 6. Re-indexing All Resources

After pulling new notes or changing content:

```bash
make index
# Triggers indexing → enrichment → graph build for all vault files
```

Or using the CLI directly from `apps/api/`:

```bash
cd apps/api
uv run minoverse index
```

---

## 7. Swapping to a Different LLM

To use a different model (e.g. a larger qwen3 or a different provider's local model):

```bash
# 1. Pull the model
docker exec -it minoverse_ollama ollama pull qwen3:7b

# 2. Update .env
echo "CHAT_MODEL=qwen3:7b" >> apps/api/.env

# 3. Restart
make restart

# 4. Re-trigger enrichment to regenerate with new model
curl -s -X POST http://localhost:8000/enrichment/<RESOURCE_ID>/trigger
```

---

## 8. Adding a New Prompt

1. Create a YAML file in `apps/api/src/ai/prompts/tasks/`:

```yaml
# apps/api/src/ai/prompts/tasks/my_new_prompt.yaml
name: my_new_prompt
version: v1
system: |
  You are a helpful assistant. Return only valid JSON.
user_template: |
  Do something with this content:

  {content}
temperature: 0.3
max_tokens: 512
```

2. Create a skill in `apps/api/src/ai/skills/`:

```python
# apps/api/src/ai/skills/my_new_skill.py
import json
import structlog
from src.ai.runtimes.llm_runtime import LLMRuntime

logger = structlog.get_logger(__name__)

async def run_my_new_skill(content: str, runtime: LLMRuntime) -> dict:
    try:
        response = await runtime.run_skill(
            prompt_name="my_new_prompt",
            logical_model="chat_model",
            render_kwargs={"content": content[:4000]},
        )
        return json.loads(response)
    except Exception as exc:
        logger.warning("my_new_skill_failed", error=str(exc))
        return {}
```

3. Use it anywhere by building a runtime:

```python
from src.ai import get_llm_runtime
from src.ai.skills.my_new_skill import run_my_new_skill

runtime = get_llm_runtime()
result = await run_my_new_skill("some content", runtime)
```

---

## 9. Testing the AI Layer

```bash
cd apps/api

# Run all AI infrastructure tests
uv run pytest src/ai/tests/ -v

# Run all tests
uv run pytest src/ -x -q
# 54 passed
```

Test files:
- `src/ai/tests/test_llm_runtime.py` — runtime dispatch, telemetry
- `src/ai/tests/test_prompt_loader.py` — YAML loading, rendering
- `src/ai/tests/test_ollama_provider.py` — availability, thinking traces, retry

---

## 10. Debugging

### Model not responding

```bash
# Check Ollama is up
curl http://localhost:11434/api/tags

# Verify model is pulled
docker exec -it minoverse_ollama ollama list

# Test model directly
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen3:0.6b","prompt":"Say hello","stream":false}' | python3 -c "
import sys, json; print(json.load(sys.stdin)['response'][:100])"
```

### Enrichment returns empty

Common causes (see `.issues/`):

| Symptom | Cause | Fix |
|---|---|---|
| `{"tags": [], "text": ""}` | Model not pulled | `ollama pull qwen3:0.6b` |
| `ActorNotFound: enrich_resource` | Dual broker bug | Restart worker with `make restart` |
| JSON parse error | Thinking traces | Already fixed: `strip_thinking()` in provider |
| `empty_entities_list` debug log | Schema mismatch | Fixed in `entity_promotion_service.py` |

### Telemetry shows failures

```bash
# Check worker logs for ai_call events with success=False
make logs-worker | grep "ai_call"
# or
make logs-api | grep "ai_call"
```

---

## 11. Key Files Reference

| File | Purpose |
|---|---|
| `src/ai/__init__.py` | `get_llm_runtime()` factory |
| `src/ai/providers/base.py` | `LLMProvider` Protocol |
| `src/ai/providers/ollama.py` | `OllamaProvider` with retry + `strip_thinking()` |
| `src/ai/runtimes/llm_runtime.py` | `LLMRuntime` — central execution layer |
| `src/ai/models/registry.py` | `ModelRegistry` logical→physical mapping |
| `src/ai/prompts/loader.py` | `PromptLoader` YAML reader |
| `src/ai/prompts/tasks/*.yaml` | Versioned prompt files |
| `src/ai/skills/*.py` | Skill executors |
| `src/ai/configs/models.yaml` | Model registry config |
| `apps/api/.env` | `CHAT_MODEL`, `EMBEDDING_MODEL` values |

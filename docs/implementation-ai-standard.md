# AI Infrastructure Standard — Implementation Guide

## Overview

This document describes the layered AI infrastructure implemented in `apps/api/src/ai/`, following the principles in `.standards/ai-llm-standard-architecture.md`.

---

## Architecture Diagram

```
Application (enrichment services, workers)
    ↓
Skills (run_summarize, run_extract_entities, run_generate_tags, run_generate_relations)
    ↓
LLMRuntime (prompt loading + provider dispatch + telemetry)
    ↓
PromptLoader (YAML files from src/ai/prompts/tasks/)
ModelRegistry (logical → physical model mapping)
    ↓
LLMProvider Protocol (provider-agnostic interface)
    ↓
OllamaProvider (concrete implementation with retry logic)
    ↓
Ollama local inference (qwen3, bge-m3)
```

---

## Directory Structure

```
apps/api/src/ai/
├── __init__.py                  # get_llm_runtime() convenience factory
├── providers/
│   ├── base.py                  # LLMProvider Protocol (runtime_checkable)
│   └── ollama.py                # OllamaProvider with tenacity retries
├── models/
│   └── registry.py              # ModelRegistry: logical → physical model
├── prompts/
│   ├── loader.py                # PromptLoader: YAML → PromptTemplate
│   └── tasks/
│       ├── summarize.yaml
│       ├── extract_entities.yaml
│       ├── generate_tags.yaml
│       └── generate_relations.yaml
├── runtimes/
│   └── llm_runtime.py           # LLMRuntime: orchestrates all layers
├── skills/
│   ├── summarize_resource.py    # run_summarize()
│   ├── extract_entities.py      # run_extract_entities()
│   ├── generate_tags.py         # run_generate_tags()
│   └── generate_relations.py    # run_generate_relations()
├── configs/
│   └── models.yaml              # Model registry config (resolved from settings)
└── tests/
    ├── test_llm_runtime.py
    ├── test_prompt_loader.py
    └── test_ollama_provider.py
```

---

## Key Principles Implemented

### 1. Provider-Agnostic
The application only imports `LLMProvider` (Protocol) or `LLMRuntime`. No business logic directly references `OllamaProvider`, the `ollama` SDK, or any model names.

### 2. Config-Driven
Model names are never hardcoded in business logic. `models.yaml` maps logical names to physical models:

```yaml
models:
  chat_model:
    provider: ollama
    physical_model: "${CHAT_MODEL}"   # resolved from settings.chat_model at load time
    temperature: 0.3
    max_tokens: 2048
  embedding_model:
    provider: ollama
    physical_model: "${EMBEDDING_MODEL}"
    temperature: 0.0
    max_tokens: 512
```

Usage in code:
```python
await runtime.run_skill(prompt_name="summarize", logical_model="chat_model", ...)
```

### 3. Prompts as Files
All prompt strings live in YAML files under `src/ai/prompts/tasks/`. No inline prompt strings exist in Python code (services now use `PromptLoader`).

### 4. Observability
Every AI call logs a structured `ai_call` event:
```python
logger.info(
    "ai_call",
    prompt=prompt_name,
    prompt_version=template.version,
    model=physical_model,
    provider=provider_name,
    latency_ms=latency_ms,
    success=True,
)
```

### 5. Retry Policies
`OllamaProvider` implements manual exponential backoff (1s → 2s → 4s, 3 attempts) for transient errors (connection errors, timeouts). Non-transient errors (auth, model-not-found) are raised immediately.

---

## What Changed From Old Code

| Before | After |
|--------|-------|
| Inline `_SYSTEM_PROMPT` string constants in each service | Loaded from YAML via `PromptLoader` |
| Inline `_USER_PROMPT_TEMPLATE` string constants | YAML `user_template` field with `{placeholder}` syntax |
| No telemetry logging in services | `ai_call` structured log with prompt, version, model, provider, latency |
| `AsyncOllamaClient` — no retry logic | `OllamaProvider` with 3-attempt exponential backoff for transient errors |
| No model registry | `ModelRegistry` maps logical → physical model from `models.yaml` |
| No LLMRuntime | `LLMRuntime` orchestrates prompt loading, rendering, provider call, telemetry |
| No skill abstraction | Skills in `src/ai/skills/` wrap runtime calls with typed result parsing |

---

## Backward Compatibility

All existing service signatures are preserved:

- `generate_summary(content, client, *, model)` — unchanged signature
- `extract_entities(content, client, *, model)` — unchanged signature
- `generate_ai_tags(content, client, *, model, max_tags)` — unchanged signature
- `generate_relations_for_resource(session, resource_id, ollama_client)` — unchanged signature
- `enrichment/services/ollama_client.py` — kept as-is (OllamaClientProtocol, AsyncOllamaClient)

`OllamaProvider` implements the same `generate(model, prompt, system)` and `is_available()` interface as `OllamaClientProtocol`, so it's drop-in compatible with the existing enrichment pipeline.

---

## How the Layers Connect

```
enrichment_pipeline.py
    → generate_summary(content, client, model=...)
        → PromptLoader.load("summarize")          # reads summarize.yaml
        → PromptLoader.render(template, content=...)
        → client.generate(model, prompt, system)  # OllamaClientProtocol
        → logger.info("ai_call", ...)             # telemetry

get_llm_runtime()           # convenience factory in src/ai/__init__.py
    → OllamaProvider(base_url)
    → ModelRegistry()        # loads models.yaml, resolves ${CHAT_MODEL}
    → PromptLoader()
    → LLMRuntime(provider, registry, loader)

LLMRuntime.run_skill(prompt_name, logical_model, render_kwargs)
    → PromptLoader.load(prompt_name)
    → ModelRegistry.get(logical_model) → physical model name
    → PromptLoader.render(template, **render_kwargs)
    → provider.generate(physical_model, prompt, system, temperature)
    → logger.info("ai_call", ...)
```

---

## Adding a New Skill

1. Add a YAML file: `src/ai/prompts/tasks/<name>.yaml`
2. Create `src/ai/skills/<name>.py` with a `run_<name>(content, runtime)` function
3. Call `runtime.run_skill(prompt_name="<name>", logical_model="chat_model", render_kwargs={...})`
4. Parse the JSON response and return a typed result

---

## Testing

```bash
cd apps/api
uv run pytest src/ -x -q
# 54 tests pass (45 existing + 9 new AI layer tests)
```

New tests added:
- `src/ai/tests/test_llm_runtime.py` — verifies runtime dispatch, telemetry, response pass-through
- `src/ai/tests/test_prompt_loader.py` — verifies YAML loading, rendering, error handling
- `src/ai/tests/test_ollama_provider.py` — verifies availability check, thinking-trace stripping, retry behavior

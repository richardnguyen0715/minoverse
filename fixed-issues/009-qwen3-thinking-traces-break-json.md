# Issue 009: Qwen3 Thinking Traces Break JSON Parsing

## Status
Resolved

## Symptom
All AI enrichment returns empty results even when Ollama responds successfully (HTTP 200).  
Worker logs show `tagging_generation_failed`, `entity_extraction_failed`, etc. with JSON decode errors.

## Root Cause
`qwen3` (and `qwen3:0.6b`) is a **thinking model**. Before emitting the actual JSON response, it outputs a reasoning block wrapped in `<think>…</think>` tags:

```
<think>
The user wants me to extract tags from this content...
</think>
{"tags": ["machine-learning", "transformers"]}
```

All enrichment services called `json.loads(response)` directly, which fails on the `<think>` prefix:

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

The exception was caught and the service silently returned empty results.

## Fix
Added `strip_thinking()` utility in `src/enrichment/services/ollama_client.py`:

```python
import re

_THINKING_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

def strip_thinking(text: str) -> str:
    return _THINKING_RE.sub("", text).strip()
```

Applied in `AsyncOllamaClient.generate()` so all callers receive clean text:

```python
return strip_thinking(response.response)
```

Also applied explicitly before `json.loads()` in `relation_generation_service.py`.

## Prevention Checklist
- [ ] Apply `strip_thinking()` in the Ollama client layer (not per-service) so all callers benefit
- [ ] When switching to a new LLM, check if it is a thinking model and test JSON output
- [ ] Add integration test: assert `json.loads(ollama_client.generate(...))` succeeds with a known prompt

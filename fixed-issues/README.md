# Known Issues & Lessons Learned

This directory documents bugs that were encountered, diagnosed, and fixed during development of Minoverse. Each file is a reference to avoid repeating the same mistakes.

## Index

| File | Category | Summary |
|---|---|---|
| [`001-cors-missing.md`](001-cors-missing.md) | Backend / Web | CORS not configured → browser `TypeError: Failed to fetch` |
| [`002-url-state-not-reactive.md`](002-url-state-not-reactive.md) | Frontend | `useState(searchParam)` doesn't update on navigation |
| [`003-uvicorn-wrong-cwd.md`](003-uvicorn-wrong-cwd.md) | DevOps | uvicorn cwd determines which `.env` pydantic-settings loads |
| [`004-sqlalchemy-reserved-metadata.md`](004-sqlalchemy-reserved-metadata.md) | Backend / ORM | `metadata` is a reserved attribute name in SQLAlchemy declarative |
| [`005-structlog-printlogger-no-name.md`](005-structlog-printlogger-no-name.md) | Backend / Logging | `add_logger_name` processor requires stdlib logger, not `PrintLogger` |
| [`006-uv-run-pid-stale.md`](006-uv-run-pid-stale.md) | DevOps | `uv run` is a launcher; the child PID is stale immediately |
| [`007-ollama-models-not-pulled.md`](007-ollama-models-not-pulled.md) | AI / Setup | Ollama container starts empty; models must be pulled manually |
| [`008-dramatiq-dual-broker.md`](008-dramatiq-dual-broker.md) | Backend / Workers | Two `dramatiq.set_broker()` calls → second overwrites first; actors lost |
| [`009-qwen3-thinking-traces-break-json.md`](009-qwen3-thinking-traces-break-json.md) | AI / LLM | qwen3 emits `<think>…</think>` before JSON; `json.loads()` fails silently |
| [`010-entity-promotion-schema-mismatch.md`](010-entity-promotion-schema-mismatch.md) | Backend / Graph | Phase 3 stores `{tools:[]}` but Phase 4 read `{entities:[]}` — always empty |

---

## Convention

Each issue file follows this structure:

```
## Symptom
## Root Cause
## Fix
## Prevention Checklist
```

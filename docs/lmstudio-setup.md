# LM Studio Setup Guide

> Use LM Studio as an AI provider — local or remote, no cloud required.

---

## Prerequisites

1. **Download LM Studio** from [lmstudio.ai](https://lmstudio.ai/) (macOS / Windows / Linux).
2. Load at least one **chat model** (e.g. `google/gemma-4-e4b`, `qwen2.5-7b-instruct`).
3. Optionally load an **embedding model** (e.g. `nomic-embed-text-v1.5`).
4. Enable and start the **LM Studio local server** (Server tab → Start Server).

---

## Deployment Scenarios

### A — LM Studio running on the same machine (localhost)

```bash
# apps/api/.env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234
LMSTUDIO_CHAT_MODEL=google/gemma-4-e4b
LMSTUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
```

### B — LM Studio running on a different machine on your LAN *(current setup)*

```bash
# apps/api/.env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://192.168.1.12:1234
LMSTUDIO_CHAT_MODEL=google/gemma-4-e4b
LMSTUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
```

Replace `192.168.1.12` with the LAN IP of the machine running LM Studio, and
`1234` with whatever port its server is bound to.

> **LM Studio server network binding** — by default LM Studio only listens on
> `127.0.0.1` (localhost). To allow connections from other machines you must
> change the binding in LM Studio's **Server → Network** settings to
> `0.0.0.0` (all interfaces) before other hosts can reach it.

### C — LM Studio with API key authentication

If you enabled the optional API key in LM Studio's server settings:

```bash
# apps/api/.env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://192.168.1.12:1234
LMSTUDIO_CHAT_MODEL=google/gemma-4-e4b
LMSTUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
LMSTUDIO_API_KEY=lms-your-key-here
```

---

## Full `.env` Reference (LM Studio section)

| Variable | Required | Default | Description |
|---|---|---|---|
| `AI_PROVIDER` | ✅ | `gemini` | Must be `lmstudio` to activate this provider |
| `LMSTUDIO_BASE_URL` | ✅ | `http://localhost:1234` | Full URL of the LM Studio server |
| `LMSTUDIO_CHAT_MODEL` | ✅ | _(empty)_ | Model ID for text generation |
| `LMSTUDIO_EMBEDDING_MODEL` | ✅ | _(empty)_ | Model ID for embeddings |
| `LMSTUDIO_API_KEY` | ❌ | _(empty)_ | Bearer token (only if auth is enabled) |

---

## Finding Model Identifiers

Model IDs shown in LM Studio's **Server** tab are what you must use verbatim.

You can also query the running server directly:

```bash
# localhost
curl http://localhost:1234/v1/models | jq '.data[].id'

# remote server
curl http://192.168.1.12:1234/v1/models | jq '.data[].id'
```

Example output:
```json
"google/gemma-4-e4b"
"text-embedding-nomic-embed-text-v1.5"
```

---

## Verifying Connectivity

```bash
# Health-check — should return 200 with a list of loaded models
curl -s http://192.168.1.12:1234/v1/models

# Quick generation test
curl -s http://192.168.1.12:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-4-e4b","messages":[{"role":"user","content":"ping"}]}'

# Embedding test
curl -s http://192.168.1.12:1234/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"text-embedding-nomic-embed-text-v1.5","input":"hello world"}'
```

---

## Applying Changes

After editing `.env`, restart the API server for the new URL to take effect:

```bash
make restart
# or if only the API needs to restart:
make stop && make start
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `LMStudioUnavailableError` on startup | Server not reachable | Run `curl http://192.168.1.12:1234/v1/models` to test; check firewall |
| `Connection refused` | LM Studio bound to `127.0.0.1` only | In LM Studio → Server → Network, bind to `0.0.0.0` |
| `Model not found` / wrong output | Model ID typo | Use `curl /v1/models` to list exact IDs |
| Embeddings always fail | No embedding model loaded | Load an embedding model in LM Studio before starting the server |
| `401 Unauthorized` | API key mismatch | Set `LMSTUDIO_API_KEY` in `.env` to match the key set in LM Studio |
| Slow responses over LAN | Network latency | Normal for large models; increase timeout in `lmstudio.py` if needed (`timeout=120.0`) |

---

## Architecture

```
apps/api/src/ai/
├── providers/
│   ├── base.py          # LLMProvider Protocol (generate, embeddings, is_available)
│   ├── ollama.py        # OllamaProvider
│   ├── gemini.py        # GeminiProvider
│   └── lmstudio.py      # LMStudioProvider
├── configs/
│   └── models.yaml      # lmstudio: section — chat + embedding model refs
├── models/
│   └── registry.py      # resolves ${LMSTUDIO_CHAT_MODEL} env placeholders
└── __init__.py           # factory — selected when AI_PROVIDER=lmstudio
```

The `LMStudioProvider` communicates via LM Studio's **OpenAI-compatible API**:

| Endpoint | Purpose |
|---|---|
| `GET /v1/models` | Health check — lists loaded models |
| `POST /v1/chat/completions` | Text generation |
| `POST /v1/embeddings` | Vector embeddings |

It uses `httpx.AsyncClient` with 3-attempt exponential backoff (1 s / 2 s / 4 s)
and automatically strips `<think>…</think>` traces from reasoning-model output.
The base URL is passed directly to `httpx` so any reachable HTTP address works —
localhost, LAN IP, or a reverse-proxied domain name.


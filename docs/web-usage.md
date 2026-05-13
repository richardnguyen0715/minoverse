# Web UI — Usage Guide

The Minoverse Web UI is a Next.js 15 application at `http://localhost:3000`. It talks directly to the FastAPI backend at `http://localhost:8000`.

---

## Prerequisites

Before starting the web UI you need the full backend running:

```bash
# Node.js 18+ required
node --version   # must be ≥ 18

# Install web dependencies (first time only)
make web-install
```

---

## Start & Stop

### Start everything (recommended)

`make start` now starts the Web UI automatically as step ⑩:

```bash
make start
```

After startup completes:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Minoverse is running 🚀

  API       →  http://localhost:8000
  API docs  →  http://localhost:8000/docs
  Web UI    →  http://localhost:3000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Start web UI only (already have backend running)

```bash
make web-dev
# or directly:
cd apps/web && npm run dev
```

### Stop everything

```bash
make stop
```

This stops: web UI → enrichment worker → vault watcher → API server → Docker services.

### Status check

```bash
make status
```

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Minoverse Status

  🟢 API server    http://localhost:8000   (PID 22146)
  🟢 Vault watcher running                (PID 22156)
  🟢 Enrich worker running                (PID 22167)
  🟢 Web UI        http://localhost:3000   (PID 22178)

  Docker services:
    🟢 minoverse_ollama     Up 5 minutes
    🟢 minoverse_postgres   Up 5 minutes (healthy)
    🟢 minoverse_redis      Up 5 minutes (healthy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Pages

| URL | Description |
|---|---|
| `http://localhost:3000` | Redirects to `/resources` |
| `http://localhost:3000/resources` | All resources — filterable grid |
| `http://localhost:3000/resources/{id}` | Resource viewer with AI panel and graph |
| `http://localhost:3000/notes` | All notes — filterable list |
| `http://localhost:3000/notes/{id}` | Note viewer with backlinks |

---

## UI Demo

### 1. Browse resources

Open `http://localhost:3000/resources`:

- Use the **type tabs** at the top to filter by `Paper / Note / Concept / Daily / YouTube / GitHub / Article / Docs / Tweet`
- Use the **search bar** to filter by title (debounced, 300 ms)
- Each card shows: title, type badge, author, date, tags preview

### 2. Open a resource

Click any card to open `http://localhost:3000/resources/{id}`:

- **Left panel** — document area:
  - Title + type badge
  - Metadata row: author, published date, source URL
  - Heading table of contents (extracted from `extra_metadata`)

- **Right panel — AI tab** (default):
  - Concise summary written by the LLM
  - AI-generated tags (colored badges)
  - Extracted entities (people, orgs, concepts, locations)
  - Related resources (by tag overlap)
  - **"Trigger enrichment"** button — re-runs the AI pipeline for this resource

- **Right panel — Graph tab**:
  - React Flow mini-graph of wiki-link neighbors
  - Click any node to navigate to that resource
  - Zoom, pan, fit-view controls

- **Right panel — Info tab**:
  - Raw metadata JSON (resource type, vault path, created/updated timestamps, frontmatter)

### 3. Command Palette (⌘K)

Press `Cmd+K` (or `Ctrl+K` on Linux/Windows) from anywhere:

- Type to search all resources by title
- Arrow keys + Enter to navigate
- Escape to close

### 4. Sidebar

Click the hamburger icon to toggle the left sidebar:

- **Library** — type navigation links
- **Recent** — last 10 resources you opened (stored in Zustand KnowledgeStore)

### 5. Notes

Open `http://localhost:3000/notes`:

- Filter by note type: All / Note / Concept / Daily Note
- Open a note to see its frontmatter metadata and **Backlinks** section (wiki links pointing to this note)

---

## Development

### Run dev server (hot reload)

```bash
make web-dev
# or
cd apps/web && npm run dev
```

Changes to `apps/web/src/` hot-reload instantly.

### Build for production

```bash
make web-build
# or
cd apps/web && npm run build
```

### Logs

```bash
make logs-web
# or
tail -f .minoverse/web.log
```

---

## Testing

```bash
# Run web tests only
make web-test

# Run all tests (API + web)
make test
```

Tests live in `apps/web/src/__tests__/`:

```
__tests__/
  lib/
    utils.test.ts   — 10 tests: resourceTypeLabel, formatDate, buildApiUrl, cn
    api.test.ts     — 5 tests: typed fetch client (mock fetch)
  store/
    ui-store.test.ts — 3 tests: palette/sidebar/rightPanelTab state
```

**Expected output:**

```
 ✓ src/__tests__/lib/utils.test.ts (10)
 ✓ src/__tests__/lib/api.test.ts (5)
 ✓ src/__tests__/store/ui-store.test.ts (3)

 Test Files  3 passed (3)
 Tests       18 passed (18)
```

---

## Environment

`apps/web/.env.local` controls the API endpoint:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Copy from the example if missing:

```bash
cp apps/web/.env.local.example apps/web/.env.local
```

Change `NEXT_PUBLIC_API_URL` to point at a remote API for staging/production.

---

## Debugging

### Web UI won't load

```bash
# Check the process is running
make status

# Check logs
make logs-web

# Restart web only
cd apps/web && npm run dev
```

### "Failed to fetch" in the browser

The API is not reachable. Check:

```bash
curl http://localhost:8000/health
# should return: {"status":"ok","version":"0.1.0"}

# If API is down, restart:
make restart
```

### Resource list is empty

The vault hasn't been indexed yet:

```bash
make index
```

### AI enrichments missing

The Ollama LLM models haven't been pulled, or the enrichment worker is not running:

```bash
# Pull models
docker exec -it minoverse_ollama ollama pull bge-m3
docker exec -it minoverse_ollama ollama pull qwen3

# Check worker
make status

# Trigger enrichment manually from the UI (right panel → AI tab → "Trigger enrichment")
# Or via API:
curl -X POST http://localhost:8000/enrichment/{resource-id}/trigger
```

### CORS error in browser console

CORS is configured in `apps/api/src/main.py` to allow `http://localhost:3000`. If you change the web port, update the `allow_origins` list there.

### Slow initial load

The Next.js dev server compiles on first request. Subsequent loads are instant. Use `make web-build` + `npm start` for production performance.

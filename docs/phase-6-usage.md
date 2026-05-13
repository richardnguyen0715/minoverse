# Phase 6 — Desktop + Sync: Usage Guide

## Quick Start

```bash
make start         # starts everything; migration 007 auto-applied
```

Open the Sync page:

```bash
make sync          # opens http://localhost:3000/sync
```

---

## Sync Event Log

### What it tracks

Every time a vault file is created, updated, or deleted, Minoverse writes a `sync_event` to the database. These events are the audit trail for your knowledge vault.

### View the event log

```bash
# Browser
make sync
# → http://localhost:3000/sync

# API
curl http://localhost:8000/sync/events
curl "http://localhost:8000/sync/events?event_type=resource.created&limit=20"
curl "http://localhost:8000/sync/events?applied=false"
```

### Filter events

| Query param | Values | Example |
|---|---|---|
| `event_type` | `resource.created`, `resource.updated`, `resource.deleted` | `?event_type=resource.deleted` |
| `applied` | `true`, `false` | `?applied=false` |
| `limit` | 1–500 (default 50) | `?limit=10` |
| `offset` | 0+ | `?offset=50` |

### Emit an event manually

```bash
curl -X POST http://localhost:8000/sync/emit \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "resource.created",
    "resource_path": "vault/notes/test.md",
    "payload": {"note": "manual test event"}
  }'
```

### Replay unapplied events

Replay all events since 24 hours ago:

```bash
SINCE=$(date -u -v-1d +"%Y-%m-%dT%H:%M:%SZ")   # macOS
# SINCE=$(date -u -d "1 day ago" +"%Y-%m-%dT%H:%M:%SZ")  # Linux

curl -X POST "http://localhost:8000/sync/replay?since=${SINCE}"
```

Replay only specific event types:

```bash
curl -X POST "http://localhost:8000/sync/replay?since=${SINCE}&event_types=resource.created&event_types=resource.updated"
```

---

## Sync Status Badge

The `SyncStatus` component appears at the top of the `/sync` page and auto-refreshes every 30 seconds.

| Status | Meaning |
|---|---|
| 🟢 Synced | All events have `applied=true` |
| 🟡 N pending | N events with `applied=false` (replay needed) |
| 🔴 Error | API unreachable |

---

## Desktop App (Tauri)

### Prerequisites

1. **Install Rust** (one-time):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env
   ```

2. **Install Tauri CLI** (one-time):
   ```bash
   cargo install tauri-cli --version "^2.0"
   ```

3. **Install npm deps**:
   ```bash
   make desktop-install
   ```

### Run in development

```bash
# Terminal 1 — start web UI
make web-dev

# Terminal 2 — start desktop shell
make desktop-dev
```

The desktop window opens and loads `http://localhost:3000`. Full hot-reload works.

### Build production binary

```bash
make desktop-build
# Output: apps/desktop/src-tauri/target/release/bundle/
```

The binary embeds the Next.js static build and ships as a single `.app` / `.exe` / `.deb`.

### Tauri IPC commands

These can be called from the Next.js frontend via `@tauri-apps/api/core`:

```typescript
import { invoke } from '@tauri-apps/api/core'

// Get OS info
const info = await invoke<{ os: string; arch: string }>('get_system_info')

// Check API health
const healthy = await invoke<boolean>('check_api_health')

// Open vault in finder/explorer
await invoke('open_vault_dir', { path: '/Users/me/vault' })
```

---

## CRDT / Future Sync

The `sync_events` table is pre-wired for multi-device sync:

### `device_id` — identify your device

```bash
# Set in apps/api/.env
DEVICE_ID=macbook-pro-richard
```

All events emitted from this device will have `device_id` set.

### `vector_clock` — causal ordering

Each device maintains a vector clock `{"device_id": sequence}`. When syncing:

1. Send your current vector clock to the sync server
2. Server returns all events with higher sequence numbers
3. Apply them in causal order (deterministic)
4. Update your local vector clock

### `operation_id` — idempotency

Every event has a unique `operation_id`. Replaying the same event twice is safe — the receiver deduplicates by `operation_id`.

---

## Makefile Reference

```bash
make sync            # open sync event log in browser
make desktop-install # install Tauri CLI npm wrapper
make desktop-dev     # run desktop in dev mode (requires Rust)
make desktop-build   # build production desktop binary (requires Rust)
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/sync/events` | List events (paginated) |
| `POST` | `/sync/emit` | Emit a sync event |
| `POST` | `/sync/replay` | Replay unapplied events since timestamp |

Full interactive docs: `http://localhost:8000/docs#/sync`

---

## Debugging

### Check sync events in DB

```bash
docker exec -it minoverse_postgres psql -U minoverse -d minoverse -c \
  "SELECT event_type, resource_path, applied, created_at FROM sync_events ORDER BY created_at DESC LIMIT 20;"
```

### Check pending (unapplied) events

```bash
curl "http://localhost:8000/sync/events?applied=false" | python3 -m json.tool
```

### Run sync tests

```bash
cd apps/api && uv run pytest src/sync/tests/ -v
```

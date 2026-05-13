# Phase 6 — Desktop + Sync: Implementation Record

## Overview

Phase 6 turns Minoverse into a production-grade, local-first Knowledge OS by adding two major capabilities:

| Capability | What it delivers |
|---|---|
| **Event Sourcing** | Every vault change is persisted as a durable `sync_event` — fully replayable, auditable, CRDT-ready |
| **Desktop App** | Tauri v2 shell wrapping the Next.js web UI — native OS integration, ships as a single binary |

---

## 6.1 Desktop App (Tauri v2)

### Location
`apps/desktop/`

### Structure

```
apps/desktop/
├── package.json              ← Tauri CLI npm wrapper
├── .gitignore
├── README.md
└── src-tauri/
    ├── Cargo.toml            ← Rust manifest
    ├── tauri.conf.json       ← Tauri configuration (loads localhost:3000)
    └── src/
        ├── main.rs           ← Entry point
        └── lib.rs            ← Tauri commands
```

### Tauri Commands (IPC)

| Command | Signature | Description |
|---|---|---|
| `get_system_info` | `() → JSON` | Returns OS, arch, family |
| `check_api_health` | `() → bool` | Pings `localhost:8000/health` |
| `open_vault_dir` | `(path: String) → ()` | Opens path in native file manager (macOS: `open`, Linux: `xdg-open`, Windows: `explorer`) |

### Dev Configuration (`tauri.conf.json`)

```json
{
  "identifier": "com.minoverse.desktop",
  "build": {
    "devUrl": "http://localhost:3000",
    "beforeBuildCommand": "cd ../web && npm run build",
    "frontendDist": "../web/.next"
  }
}
```

In dev mode: loads `http://localhost:3000` (the Next.js dev server).  
In production build: embeds the Next.js static output.

### Prerequisites to Build

```bash
# 1. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 2. Install Tauri CLI
cargo install tauri-cli --version "^2.0"

# 3. Install npm deps
make desktop-install

# 4. Run in dev mode
make desktop-dev

# 5. Build production binary
make desktop-build
```

---

## 6.2 Local Database Packaging

The local-first packaging is already delivered via Docker Compose:

| Service | Container | Port |
|---|---|---|
| PostgreSQL 16 + pgvector | `minoverse_postgres` | 5432 |
| Redis 7 | `minoverse_redis` | 6379 |
| Ollama | `minoverse_ollama` | 11434 |

`make start` brings up all three automatically. No cloud dependency required.

For future packaging: Tauri sidecar support can bundle these as embedded services using `tauri-plugin-shell`.

---

## 6.3 Event Sourcing

### Database Table: `sync_events` (migration 007)

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` |
| `event_type` | VARCHAR(50) | See event type catalog below |
| `resource_id` | UUID FK → resources | SET NULL on delete; nullable |
| `resource_path` | TEXT | Vault-relative path (useful after resource deletion) |
| `operation_id` | UUID | Per-operation idempotency key (CRDT-ready) |
| `device_id` | VARCHAR(255) | Multi-device identifier (future use) |
| `vector_clock` | JSONB | CRDT vector clock `{"device_id": sequence}` |
| `payload` | JSONB | Event-specific diff / metadata |
| `applied` | BOOLEAN | Replay status; `false` = pending |
| `created_at` | TIMESTAMPTZ | Event timestamp |

Indexes: `event_type`, `resource_id`, `applied`, `created_at`.

### Event Type Catalog

| Event type | Emitted by | Trigger |
|---|---|---|
| `resource.created` | ingestion_service | New vault file indexed |
| `resource.updated` | ingestion_service | Existing file re-indexed |
| `resource.deleted` | ingestion_service | File removed from vault |
| `enrichment.completed` | (reserved) | AI enrichment job finishes |
| `graph.built` | (reserved) | Graph build job finishes |
| `memory.ask` | (reserved) | Copilot question answered |

### Architecture Flow

```
Vault file saved
    → watchfiles detects change
    → ingestion_service.ingest_file()
        → upsert_resource()       ← creates/updates DB row
        → _emit_sync_event()      ← fire-and-forget sync event
            → event_log_service.emit()
                → sync_event_repository.log_event()
                    → INSERT INTO sync_events
```

### Code Structure

```
src/sync/
├── __init__.py
├── entities/
│   ├── __init__.py
│   └── sync_event.py          ← SyncEvent ORM model
├── schemas/
│   ├── __init__.py
│   └── sync_schemas.py        ← SyncEventCreate, SyncEventRead, SyncEventFilter, SyncEventPage
├── repositories/
│   ├── __init__.py
│   └── sync_event_repository.py  ← log_event, list_events, count_events, mark_applied, get_events_since
├── services/
│   ├── __init__.py
│   └── event_log_service.py   ← emit, list_events, replay_events
├── routes.py                  ← sync_router → GET /sync/events, POST /sync/emit, POST /sync/replay
└── tests/
    ├── __init__.py
    └── test_phase6.py         ← 14 unit tests
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/sync/events` | Paginated event log; filter by `event_type`, `applied`, `limit`, `offset` |
| `POST` | `/sync/emit` | Manually emit a sync event |
| `POST` | `/sync/replay` | Replay unapplied events since a timestamp; marks them `applied=true` |

---

## 6.4 CRDT / Future Sync Preparation

The `sync_events` table is designed to be CRDT-ready from day one:

| Field | CRDT purpose |
|---|---|
| `operation_id` | Unique per logical operation — enables idempotent replay across devices |
| `device_id` | Identifies the originating device — enables per-device event filtering |
| `vector_clock` | `{"device_id": sequence_number}` — enables causal ordering without central clock |
| `applied` | Replay cursor — each device tracks which events it has processed |

When multi-device sync is implemented (future), the replay endpoint becomes the sync protocol:
1. Device A sends its `vector_clock` to the server
2. Server returns all events not yet seen by Device A
3. Device A applies them, marks them applied, and sends its new events up

---

## Frontend Changes

### New Components

| File | Purpose |
|---|---|
| `src/components/sync/sync-status.tsx` | Polling status badge: 🟢 Synced / 🟡 N pending / 🔴 Error |
| `src/app/sync/page.tsx` | Full event log page with table, type filter, Replay button |

### Sidebar Update

Added `🔄 Sync` nav link (after Memory).

### New Types

`SyncEvent`, `SyncEventPage`, `SyncEmitRequest`, `SyncReplayResult` added to `src/lib/types.ts`.

### New API Functions

`listSyncEvents`, `emitSyncEvent`, `replaySyncEvents` added to `src/lib/api.ts`.

---

## Test Coverage

| Suite | Tests | Result |
|---|---|---|
| Backend (Phase 6) | 14 | ✅ All pass |
| Backend (total) | 90 | ✅ All pass |
| Frontend (sync) | 7 | ✅ All pass |
| Frontend (total) | 50 | ✅ All pass |

---

## Migration

```bash
make migrate
# applies 007_add_sync_phase6.py → creates sync_events table + 4 indexes
```

Applied automatically on `make start`.

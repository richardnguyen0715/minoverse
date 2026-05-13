# Minoverse — Quick Start Guide

> One command to start everything. One command to stop.

---

## Start

```bash
make start
```

That's it. This single command:

1. Starts Postgres, Redis, and Ollama (Docker)
2. Waits for Postgres to be healthy
3. Installs Python dependencies (`uv sync`)
4. Applies any pending database migrations
5. Starts the API server in the background → `http://localhost:8000`
6. Indexes all markdown files in your vault
7. Starts the live file watcher (auto-indexes on save)

---

## Stop

```bash
make stop
```

Stops the API server, the vault watcher, and all Docker services.

---

## Other Commands

```bash
make restart     # stop + start in one shot
make status      # show what is running
make logs-api    # tail API server logs
make logs-watch  # tail vault watcher logs
make index       # re-index the vault manually
make migrate     # apply pending DB migrations
make test        # run all tests
make help        # list all available commands
```

---

## First-Time Setup

The only thing you need before running `make start` for the first time:

1. **Docker** must be running (Docker Desktop or `dockerd`)
2. **uv** must be installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Clone the repo:
   ```bash
   git clone https://github.com/richardnguyen0715/minoverse.git
   cd minoverse
   ```

Then just:
```bash
make start
```

---

## Where Things Are

| What | Location |
|---|---|
| API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |
| API server log | `.minoverse/api.log` |
| Vault watcher log | `.minoverse/watcher.log` |
| Your vault (markdown files) | `vault/` |
| API config | `apps/api/.env` (auto-created on first start) |

---

## Adding Knowledge to Your Vault

Drop any `.md` file into the `vault/` directory. The watcher picks it up automatically:

```bash
cat > vault/notes/my-idea.md << 'EOF'
---
title: My Idea
tags: [ideas, project]
---

# My Idea

This links to [[Another Note]].
EOF
```

The file is indexed within seconds. Check it via API:

```bash
curl http://localhost:8000/notes | python3 -m json.tool
```

---

## Checking Status

```bash
make status
```

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Minoverse Status

  🟢 API server    http://localhost:8000   (PID 22146)
  🟢 Vault watcher running             (PID 22156)

  Docker services:
    🟢 minoverse_ollama     Up 2 minutes
    🟢 minoverse_postgres   Up 2 minutes (healthy)
    🟢 minoverse_redis      Up 2 minutes (healthy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Troubleshooting

**`make start` fails at postgres step**
: Docker is not running. Start Docker Desktop and try again.

**API shows 🔴 in `make status` after start**
: The API process crashed. Check the log: `make logs-api`

**Vault files not being picked up**
: Check `VAULT_PATH` in `apps/api/.env` — it should point to the `vault/` directory.  
  Run `make index` to force a full re-index.

**Port 8000 already in use**
: Something else is using the port. Run `lsof -i :8000` to find it, kill it, then `make start`.

**Migrations fail**
: Postgres may not be healthy yet. Run `make stop` then `make start` again.

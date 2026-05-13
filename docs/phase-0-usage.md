# Phase 0 — Usage Guide

> Start, stop, and debug the local development stack.

---

## Prerequisites

All commands assume you have:
- Docker Desktop running
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Dependencies installed (`cd apps/api && uv sync --extra dev`)

---

## START

### Step 1 — Start infrastructure

```bash
cd infra
docker compose up -d postgres redis ollama
```

Wait until all containers are healthy:

```bash
docker compose ps
```

Expected output:

```
NAME                IMAGE                    STATUS
minoverse_postgres  pgvector/pgvector:pg16   Up N seconds (healthy)
minoverse_redis     redis:7-alpine           Up N seconds (healthy)
minoverse_ollama    ollama/ollama:latest     Up N seconds
```

> Note: `minoverse_ollama` does not have a healthcheck — "Up" is sufficient.

### Step 2 — Run database migrations

```bash
cd ../apps/api
uv run alembic upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema — Phase 0 foundation tables.
```

> Skip this step on subsequent starts — migrations only need to run once (or after a new migration is added).

### Step 3 — Start the API server

```bash
# still inside apps/api/
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:

```
INFO:  Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:  Started reloader process using WatchFiles
INFO:  Application startup complete.
```

The API is now available at:

| URL | Description |
|---|---|
| http://localhost:8000 | Redirects to `/docs` |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc UI |
| http://localhost:8000/health | Liveness check → `{"status":"ok","version":"0.1.0"}` |

---

## STOP

### Stop the API server

Press `Ctrl+C` in the terminal running uvicorn.

### Stop infrastructure (keep data)

```bash
cd infra
docker compose stop
```

Containers are stopped but volumes are preserved — database data survives.

### Stop and remove containers (keep data)

```bash
docker compose down
```

Volumes (`postgres_data`, `redis_data`, `ollama_data`) are preserved.

### Full teardown (destroys all data)

```bash
docker compose down -v
```

> ⚠️ This deletes the database. You will need to re-run migrations on next start.

---

## RESTART

### Restart after `docker compose stop`

```bash
cd infra
docker compose start
# then in apps/api/
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Restart after `docker compose down` (data preserved)

```bash
cd infra
docker compose up -d postgres redis ollama
# migrations already applied — skip alembic
cd ../apps/api
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Restart after `docker compose down -v` (data wiped)

```bash
cd infra
docker compose up -d postgres redis ollama
cd ../apps/api
uv run alembic upgrade head      # re-run migrations
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## DEBUG

### Check container health

```bash
cd infra
docker compose ps                # status + health
docker compose logs postgres     # postgres logs
docker compose logs redis        # redis logs
docker compose logs ollama       # ollama logs
```

### Check if pgvector extension is loaded

```bash
docker exec -it minoverse_postgres psql -U minoverse -d minoverse \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

Expected:

```
 extname | extversion
---------+------------
 vector  | 0.8.0
```

### Verify all tables were created

```bash
docker exec -it minoverse_postgres psql -U minoverse -d minoverse -c "\dt"
```

Expected tables:

```
 chunk_embeddings   ingestion_jobs   notes
 resource_chunks    resource_contents  resource_tags
 resources          tags             vault_files
 wiki_links
```

### Check migration history

```bash
cd apps/api
uv run alembic history --verbose
uv run alembic current           # which revision is applied
```

### Roll back last migration

```bash
uv run alembic downgrade -1
```

### Run API in debug mode (verbose SQL + dev logging)

```bash
cd apps/api
DEBUG=true uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

With `DEBUG=true`:
- SQLAlchemy echoes all SQL queries to stdout
- structlog uses pretty colored console output instead of JSON

### Test the health endpoint

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

Expected:

```json
{
    "status": "ok",
    "version": "0.1.0"
}
```

### Inspect Redis (event bus)

```bash
docker exec -it minoverse_redis redis-cli ping        # should return PONG
docker exec -it minoverse_redis redis-cli monitor     # live command stream
```

### Connect to PostgreSQL directly

```bash
docker exec -it minoverse_postgres psql -U minoverse -d minoverse
```

Useful psql commands:

```sql
\dt                        -- list tables
\d resources               -- describe resources table
\d chunk_embeddings        -- verify vector(1536) column type
SELECT COUNT(*) FROM vault_files;
\q                         -- exit
```

### Rebuild the API container (after dependency changes)

```bash
cd infra
docker compose build api
docker compose up -d api
```

---

## Port Reference

| Service | Port | Notes |
|---|---|---|
| FastAPI | 8000 | Dev server (uvicorn --reload) |
| PostgreSQL | 5432 | User: `minoverse`, DB: `minoverse` |
| Redis | 6379 | No auth in dev |
| Ollama | 11434 | REST API for local LLMs |

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `No 'script_location' key found` | Running `alembic` from wrong directory | `cd apps/api` first |
| `connection refused :5432` | Postgres container not running | `docker compose up -d postgres` |
| `connection refused :6379` | Redis container not running | `docker compose up -d redis` |
| `Unable to determine which files to ship` | hatchling build config missing | `[tool.hatch.build.targets.wheel] packages = ["src"]` in pyproject.toml |
| `Attribute name 'metadata' is reserved` | SQLAlchemy DeclarativeBase conflict | Use `extra_metadata` + `mapped_column("metadata", ...)` |
| `404 Not Found` on `/` | No routes defined | Expected in Phase 0 — visit `/docs` or `/health` |

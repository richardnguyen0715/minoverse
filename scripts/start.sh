#!/usr/bin/env bash
# start.sh — Start the full Minoverse development stack.
#
# Steps (in order):
#   1. Start infrastructure (postgres, redis, ollama) via Docker Compose
#   2. Wait for postgres to be healthy
#   3. Sync Python dependencies (uv sync)
#   4. Apply database migrations (alembic upgrade head)
#   5. Start API server in background → .minoverse/api.log
#   6. Wait for API to respond at /health
#   7. Index the vault (minoverse index)
#   8. Start the vault watcher in background → .minoverse/watcher.log

# ── Environment bootstrap ─────────────────────────────────────────────────────
# When launched from a GUI app (e.g. Tauri .app bundle), the inherited PATH is
# minimal. Augment it with every common macOS tool location before anything runs.
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Load nvm so `node`/`npm` are available
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" --no-use 2>/dev/null || true

# If Docker CLI is bundled inside Docker Desktop but not on PATH, add it
if ! command -v docker &>/dev/null; then
  DOCKER_EXTRA="/Applications/Docker.app/Contents/Resources/bin"
  [ -d "$DOCKER_EXTRA" ] && export PATH="$DOCKER_EXTRA:$PATH"
fi

# If Docker Desktop is installed but the daemon isn't running, start it
if command -v docker &>/dev/null && ! docker info &>/dev/null 2>&1; then
  echo "🔷 Starting Docker Desktop..."
  open -a Docker 2>/dev/null || true
  # Wait up to 60 s for the daemon to be ready
  for i in $(seq 1 30); do
    docker info &>/dev/null 2>&1 && break
    [ "$i" -eq 30 ] && { echo "❌ Docker Desktop did not start in time" >&2; exit 1; }
    sleep 2
  done
  echo "✅ Docker Desktop ready"
fi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT/apps/api"
INFRA_DIR="$ROOT/infra"
RUN_DIR="$ROOT/.minoverse"

API_PID_FILE="$RUN_DIR/api.pid"
WATCHER_PID_FILE="$RUN_DIR/watcher.pid"
API_LOG="$RUN_DIR/api.log"
WATCHER_LOG="$RUN_DIR/watcher.log"

_info()    { echo "🔷 $*"; }
_ok()      { echo "✅ $*"; }
_warn()    { echo "⚠️  $*"; }
_fail()    { echo "❌ $*" >&2; exit 1; }

# ── Guard: already running ──────────────────────────────────────────────────
if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
  _warn "Minoverse is already running (API PID $(cat "$API_PID_FILE"))"
  echo "   Run 'make stop' first, or 'make restart'."
  exit 0
fi

mkdir -p "$RUN_DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting Minoverse"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Infrastructure ────────────────────────────────────────────────────────
cd "$INFRA_DIR"

# Copy .env for infra if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  _warn "Created infra/.env from .env.example — edit if needed"
fi

# Read AI_PROVIDER to decide whether Ollama container is needed.
AI_PROVIDER="${AI_PROVIDER:-}"
if [ -z "$AI_PROVIDER" ] && [ -f "$API_DIR/.env" ]; then
  AI_PROVIDER=$(grep -E '^AI_PROVIDER=' "$API_DIR/.env" 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || true)
fi
AI_PROVIDER="${AI_PROVIDER:-ollama}"

# Read optional service flags (set by Tauri splash → ~/.minoverse/services.conf)
SERVICES_CONF="$RUN_DIR/services.conf"
ENABLE_WORKER="${ENABLE_WORKER:-true}"
ENABLE_WATCHER="${ENABLE_WATCHER:-true}"
if [ -f "$SERVICES_CONF" ]; then
  # shellcheck source=/dev/null
  source "$SERVICES_CONF"
fi

# Always start postgres + redis; conditionally start ollama
AI_PROVIDER_LC=$(echo "$AI_PROVIDER" | tr '[:upper:]' '[:lower:]')
if [ "$AI_PROVIDER_LC" = "ollama" ]; then
  _info "Starting infrastructure (postgres, redis, ollama)..."
  docker compose up -d postgres redis ollama --quiet-pull
else
  _info "Starting infrastructure (postgres, redis)..."
  docker compose up -d postgres redis --quiet-pull
  _info "AI_PROVIDER=${AI_PROVIDER} — skipping Ollama container"
fi

# ── 2. Wait for postgres ─────────────────────────────────────────────────────
_info "Waiting for postgres..."
for i in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U minoverse > /dev/null 2>&1; then
    _ok "Postgres ready"
    break
  fi
  [ "$i" -eq 30 ] && _fail "Postgres did not become healthy after 60 s"
  sleep 2
done

# ── 3. Python deps ───────────────────────────────────────────────────────────
_info "Syncing Python dependencies..."
cd "$API_DIR"

# Create a minimal API .env if missing (infra .env has postgres-specific keys
# that the Settings model doesn't accept; generate the right keys here)
if [ ! -f ".env" ]; then
  cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://minoverse:minoverse@localhost:5432/minoverse
REDIS_URL=redis://localhost:6379/0
VAULT_PATH=../../vault
DEBUG=false
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=bge-m3
CHAT_MODEL=qwen3
EOF
  _warn "Created apps/api/.env — edit VAULT_PATH if your vault is elsewhere"
fi

uv sync --quiet
_ok "Dependencies up to date"

# ── 4. Migrations ────────────────────────────────────────────────────────────
_info "Applying database migrations..."
uv run alembic upgrade head
_ok "Migrations applied"

# ── 5. API server ────────────────────────────────────────────────────────────
_info "Starting API server (port 8000)..."
# Run the venv binary directly from API_DIR so pydantic-settings picks up
# apps/api/.env (not the root .env which has infra-only postgres keys).
cd "$API_DIR"
nohup "$API_DIR/.venv/bin/uvicorn" src.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  > "$API_LOG" 2>&1 &
echo $! > "$API_PID_FILE"
_ok "API server started (PID $(cat "$API_PID_FILE"))"
# Stay in $API_DIR — steps 7-9 also need apps/api as cwd for pydantic-settings

# ── 6. Wait for API /health ──────────────────────────────────────────────────
_info "Waiting for API to respond..."
for i in $(seq 1 20); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    _ok "API is up at http://localhost:8000"
    break
  fi
  [ "$i" -eq 20 ] && { _warn "API slow to start — continuing anyway"; break; }
  sleep 1
done

# ── 7. Index vault ───────────────────────────────────────────────────────────
_info "Indexing vault..."
"$API_DIR/.venv/bin/minoverse" index

# ── 8. Vault watcher (optional) ───────────────────────────────────────────────
if [ "${ENABLE_WATCHER}" = "true" ]; then
  _info "Starting vault watcher..."
  nohup "$API_DIR/.venv/bin/minoverse" watch \
    > "$WATCHER_LOG" 2>&1 &
  echo $! > "$WATCHER_PID_FILE"
  _ok "Vault watcher started (PID $(cat "$WATCHER_PID_FILE"))"
else
  _info "Vault watcher disabled — skipping"
fi

# ── 9. Dramatiq enrichment worker (optional) ─────────────────────────────────
WORKER_PID_FILE="$RUN_DIR/worker.pid"
WORKER_LOG="$RUN_DIR/worker.log"
if [ "${ENABLE_WORKER}" = "true" ]; then
  _info "Starting enrichment worker..."
  nohup "$API_DIR/.venv/bin/python" -m dramatiq src.workers \
    > "$WORKER_LOG" 2>&1 &
  echo $! > "$WORKER_PID_FILE"
  _ok "Enrichment worker started (PID $(cat "$WORKER_PID_FILE"))"
else
  _info "Enrichment worker disabled — skipping"
fi
cd "$ROOT"

# ── 10. Web dev server ────────────────────────────────────────────────────────
WEB_PID_FILE="$RUN_DIR/web.pid"
WEB_LOG="$RUN_DIR/web.log"
_info "Starting web UI (port 3000)..."
cd "$ROOT/apps/web"
nohup npm run dev > "$WEB_LOG" 2>&1 &
echo $! > "$WEB_PID_FILE"
_ok "Web UI started (PID $(cat "$WEB_PID_FILE"))"
cd "$ROOT"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Minoverse is running 🚀"
echo ""
echo "  API       →  http://localhost:8000"
echo "  API docs  →  http://localhost:8000/docs"
echo "  Web UI    →  http://localhost:3000"
echo "  Logs      →  .minoverse/api.log  |  .minoverse/watcher.log  |  .minoverse/worker.log  |  .minoverse/web.log"
echo ""
echo "  make stop      — stop everything"
echo "  make status    — check what's running"
echo "  make logs-api  — tail API logs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

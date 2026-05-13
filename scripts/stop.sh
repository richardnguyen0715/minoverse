#!/usr/bin/env bash
# stop.sh — Stop the full Minoverse development stack.
#
# Steps (in order):
#   1. Stop the vault watcher (by PID)
#   2. Stop the API server (by PID)
#   3. Stop Docker Compose infrastructure
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT/infra"
RUN_DIR="$ROOT/.minoverse"

_info() { echo "🔷 $*"; }
_ok()   { echo "✅ $*"; }
_skip() { echo "   ⏭  $*"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Stopping Minoverse"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 0. Enrichment worker ─────────────────────────────────────────────────────
WORKER_PID_FILE="$RUN_DIR/worker.pid"
if [ -f "$WORKER_PID_FILE" ]; then
  WORKER_PID=$(cat "$WORKER_PID_FILE")
  if kill -0 "$WORKER_PID" 2>/dev/null; then
    kill "$WORKER_PID"
    _ok "Enrichment worker stopped (PID $WORKER_PID)"
  else
    _skip "Enrichment worker was not running (stale PID $WORKER_PID)"
  fi
  rm -f "$WORKER_PID_FILE"
else
  _skip "No enrichment worker PID file found"
fi

# ── 0b. Web UI ───────────────────────────────────────────────────────────────
WEB_PID_FILE="$RUN_DIR/web.pid"
if [ -f "$WEB_PID_FILE" ]; then
  WEB_PID=$(cat "$WEB_PID_FILE")
  if kill -0 "$WEB_PID" 2>/dev/null; then
    kill "$WEB_PID"
    _ok "Web UI stopped (PID $WEB_PID)"
  else
    _skip "Web UI was not running (stale PID $WEB_PID)"
  fi
  rm -f "$WEB_PID_FILE"
else
  _skip "No web UI PID file found"
fi

# ── 1. Vault watcher ─────────────────────────────────────────────────────────
WATCHER_PID_FILE="$RUN_DIR/watcher.pid"
if [ -f "$WATCHER_PID_FILE" ]; then
  WATCHER_PID=$(cat "$WATCHER_PID_FILE")
  if kill -0 "$WATCHER_PID" 2>/dev/null; then
    kill "$WATCHER_PID"
    _ok "Vault watcher stopped (PID $WATCHER_PID)"
  else
    _skip "Vault watcher was not running (stale PID $WATCHER_PID)"
  fi
  rm -f "$WATCHER_PID_FILE"
else
  _skip "No vault watcher PID file found"
fi

# ── 2. API server ────────────────────────────────────────────────────────────
API_PID_FILE="$RUN_DIR/api.pid"
if [ -f "$API_PID_FILE" ]; then
  API_PID=$(cat "$API_PID_FILE")
  if kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID"
    _ok "API server stopped (PID $API_PID)"
  else
    _skip "API server was not running (stale PID $API_PID)"
  fi
  rm -f "$API_PID_FILE"
else
  _skip "No API PID file found"
fi

# ── 3. Infrastructure ────────────────────────────────────────────────────────
_info "Stopping infrastructure (postgres, redis, ollama)..."
cd "$INFRA_DIR"
docker compose stop
_ok "Infrastructure stopped"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Minoverse stopped"
echo "  Run 'make start' to start again"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

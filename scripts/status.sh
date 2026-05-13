#!/usr/bin/env bash
# status.sh — Show the running status of all Minoverse processes and services.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT/infra"
RUN_DIR="$ROOT/.minoverse"

_running() { echo "  🟢 $*"; }
_stopped() { echo "  🔴 $*"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Minoverse Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── API server ───────────────────────────────────────────────────────────────
API_PID_FILE="$RUN_DIR/api.pid"
if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
  _running "API server    http://localhost:8000   (PID $(cat "$API_PID_FILE"))"
else
  _stopped "API server    not running"
fi

# ── Vault watcher ────────────────────────────────────────────────────────────
WATCHER_PID_FILE="$RUN_DIR/watcher.pid"
if [ -f "$WATCHER_PID_FILE" ] && kill -0 "$(cat "$WATCHER_PID_FILE")" 2>/dev/null; then
  _running "Vault watcher running             (PID $(cat "$WATCHER_PID_FILE"))"
else
  _stopped "Vault watcher not running"
fi

# ── Enrichment worker ─────────────────────────────────────────────────────────
WORKER_PID_FILE="$RUN_DIR/worker.pid"
if [ -f "$WORKER_PID_FILE" ] && kill -0 "$(cat "$WORKER_PID_FILE")" 2>/dev/null; then
  _running "Enrich worker running             (PID $(cat "$WORKER_PID_FILE"))"
else
  _stopped "Enrich worker not running"
fi

# ── Web UI ───────────────────────────────────────────────────────────────────
WEB_PID_FILE="$RUN_DIR/web.pid"
if [ -f "$WEB_PID_FILE" ] && kill -0 "$(cat "$WEB_PID_FILE")" 2>/dev/null; then
  _running "Web UI        http://localhost:3000   (PID $(cat "$WEB_PID_FILE"))"
else
  _stopped "Web UI        not running"
fi

# ── Docker services ──────────────────────────────────────────────────────────
echo ""
echo "  Docker services:"
cd "$INFRA_DIR"
docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null \
  | tail -n +2 \
  | while IFS= read -r line; do
      if echo "$line" | grep -qiE "Up|running|healthy"; then
        echo "    🟢 $line"
      else
        echo "    🔴 $line"
      fi
    done

echo ""
echo "  Logs:  .minoverse/api.log  |  .minoverse/watcher.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

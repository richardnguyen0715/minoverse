# Issue 006 — Stale PID When Using `uv run` to Start Background Processes

**Category:** DevOps / Process Management  
**Fixed in:** Phase 1 unified start/stop system  
**Files changed:** `scripts/start.sh`

---

## Symptom

`make stop` doesn't kill the API server or watcher. `make status` shows them as "not running" even though the process is clearly alive (port 8000 is occupied, `ps aux` shows uvicorn). Re-running `make start` says "already running" or starts a second copy.

---

## Root Cause

`uv run <command>` is a **launcher process**. It:

1. Spawns a child (uvicorn, minoverse, etc.)
2. Waits for the child to start
3. **Exits itself**

When you capture `$!` after `nohup uv run uvicorn ... &`, you capture the PID of the `uv` launcher process — which exits within milliseconds. The actual uvicorn process gets a different PID as a grandchild.

```bash
# ❌ Broken — $! is the uv launcher PID, which is already dead
nohup uv run uvicorn src.main:app --port 8000 &
echo $! > api.pid   # stale PID; kill won't work
```

`stop.sh` then reads the stale PID, `kill` fails silently (process doesn't exist), and uvicorn keeps running as an orphan.

---

## Fix

Run the **venv binaries directly**, bypassing `uv run`. This makes the process you launched the actual server, so `$!` is the correct PID:

```bash
# ✅ Fixed — run the venv binary directly; $! is uvicorn's real PID
cd "$API_DIR"
nohup "$API_DIR/.venv/bin/uvicorn" src.main:app --host 0.0.0.0 --port 8000 --reload \
  > "$API_LOG" 2>&1 &
echo $! > "$API_PID_FILE"   # correct PID
```

Same pattern for the CLI watcher:

```bash
nohup "$API_DIR/.venv/bin/minoverse" watch > "$WATCHER_LOG" 2>&1 &
echo $! > "$WATCHER_PID_FILE"
```

And for the Dramatiq worker:

```bash
nohup "$API_DIR/.venv/bin/python" -m dramatiq src.enrichment.workers.enrichment_worker \
  > "$WORKER_LOG" 2>&1 &
echo $! > "$WORKER_PID_FILE"
```

---

## Prevention Checklist

- [ ] **Never** use `uv run <binary> &` with `$!` PID capture for background daemon processes.
- [ ] Always use `.venv/bin/<binary>` directly when you need a stable, killable PID.
- [ ] `uv run` is fine for one-shot commands (`uv run alembic upgrade head`, `uv run pytest`, etc.).
- [ ] PID files live in `.minoverse/` (`api.pid`, `watcher.pid`, `worker.pid`, `web.pid`). `stop.sh` reads them with `kill -0 <pid>` to check liveness before killing.
- [ ] Verify PIDs are correct after `make start` by running `make status` and cross-checking with `ps aux | grep uvicorn`.

# Issue 003 — Wrong `.env` Loaded: Uvicorn CWD Determines Pydantic Settings Source

**Category:** DevOps / Configuration  
**Fixed in:** `35b5fd0`  
**Files changed:** `scripts/start.sh`

---

## Symptom

API server fails to start with:

```
pydantic_core._pydantic_core.ValidationError: 3 validation errors for Settings
postgres_user
  Extra inputs are not permitted [type=extra_forbidden, ...]
postgres_password
  Extra inputs are not permitted [type=extra_forbidden, ...]
postgres_db
  Extra inputs are not permitted [type=extra_forbidden, ...]
```

`curl http://localhost:8000/health` returns nothing (connection refused or empty).

---

## Root Cause

`pydantic-settings` resolves `env_file = ".env"` **relative to the process's current working directory (cwd)**, not relative to the Python file or package.

The project has **two** `.env` files:

| File | Purpose | Contains |
|---|---|---|
| `.env` (root) | Docker Compose / infra | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, ... |
| `apps/api/.env` | FastAPI / pydantic Settings | `DATABASE_URL`, `REDIS_URL`, `VAULT_PATH`, ... |

When uvicorn is launched from the **project root** (e.g. with `--app-dir apps/api`), its cwd is `/minoverse/`. Pydantic-settings finds `/minoverse/.env` (the infra file) and tries to load `POSTGRES_USER` etc. into `Settings`, which rejects them because `extra = "forbid"`.

```bash
# ❌ Broken — cwd is project root
nohup uvicorn src.main:app --app-dir apps/api --port 8000 &
# pydantic reads: /minoverse/.env  ← WRONG file
```

---

## Fix

`cd` into `apps/api` **before** starting uvicorn (step 5) and **stay there** through all Python steps (7 index, 8 watcher, 9 worker). Only `cd "$ROOT"` after step 9, before the web UI step:

```bash
# ✅ Fixed — in start.sh
cd "$API_DIR"   # /minoverse/apps/api

# step 5 — uvicorn
nohup "$API_DIR/.venv/bin/uvicorn" src.main:app ...

# step 7 — index (still in API_DIR)
"$API_DIR/.venv/bin/minoverse" index

# step 8 — watcher (still in API_DIR)
nohup "$API_DIR/.venv/bin/minoverse" watch ...

# step 9 — worker (still in API_DIR)
nohup "$API_DIR/.venv/bin/python" -m dramatiq ...

cd "$ROOT"  # back to root only before web UI step 10
# pydantic reads: /minoverse/apps/api/.env  ← correct file for all API steps
```

---

## Prevention Checklist

- [ ] Always `cd` to the app directory before launching long-running Python processes that use pydantic-settings with relative `env_file`.
- [ ] Never use `--app-dir` as a substitute for changing cwd — it only modifies `sys.path`, not the working directory.
- [ ] Keep the root `.env` for Docker Compose only; keep `apps/api/.env` for the FastAPI process only. They must not overlap in key names.
- [ ] The symptom is `extra_forbidden` on infra-only keys (`POSTGRES_*`). If you see that, check which `.env` pydantic is actually loading.
- [ ] To debug: add `print(Settings.model_config.get("env_file"))` and `print(os.getcwd())` at the top of `config.py` temporarily.

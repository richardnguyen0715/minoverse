# Issue 001 — CORS Missing: Browser `TypeError: Failed to fetch`

**Category:** Backend / Web UI  
**Fixed in:** `35b5fd0`  
**Files changed:** `apps/api/src/main.py`

---

## Symptom

Browser console shows:

```
Console TypeError
Failed to fetch
  src/lib/api.ts (6:21) @ apiFetch
```

The call stack ends at `fetch(...)` inside `apiFetch`. The error is a **network-level** `TypeError`, not an HTTP 4xx/5xx. All page data is empty. The API responds normally when called directly with `curl`.

---

## Root Cause

The Next.js web app (`http://localhost:3000`) makes cross-origin requests to the FastAPI backend (`http://localhost:8000`). Browsers enforce the **Same-Origin Policy** and block these unless the server explicitly opts in via CORS headers.

FastAPI does **not** add CORS headers by default. `CORSMiddleware` was never added to `src/main.py`, so every browser request was silently rejected before reaching any route handler.

```python
# main.py — MISSING before the fix
# No CORSMiddleware → all browser fetch() calls fail
```

---

## Fix

Add `CORSMiddleware` in `create_app()` **before** router registration:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Verify it's working:

```bash
curl -s -D - -o /dev/null -H "Origin: http://localhost:3000" http://localhost:8000/health \
  | grep -i "access-control"
# access-control-allow-origin: http://localhost:3000  ← must appear
```

---

## Prevention Checklist

- [ ] Whenever adding a web frontend that calls the API from a browser, immediately add `CORSMiddleware` to `main.py`.
- [ ] Add the web origin (`http://localhost:3000`) to `allow_origins`. Do **not** use `["*"]` with `allow_credentials=True` (browsers reject that combination).
- [ ] If adding a staging/production URL, add it to the list too.
- [ ] The symptom is always `TypeError: Failed to fetch` (not a 403 or 401) — `curl` works fine but the browser doesn't.

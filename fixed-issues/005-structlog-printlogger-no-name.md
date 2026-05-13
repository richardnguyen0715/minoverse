# Issue 005 — Structlog `PrintLogger` Has No Attribute `name`

**Category:** Backend / Logging  
**Fixed in:** Phase 1 fix  
**Files changed:** `apps/api/src/core/logging.py`

---

## Symptom

Any call to a structlog logger (`.info()`, `.error()`, etc.) crashes with:

```
AttributeError: 'PrintLogger' object has no attribute 'name'
  File "structlog/stdlib.py", line 838, in add_logger_name
      event_dict["logger"] = logger.name
```

The full traceback runs through `structlog._base._proxy_to_logger` →  `_process_event` → `add_logger_name`.

---

## Root Cause

The `structlog.stdlib.add_logger_name` processor reads `logger.name` from the underlying logger. This attribute exists on `logging.Logger` (stdlib) objects but **not** on structlog's own `PrintLogger`.

If structlog is configured with `logger_factory=structlog.PrintLoggerFactory()`, it creates `PrintLogger` instances, which are simple wrappers around `sys.stdout` with no `.name` attribute. Combining `add_logger_name` with `PrintLoggerFactory` is incompatible.

```python
# ❌ Broken — PrintLogger has no .name
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,  # needs logger.name
        ...
    ],
    logger_factory=structlog.PrintLoggerFactory(),  # gives PrintLogger
)
```

---

## Fix

Switch to `structlog.stdlib.LoggerFactory()`, which creates stdlib `logging.Logger` instances that have `.name`:

```python
# ✅ Fixed
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,   # now works: logger.name exists
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),   # stdlib Logger
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

---

## Prevention Checklist

- [ ] Always pair `add_logger_name` with `stdlib.LoggerFactory()`.
- [ ] Use `PrintLoggerFactory` only in tests or scripts where you explicitly don't need `add_logger_name`.
- [ ] Standard configuration for this project: `stdlib.LoggerFactory()` + `stdlib.BoundLogger` + `add_log_level` + `add_logger_name` + `TimeStamper` + `JSONRenderer`.
- [ ] Check `apps/api/src/core/logging.py` as the canonical structlog configuration reference.

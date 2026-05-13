# Issue 011: Gemini Free-Tier Quota Exhausted — All API Calls Fail

## Status
Observed (unresolved)

## Symptom
All AI enrichment tasks (`extract_entities`, `generate_tags`) return `success=False`.  
Worker logs show repeated `gemini_quota_error` warnings followed by `*_skill_failed` errors:

```
[warning] gemini_quota_error   attempt=1  key_index=0  model=gemini-2.0-flash  retry_in=59.0
[warning] gemini_quota_error   attempt=2  key_index=0  model=gemini-2.0-flash  retry_in=59.0
[warning] gemini_quota_error   attempt=3  key_index=0  model=gemini-2.0-flash  retry_in=0.0
[warning] extract_entities_skill_failed  error="Gemini quota exhausted after 3 retries: ..."
[info   ] ai_call  model=gemini-2.0-flash  success=False  latency_ms=~60000–120000
```

## Root Cause
The system launched with 5 Gemini API keys (`key_count=5`, `auth=api_keys`) but **all keys are on the free tier** and their quotas were simultaneously exhausted:

| Quota violated | Quota ID |
|---|---|
| Input tokens per minute | `GenerateContentInputTokensPerModelPerMinute-FreeTier` |
| Requests per minute | `GenerateRequestsPerMinutePerProjectPerModel-FreeTier` |
| Requests per day | `GenerateRequestsPerDayPerProjectPerModel-FreeTier` |

The daily per-project-per-model cap (`limit: 0` in the error body means the limit has been fully consumed) caused all retries to also fail immediately — the 59-second `retryDelay` from the API only addresses the per-minute bucket; the per-day bucket does not recover until midnight (UTC).

Key rotation did not help because all keys share the same exhaustion state (same project quota pool and/or individually depleted free allocations).

## Timeline (from log, 2026-05-10)
- `03:08:22` — First `429 RESOURCE_EXHAUSTED` on `gemini-2.0-flash`
- `03:08–03:11` — Retries cycle with 59 s back-off, all fail
- `03:11:59` — `extract_entities_skill_failed` after 3 retries (~60 s total latency)
- `03:12:00` — `generate_tags_skill_failed` after 3 retries (~76 s total latency)
- `03:13:59` — Further enrichment jobs also fail; worker continues consuming queue items with no AI output

## Fix / Remediation Options

1. **Upgrade at least one key to a paid tier** — Free-tier daily cap resets at midnight UTC; a paid key has no hard daily cap and higher RPM limits. Add one paid key and promote it as the primary; keep free keys as low-priority fallback.

2. **Track per-key daily exhaustion state** — When a key receives a day-quota violation, mark it as `exhausted_until=next_midnight` in Redis and skip it during rotation instead of burning retry budget retrying it.

3. **Fall back to Ollama on quota exhaustion** — If all Gemini keys are marked exhausted, route the task to the local Ollama provider (already present in the codebase) rather than failing the skill entirely.

4. **Spread keys across different Google projects** — Free-tier quota is per-project-per-model. Keys from separate GCP projects have independent daily budgets.

## Prevention Checklist
- [ ] At least one paid-tier Gemini key in production rotation
- [ ] Per-key quota state persisted in Redis with TTL until quota reset (midnight UTC)
- [ ] Retry logic skips keys already known to be day-quota-exhausted
- [ ] Ollama used as fallback provider when all remote keys are exhausted
- [ ] Alert/metric emitted when `gemini_quota_error` exceeds threshold, before full exhaustion

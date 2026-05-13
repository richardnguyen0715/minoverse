# Issue 008: Dramatiq Dual-Broker — ActorNotFound at Runtime

## Status
Resolved

## Symptom
```
dramatiq.errors.ActorNotFound: enrich_resource
```
Worker boots successfully, receives messages, but immediately moves them to the DLQ.  
All enrichment/graph jobs silently fail. The `enrich_resource` actor exists in code but is "not found" at runtime.

## Root Cause
Each worker module (`enrichment_worker.py`, `graph_worker.py`) called `dramatiq.set_broker()` independently:

```python
# enrichment_worker.py
broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(broker)  # registers enrich_resource on broker_1

# graph_worker.py  
broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(broker)  # REPLACES global broker → broker_1 actors lost!
```

When `src/workers.py` imported both modules, the second `set_broker()` call replaced the first. The `enrich_resource` actor was registered on the now-discarded `broker_1`, so `broker_2` had no record of it.

## Fix
Centralize broker setup in `src/workers.py` **before** any actor module is imported:

```python
# src/workers.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from src.core.config import settings

broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(broker)  # set ONCE before actor imports

from src.enrichment.workers.enrichment_worker import enrich_resource  # noqa
from src.graph.workers.graph_worker import build_graph_for_resource   # noqa
```

Remove `dramatiq.set_broker()` from all individual worker modules.

## Prevention Checklist
- [ ] Broker setup happens exactly once, in the worker entry-point module
- [ ] Individual actor modules use `@dramatiq.actor` without calling `set_broker()`
- [ ] Verify with: `python -c "import src.workers as w; import dramatiq; print(dramatiq.get_broker().actors.keys())"`

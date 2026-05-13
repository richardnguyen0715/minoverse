"""Dramatiq worker entry point — sets up the broker then discovers all actors.

The broker MUST be created and set globally before any actor module is imported;
otherwise each actor module that calls dramatiq.set_broker() would overwrite the
previous one, causing ActorNotFound errors at runtime.
"""
import dramatiq
from dramatiq.brokers.redis import RedisBroker

from src.core.config import settings

# ── Single shared broker ──────────────────────────────────────────────────────
broker = RedisBroker(url=settings.redis_url)
dramatiq.set_broker(broker)

# ── Actor discovery (imported AFTER broker is set) ────────────────────────────
from src.enrichment.workers.enrichment_worker import enrich_resource  # noqa: F401
from src.graph.workers.graph_worker import build_graph_for_resource  # noqa: F401

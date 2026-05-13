"""Dramatiq graph worker — builds the knowledge graph for a single resource.

Runs entity promotion (from AI enrichments) and relation generation (via Ollama)
in a single idempotent background job. Shares the same Dramatiq broker and
worker process as the enrichment worker (discovered via src/workers.py imports).

The broker is set up in ``src.workers`` before this module is imported,
so no broker setup is performed here.
"""
import asyncio

import dramatiq
import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)


@dramatiq.actor(max_retries=3, min_backoff=5000, time_limit=300_000)
def build_graph_for_resource(resource_id: str) -> None:
    """Dramatiq actor: build the knowledge graph for a single resource.

    Args:
        resource_id: String representation of the resource UUID.
    """
    asyncio.run(_build_graph_async(resource_id))


async def _build_graph_async(resource_id: str) -> None:
    """Async implementation: promotes entities then generates relations.

    Creates a fresh DB engine per invocation to avoid asyncpg
    "another operation is in progress" errors in Dramatiq worker threads.

    Args:
        resource_id: String representation of the resource UUID.
    """
    import uuid as _uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from src.ai import get_llm_runtime
    from src.core.config import settings
    from src.graph.services.entity_promotion_service import promote_entities_from_enrichment
    from src.graph.services.relation_generation_service import generate_relations_for_resource

    rid = _uuid.UUID(resource_id)
    runtime = get_llm_runtime()

    engine = create_async_engine(
        settings.database_url,
        pool_size=2,
        max_overflow=0,
        pool_pre_ping=True,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with factory() as session:
            entities = await promote_entities_from_enrichment(session, rid)
            relations = await generate_relations_for_resource(session, rid, runtime._provider)
            await session.commit()

        logger.info(
            "graph_worker_completed",
            resource_id=resource_id,
            entities_promoted=len(entities),
            relations_generated=len(relations),
        )
    finally:
        await engine.dispose()

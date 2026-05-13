"""Dramatiq enrichment worker.

Defines the ``enrich_resource`` Dramatiq actor that runs the full AI
enrichment pipeline for a single resource in a background worker process.

The actor is synchronous (Dramatiq requirement) and drives async logic
via ``asyncio.run()``.

The broker is set up in ``src.workers`` before this module is imported,
so no broker setup is performed here.
"""
import asyncio

import dramatiq
import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)


@dramatiq.actor(max_retries=3, min_backoff=5000, time_limit=300_000)
def enrich_resource(resource_id: str) -> None:
    """Dramatiq actor: run AI enrichment for a single resource.

    Args:
        resource_id: String representation of the resource UUID.
    """
    asyncio.run(_enrich_resource_async(resource_id))


async def _enrich_resource_async(resource_id: str) -> None:
    """Async implementation of the enrichment actor.

    Creates a fresh DB engine and session per invocation to avoid
    asyncpg "another operation is in progress" errors when Dramatiq
    worker threads call asyncio.run() with different event loops.

    Args:
        resource_id: String representation of the resource UUID.
    """
    import uuid as _uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from src.ai import get_llm_runtime
    from src.core.config import settings
    from src.enrichment.pipelines.enrichment_pipeline import run_enrichment_for_resource

    rid = _uuid.UUID(resource_id)
    runtime = get_llm_runtime()

    # Create a fresh engine for this invocation — avoids sharing connections
    # across event loops which causes asyncpg InterfaceError.
    engine = create_async_engine(
        settings.database_url,
        pool_size=2,
        max_overflow=0,
        pool_pre_ping=True,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with factory() as session:
            pipeline_result = await run_enrichment_for_resource(
                rid,
                session,
                runtime=runtime,
            )
            await session.commit()

        logger.info(
            "enrichment_worker_completed",
            resource_id=resource_id,
            succeeded=pipeline_result.succeeded,
            failed=pipeline_result.failed,
            skipped_ollama_unavailable=pipeline_result.skipped_ollama_unavailable,
        )
    finally:
        await engine.dispose()

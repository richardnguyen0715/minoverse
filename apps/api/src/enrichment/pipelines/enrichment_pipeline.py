"""Enrichment pipeline orchestrator.

Coordinates all AI enrichment steps for a single resource. Each step
runs independently — a failure in one step is logged as a warning and
does not abort the remaining steps. The pipeline is idempotent: calling
it twice for the same resource produces the same database state via
upserts.

The pipeline does NOT call session.commit(); that is the caller's
responsibility (typically the Dramatiq worker).
"""
import time
import uuid
from dataclasses import dataclass, field

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.ai.skills.extract_entities import run_extract_entities
from src.ai.skills.generate_tags import run_generate_tags
from src.ai.skills.summarize_resource import run_summarize
from src.enrichment.repositories.enrichment_repository import upsert_enrichment
from src.enrichment.schemas.enrichment_schemas import EnrichmentType
from src.enrichment.services.related_service import find_related_resources

logger = structlog.get_logger(__name__)

_CONTENT_QUERY = text(
    """
    SELECT COALESCE(rc.clean_text, rc.raw_markdown, r.title, '') AS body_text
    FROM resources r
    LEFT JOIN resource_contents rc ON rc.resource_id = r.id
    WHERE r.id = :resource_id
    ORDER BY rc.version DESC
    LIMIT 1
    """
)


@dataclass
class EnrichmentPipelineResult:
    """Summary of one pipeline execution.

    Attributes:
        resource_id: UUID of the processed resource.
        succeeded: Names of enrichment types that completed successfully.
        failed: Names of enrichment types that raised an exception.
        skipped_ollama_unavailable: Kept for backward compatibility; always False.
    """

    resource_id: uuid.UUID
    succeeded: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    skipped_ollama_unavailable: bool = False


async def run_enrichment_for_resource(
    resource_id: uuid.UUID,
    session: AsyncSession,
    *,
    runtime: LLMRuntime,
    # Legacy params kept for backward compat — ignored when runtime is provided
    ollama_client: object = None,
    model: str = "qwen3",
) -> EnrichmentPipelineResult:
    """Run all AI enrichment steps for a single resource via LLMRuntime.

    Steps (each independent):
    1. Summary → upserts SUMMARY_CONCISE, SUMMARY_DETAILED, KEY_INSIGHTS
    2. Tagging → upserts AI_TAGS
    3. Entity extraction → upserts ENTITIES
    4. Related resources → upserts RELATED

    Idempotent: repeated calls for the same resource_id produce the
    same database state via ON CONFLICT DO UPDATE.

    Args:
        resource_id: UUID of the resource to enrich.
        session: Active async database session. Caller must commit.
        runtime: LLMRuntime wired to the active AI provider (Gemini/Ollama).
        ollama_client: Ignored; kept for backward compatibility.
        model: Ignored; kept for backward compatibility.

    Returns:
        EnrichmentPipelineResult describing which steps succeeded or failed.
    """
    result = EnrichmentPipelineResult(resource_id=resource_id)

    # Check provider availability
    if not await runtime._provider.is_available():
        logger.warning("ai_provider_unavailable_skipping_enrichment", resource_id=str(resource_id))
        result.skipped_ollama_unavailable = True
        return result

    # Fetch resource content
    content_row = await session.execute(_CONTENT_QUERY, {"resource_id": resource_id})
    content: str = content_row.scalar_one_or_none() or ""

    provider = runtime._provider.provider_name

    # ── Step 1: Summary ───────────────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        summary = await run_summarize(content, runtime)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        await upsert_enrichment(
            session,
            resource_id=resource_id,
            enrichment_type=EnrichmentType.SUMMARY_CONCISE,
            content={"text": summary.concise},
            model_name=provider,
            processing_ms=elapsed_ms,
        )
        await upsert_enrichment(
            session,
            resource_id=resource_id,
            enrichment_type=EnrichmentType.SUMMARY_DETAILED,
            content={"text": summary.detailed},
            model_name=provider,
            processing_ms=elapsed_ms,
        )
        await upsert_enrichment(
            session,
            resource_id=resource_id,
            enrichment_type=EnrichmentType.KEY_INSIGHTS,
            content={"items": summary.key_insights},
            model_name=provider,
            processing_ms=elapsed_ms,
        )
        result.succeeded.extend([
            EnrichmentType.SUMMARY_CONCISE,
            EnrichmentType.SUMMARY_DETAILED,
            EnrichmentType.KEY_INSIGHTS,
        ])
        logger.info("summary_enrichment_done", resource_id=str(resource_id), ms=elapsed_ms)
    except Exception as exc:
        logger.warning("summary_enrichment_failed", resource_id=str(resource_id), error=str(exc))
        result.failed.extend([
            EnrichmentType.SUMMARY_CONCISE,
            EnrichmentType.SUMMARY_DETAILED,
            EnrichmentType.KEY_INSIGHTS,
        ])

    # ── Step 2: Tagging ───────────────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        tags_result = await run_generate_tags(content, runtime)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        await upsert_enrichment(
            session,
            resource_id=resource_id,
            enrichment_type=EnrichmentType.AI_TAGS,
            content={"tags": tags_result.tags},
            model_name=provider,
            processing_ms=elapsed_ms,
        )
        result.succeeded.append(EnrichmentType.AI_TAGS)
        logger.info("tagging_enrichment_done", resource_id=str(resource_id), ms=elapsed_ms)
    except Exception as exc:
        logger.warning("tagging_enrichment_failed", resource_id=str(resource_id), error=str(exc))
        result.failed.append(EnrichmentType.AI_TAGS)

    # ── Step 3: Entity extraction ─────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        entities = await run_extract_entities(content, runtime)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        await upsert_enrichment(
            session,
            resource_id=resource_id,
            enrichment_type=EnrichmentType.ENTITIES,
            content={
                "tools": entities.tools,
                "frameworks": entities.frameworks,
                "papers": entities.papers,
                "methodologies": entities.methodologies,
            },
            model_name=provider,
            processing_ms=elapsed_ms,
        )
        result.succeeded.append(EnrichmentType.ENTITIES)
        logger.info("entity_enrichment_done", resource_id=str(resource_id), ms=elapsed_ms)
    except Exception as exc:
        logger.warning("entity_enrichment_failed", resource_id=str(resource_id), error=str(exc))
        result.failed.append(EnrichmentType.ENTITIES)

    # ── Step 4: Related resources ─────────────────────────────────────────────
    try:
        t0 = time.monotonic()
        related = await find_related_resources(resource_id, session)
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        await upsert_enrichment(
            session,
            resource_id=resource_id,
            enrichment_type=EnrichmentType.RELATED,
            content={"resource_ids": related.resource_ids},
            model_name=provider,
            processing_ms=elapsed_ms,
        )
        result.succeeded.append(EnrichmentType.RELATED)
        logger.info("related_enrichment_done", resource_id=str(resource_id), ms=elapsed_ms)
    except Exception as exc:
        logger.warning("related_enrichment_failed", resource_id=str(resource_id), error=str(exc))
        result.failed.append(EnrichmentType.RELATED)

    return result


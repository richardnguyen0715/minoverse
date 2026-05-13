"""Semantic memory service — extracts durable concepts from resources."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.ai.skills.synthesize_semantic import run_synthesize_semantic
from src.enrichment.entities.ai_enrichment import AiEnrichment
from src.memory.entities.semantic_memory import SemanticMemory
from src.memory.repositories import semantic_repository
from src.retrieval.entities.chunk import ResourceContent

logger = structlog.get_logger(__name__)


async def extract_semantic_from_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
    runtime: LLMRuntime,
) -> SemanticMemory | None:
    """Extract a durable knowledge concept from a resource's content.

    Reads the resource's clean_text (from resource_contents) and/or its
    AI summary (from ai_enrichments) then synthesises a semantic memory.

    Args:
        session: Active async database session.
        resource_id: UUID of the source resource.
        runtime: LLMRuntime for AI synthesis.

    Returns:
        Created SemanticMemory, or None if no usable content found.
    """
    content_parts: list[str] = []

    # Try resource content first
    rc_stmt = select(ResourceContent).where(ResourceContent.resource_id == resource_id)
    rc_result = await session.execute(rc_stmt)
    resource_content = rc_result.scalar_one_or_none()
    if resource_content and resource_content.clean_text:
        content_parts.append(resource_content.clean_text[:3000])

    # Also include AI summary if available
    ae_stmt = (
        select(AiEnrichment)
        .where(
            AiEnrichment.resource_id == resource_id,
            AiEnrichment.enrichment_type == "summary",
            AiEnrichment.is_current.is_(True),
        )
    )
    ae_result = await session.execute(ae_stmt)
    enrichment = ae_result.scalar_one_or_none()
    if enrichment and isinstance(enrichment.content, dict):
        summary = enrichment.content.get("concise") or enrichment.content.get("detailed", "")
        if summary:
            content_parts.append(f"Summary: {summary}")

    if not content_parts:
        logger.info("semantic_extract_no_content", resource_id=str(resource_id))
        return None

    combined = "\n\n".join(content_parts)
    result = await run_synthesize_semantic(combined, runtime)

    if not result.get("concept"):
        logger.warning("semantic_extract_empty_concept", resource_id=str(resource_id))
        return None

    memory = await semantic_repository.create_semantic(
        session,
        concept=result["concept"],
        content=result["content"],
        source_resource_id=resource_id,
    )

    logger.info(
        "semantic_memory_extracted",
        resource_id=str(resource_id),
        memory_id=str(memory.id),
        concept=memory.concept,
    )
    return memory


async def list_semantic_memories(session: AsyncSession) -> list[SemanticMemory]:
    """List all semantic memories ordered by most recent first.

    Args:
        session: Active async database session.

    Returns:
        List of SemanticMemory records.
    """
    return await semantic_repository.list_semantic(session)


async def get_semantic_memory(
    session: AsyncSession,
    memory_id: uuid.UUID,
) -> SemanticMemory | None:
    """Fetch a single semantic memory by primary key.

    Args:
        session: Active async database session.
        memory_id: UUID primary key.

    Returns:
        SemanticMemory or None.
    """
    return await semantic_repository.get_semantic(session, memory_id)

"""Enrichment repository — persistence layer for AI enrichment records.

Provides idempotent upsert and list operations for the ``ai_enrichments``
table. All writes use ON CONFLICT DO UPDATE to remain retry-safe.
"""
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.enrichment.entities.ai_enrichment import AiEnrichment

logger = structlog.get_logger(__name__)


async def upsert_enrichment(
    session: AsyncSession,
    *,
    resource_id: uuid.UUID,
    enrichment_type: str,
    content: dict,  # type: ignore[type-arg]
    model_name: str,
    processing_ms: int,
    prompt_version: str = "v1",
) -> AiEnrichment:
    """Insert or update an enrichment record for a resource.

    Uses ON CONFLICT DO UPDATE keyed on the unique constraint
    ``uq_ai_enrichments_resource_type`` so the operation is idempotent
    and retry-safe.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource being enriched.
        enrichment_type: Enrichment type string (see EnrichmentType).
        content: Dict containing the AI-generated output.
        model_name: Identifier of the model that produced the output.
        processing_ms: Wall-clock generation time in milliseconds.
        prompt_version: Prompt template version (default ``"v1"``).

    Returns:
        The upserted AiEnrichment ORM instance.
    """
    new_id = uuid.uuid4()
    now = datetime.now(tz=timezone.utc)

    stmt = (
        insert(AiEnrichment)
        .values(
            id=new_id,
            resource_id=resource_id,
            enrichment_type=enrichment_type,
            content=content,
            model_name=model_name,
            prompt_version=prompt_version,
            processing_ms=processing_ms,
            is_current=True,
            created_at=now,
            updated_at=now,
        )
        .on_conflict_do_update(
            constraint="uq_ai_enrichments_resource_type",
            set_={
                "content": content,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "processing_ms": processing_ms,
                "is_current": True,
                "updated_at": now,
            },
        )
        .returning(AiEnrichment)
    )

    result = await session.execute(stmt)
    row = result.scalar_one()
    return row


async def list_enrichments_for_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
) -> list[AiEnrichment]:
    """Return all current enrichments for a resource, ordered by type.

    Args:
        session: Active async database session.
        resource_id: UUID of the target resource.

    Returns:
        List of current AiEnrichment records ordered by enrichment_type.
    """
    stmt = (
        select(AiEnrichment)
        .where(
            AiEnrichment.resource_id == resource_id,
            AiEnrichment.is_current.is_(True),
        )
        .order_by(AiEnrichment.enrichment_type)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

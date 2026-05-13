"""FastAPI routes for AI enrichment endpoints.

Provides read access to enrichment records and a manual trigger endpoint
that enqueues a Dramatiq enrichment job.
"""
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.enrichment.repositories.enrichment_repository import (
    list_enrichments_for_resource,
)
from src.enrichment.schemas.enrichment_schemas import EnrichmentOutput, EnrichmentType
from src.enrichment.workers.enrichment_worker import enrich_resource

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.get("/{resource_id}", response_model=list[EnrichmentOutput])
async def list_enrichments(
    resource_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> list[EnrichmentOutput]:
    """List all current AI enrichments for a resource.

    Args:
        resource_id: UUID of the target resource.
        session: Injected async database session.

    Returns:
        List of EnrichmentOutput records ordered by enrichment type.
    """
    records = await list_enrichments_for_resource(session, resource_id)
    return [
        EnrichmentOutput(
            resource_id=str(r.resource_id),
            enrichment_type=EnrichmentType(r.enrichment_type),
            content=r.content,
            model_name=r.model_name,
            prompt_version=r.prompt_version,
            processing_ms=r.processing_ms or 0,
        )
        for r in records
    ]


@router.get("/{resource_id}/{enrichment_type}", response_model=EnrichmentOutput)
async def get_enrichment(
    resource_id: uuid.UUID,
    enrichment_type: str,
    session: AsyncSession = Depends(get_async_session),
) -> EnrichmentOutput:
    """Retrieve a specific enrichment type for a resource.

    Args:
        resource_id: UUID of the target resource.
        enrichment_type: Enrichment type string (e.g. ``"summary_concise"``).
        session: Injected async database session.

    Returns:
        The matching EnrichmentOutput record.

    Raises:
        HTTPException: 404 if no matching enrichment exists.
    """
    records = await list_enrichments_for_resource(session, resource_id)
    for r in records:
        if r.enrichment_type == enrichment_type:
            return EnrichmentOutput(
                resource_id=str(r.resource_id),
                enrichment_type=EnrichmentType(r.enrichment_type),
                content=r.content,
                model_name=r.model_name,
                prompt_version=r.prompt_version,
                processing_ms=r.processing_ms or 0,
            )
    raise HTTPException(
        status_code=404,
        detail=f"No enrichment of type '{enrichment_type}' found for resource {resource_id}",
    )


@router.post("/{resource_id}/trigger", response_model=dict[str, str])
async def trigger_enrichment(resource_id: uuid.UUID) -> dict[str, str]:
    """Manually trigger AI enrichment for a resource by enqueuing a Dramatiq job.

    Args:
        resource_id: UUID of the resource to enrich.

    Returns:
        Dict with ``status`` and ``resource_id`` keys.
    """
    enrich_resource.send(str(resource_id))
    logger.info("enrichment_triggered_via_api", resource_id=str(resource_id))
    return {"status": "queued", "resource_id": str(resource_id)}

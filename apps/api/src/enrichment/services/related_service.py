"""Related resource discovery service.

Finds resources related to a given resource using tag-overlap similarity.
This is a pre-Phase-2 implementation; Phase 2 will upgrade it to use
vector similarity via pgvector.
"""
import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.enrichment.schemas.enrichment_schemas import RelatedResult

logger = structlog.get_logger(__name__)

_TAG_OVERLAP_SQL = text(
    """
    SELECT rt2.resource_id, COUNT(*) AS overlap
    FROM resource_tags rt1
    JOIN resource_tags rt2
        ON rt1.tag_id = rt2.tag_id
        AND rt2.resource_id != rt1.resource_id
    WHERE rt1.resource_id = :resource_id
    GROUP BY rt2.resource_id
    ORDER BY overlap DESC
    LIMIT :limit
    """
)


async def find_related_resources(
    resource_id: uuid.UUID,
    session: AsyncSession,
    *,
    limit: int = 5,
) -> RelatedResult:
    """Find resources most related to the given resource by tag overlap.

    Pre-Phase-2 implementation using tag overlap similarity. Will be
    upgraded to vector similarity in Phase 2.

    Args:
        resource_id: UUID of the target resource.
        session: Active async database session.
        limit: Maximum number of related resources to return.

    Returns:
        RelatedResult containing up to ``limit`` related resource UUIDs.
        Returns empty list on any error.
    """
    try:
        result = await session.execute(
            _TAG_OVERLAP_SQL,
            {"resource_id": resource_id, "limit": limit},
        )
        rows = result.fetchall()
        return RelatedResult(resource_ids=[str(row.resource_id) for row in rows])
    except Exception as exc:
        logger.warning(
            "related_resource_lookup_failed",
            resource_id=str(resource_id),
            error=str(exc),
        )
        return RelatedResult(resource_ids=[])

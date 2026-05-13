"""Entity promotion service — promotes AI-extracted entities into the concept graph.

Reads the ``entities`` AiEnrichment for a resource, upserts each named entity
as a ConceptEntity, and links it to the resource via ResourceEntity.
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.enrichment.entities.ai_enrichment import AiEnrichment
from src.graph.entities.concept_entity import ConceptEntity
from src.graph.repositories.concept_entity_repository import (
    link_resource_entity,
    upsert_concept_entity,
)

logger = structlog.get_logger(__name__)

_VALID_ENTITY_TYPES = frozenset(
    {"concept", "person", "technology", "framework", "organization", "place"}
)


async def promote_entities_from_enrichment(
    session: AsyncSession,
    resource_id: uuid.UUID,
) -> list[ConceptEntity]:
    """Promote AI-extracted entities for a resource into the concept graph.

    Reads the ``entities`` enrichment record, upserts each entity as a
    ConceptEntity (deduplicating by canonical_name + entity_type), and
    creates a ResourceEntity link.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource to promote entities for.

    Returns:
        List of ConceptEntity records that were created or updated.
    """
    stmt = select(AiEnrichment).where(
        AiEnrichment.resource_id == resource_id,
        AiEnrichment.enrichment_type == "entities",
        AiEnrichment.is_current.is_(True),
    )
    result = await session.execute(stmt)
    enrichment = result.scalar_one_or_none()

    if enrichment is None:
        logger.debug("no_entities_enrichment_found", resource_id=str(resource_id))
        return []

    raw_entities: list[dict[str, str]] = enrichment.content.get("entities", [])

    # Phase 3 entity_service stores a categorized format:
    # {"tools": [...], "frameworks": [...], "papers": [...], "methodologies": [...]}
    # Promote each category into the flat {"name": ..., "type": ...} format.
    if not raw_entities:
        _type_map = {
            "tools": "technology",
            "frameworks": "framework",
            "papers": "concept",
            "methodologies": "concept",
        }
        for key, entity_type in _type_map.items():
            for name in enrichment.content.get(key, []):
                name = str(name).strip()
                if name:
                    raw_entities.append({"name": name, "type": entity_type})
    if not raw_entities:
        logger.debug("empty_entities_list", resource_id=str(resource_id))
        return []

    promoted: list[ConceptEntity] = []
    seen: set[tuple[str, str]] = set()

    for item in raw_entities:
        name = (item.get("name") or "").strip()
        entity_type = (item.get("type") or "concept").strip().lower()

        if not name:
            continue
        if entity_type not in _VALID_ENTITY_TYPES:
            entity_type = "concept"

        canonical = name.lower()
        dedup_key = (canonical, entity_type)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        entity = await upsert_concept_entity(
            session,
            name=name,
            entity_type=entity_type,
            description=item.get("description"),
        )
        await link_resource_entity(session, resource_id, entity.id)
        promoted.append(entity)

    logger.info(
        "entities_promoted",
        resource_id=str(resource_id),
        count=len(promoted),
    )
    return promoted

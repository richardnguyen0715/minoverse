"""Repository for concept_relations table."""
import uuid

import structlog
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.graph.entities.concept_entity import ConceptEntity
from src.graph.entities.concept_relation import ConceptRelation
from src.graph.entities.resource_entity import ResourceEntity

logger = structlog.get_logger(__name__)


async def upsert_concept_relation(
    session: AsyncSession,
    *,
    src_id: uuid.UUID,
    dst_id: uuid.UUID,
    relation_type: str,
    weight: float = 1.0,
    resource_id: uuid.UUID | None = None,
    generated_by: str = "ollama",
) -> ConceptRelation:
    """Insert or update a directed relation keyed on (src, dst, relation_type).

    Args:
        session: Active async database session.
        src_id: Source concept entity UUID.
        dst_id: Target concept entity UUID.
        relation_type: One of the RelationType enum values.
        weight: Edge weight (default 1.0).
        resource_id: Optional origin resource UUID.
        generated_by: Generator tag (e.g. ``"ollama"``, ``"wiki_link"``).

    Returns:
        The upserted ConceptRelation ORM instance.
    """
    stmt = (
        insert(ConceptRelation)
        .values(
            id=uuid.uuid4(),
            source_entity_id=src_id,
            target_entity_id=dst_id,
            relation_type=relation_type,
            weight=weight,
            source_resource_id=resource_id,
            generated_by=generated_by,
        )
        .on_conflict_do_update(
            constraint="uq_concept_relations_src_dst_type",
            set_={
                "weight": weight,
                "source_resource_id": resource_id,
                "generated_by": generated_by,
            },
        )
        .returning(ConceptRelation)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def list_neighbors(
    session: AsyncSession,
    entity_id: uuid.UUID,
    depth: int = 1,
) -> list[tuple[ConceptEntity, ConceptRelation]]:
    """Return immediate neighbors (depth=1) of an entity.

    Args:
        session: Active async database session.
        entity_id: UUID of the focal entity.
        depth: Traversal depth (currently only depth=1 is supported).

    Returns:
        List of (ConceptEntity, ConceptRelation) tuples for each neighbor.
    """
    stmt = (
        select(ConceptEntity, ConceptRelation)
        .join(
            ConceptRelation,
            or_(
                ConceptRelation.source_entity_id == entity_id,
                ConceptRelation.target_entity_id == entity_id,
            ),
        )
        .where(
            or_(
                ConceptRelation.source_entity_id == entity_id,
                ConceptRelation.target_entity_id == entity_id,
            ),
            ConceptEntity.id != entity_id,
        )
    )
    result = await session.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]


async def list_relations_for_entity(
    session: AsyncSession,
    entity_id: uuid.UUID,
) -> list[ConceptRelation]:
    """Return all relations where entity is source or target.

    Args:
        session: Active async database session.
        entity_id: UUID of the focal entity.

    Returns:
        List of ConceptRelation records.
    """
    stmt = select(ConceptRelation).where(
        or_(
            ConceptRelation.source_entity_id == entity_id,
            ConceptRelation.target_entity_id == entity_id,
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_full_graph(
    session: AsyncSession,
) -> tuple[list[ConceptEntity], list[ConceptRelation]]:
    """Fetch all entities and all relations for the global graph view.

    Args:
        session: Active async database session.

    Returns:
        Tuple of (entities, relations).
    """
    entities_result = await session.execute(
        select(ConceptEntity).order_by(ConceptEntity.canonical_name)
    )
    relations_result = await session.execute(select(ConceptRelation))
    return (
        list(entities_result.scalars().all()),
        list(relations_result.scalars().all()),
    )


async def get_resource_graph(
    session: AsyncSession,
    resource_id: uuid.UUID,
) -> tuple[list[ConceptEntity], list[ConceptRelation]]:
    """Fetch entities and relations scoped to a single resource.

    Returns all entities linked to the resource and all relations where
    both endpoints are in that entity set.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource.

    Returns:
        Tuple of (entities, relations).
    """
    entity_stmt = (
        select(ConceptEntity)
        .join(ResourceEntity, ResourceEntity.entity_id == ConceptEntity.id)
        .where(ResourceEntity.resource_id == resource_id)
    )
    entity_result = await session.execute(entity_stmt)
    entities = list(entity_result.scalars().all())

    if not entities:
        return entities, []

    entity_ids = {e.id for e in entities}
    relation_stmt = select(ConceptRelation).where(
        ConceptRelation.source_entity_id.in_(entity_ids),
        ConceptRelation.target_entity_id.in_(entity_ids),
    )
    relation_result = await session.execute(relation_stmt)
    return entities, list(relation_result.scalars().all())

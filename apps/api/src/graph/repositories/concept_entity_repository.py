"""Repository for concept_entities and resource_entities tables."""
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.graph.entities.concept_entity import ConceptEntity
from src.graph.entities.resource_entity import ResourceEntity

logger = structlog.get_logger(__name__)


def _canonical(name: str) -> str:
    """Normalize entity name to a canonical dedup key."""
    return name.strip().lower()


async def upsert_concept_entity(
    session: AsyncSession,
    *,
    name: str,
    entity_type: str,
    description: str | None = None,
) -> ConceptEntity:
    """Insert or update a concept entity keyed on (canonical_name, entity_type).

    Args:
        session: Active async database session.
        name: Display name of the entity.
        entity_type: One of the EntityType enum values.
        description: Optional plain-text description.

    Returns:
        The upserted ConceptEntity ORM instance.
    """
    canonical = _canonical(name)
    stmt = (
        insert(ConceptEntity)
        .values(
            id=uuid.uuid4(),
            name=name,
            entity_type=entity_type,
            canonical_name=canonical,
            description=description,
        )
        .on_conflict_do_update(
            constraint="uq_concept_entities_canonical_type",
            set_={
                "name": name,
                "description": description,
            },
        )
        .returning(ConceptEntity)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def link_resource_entity(
    session: AsyncSession,
    resource_id: uuid.UUID,
    entity_id: uuid.UUID,
) -> None:
    """Create a resource→entity link if it doesn't already exist.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource.
        entity_id: UUID of the concept entity.
    """
    stmt = (
        insert(ResourceEntity)
        .values(resource_id=resource_id, entity_id=entity_id)
        .on_conflict_do_nothing()
    )
    await session.execute(stmt)


async def list_concept_entities(
    session: AsyncSession,
    entity_type: str | None = None,
) -> list[ConceptEntity]:
    """List concept entities, optionally filtered by type.

    Args:
        session: Active async database session.
        entity_type: Optional filter on entity_type column.

    Returns:
        List of ConceptEntity records ordered by canonical_name.
    """
    stmt = select(ConceptEntity).order_by(ConceptEntity.canonical_name)
    if entity_type is not None:
        stmt = stmt.where(ConceptEntity.entity_type == entity_type)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_concept_entity(
    session: AsyncSession,
    entity_id: uuid.UUID,
) -> ConceptEntity | None:
    """Fetch a single concept entity by primary key.

    Args:
        session: Active async database session.
        entity_id: UUID primary key.

    Returns:
        ConceptEntity or None if not found.
    """
    return await session.get(ConceptEntity, entity_id)


async def get_entities_for_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
) -> list[ConceptEntity]:
    """Return all concept entities linked to a resource.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource.

    Returns:
        List of linked ConceptEntity records.
    """
    stmt = (
        select(ConceptEntity)
        .join(ResourceEntity, ResourceEntity.entity_id == ConceptEntity.id)
        .where(ResourceEntity.resource_id == resource_id)
        .order_by(ConceptEntity.canonical_name)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

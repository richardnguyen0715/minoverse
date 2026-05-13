"""Repository for semantic_memories table."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.entities.semantic_memory import SemanticMemory

logger = structlog.get_logger(__name__)


async def create_semantic(
    session: AsyncSession,
    *,
    concept: str,
    content: str,
    source_resource_id: uuid.UUID | None = None,
) -> SemanticMemory:
    """Create a new semantic memory record.

    Args:
        session: Active async database session.
        concept: Short concept name.
        content: Durable knowledge content.
        source_resource_id: Optional originating resource UUID.

    Returns:
        The created SemanticMemory ORM instance.
    """
    sm = SemanticMemory(
        id=uuid.uuid4(),
        concept=concept,
        content=content,
        source_resource_id=source_resource_id,
    )
    session.add(sm)
    await session.flush()
    logger.info("semantic_memory_created", memory_id=str(sm.id), concept=concept)
    return sm


async def get_semantic(
    session: AsyncSession,
    memory_id: uuid.UUID,
) -> SemanticMemory | None:
    """Fetch a semantic memory by primary key.

    Args:
        session: Active async database session.
        memory_id: UUID primary key.

    Returns:
        SemanticMemory or None.
    """
    return await session.get(SemanticMemory, memory_id)


async def list_semantic(session: AsyncSession) -> list[SemanticMemory]:
    """Return all semantic memories ordered by most recent first.

    Args:
        session: Active async database session.

    Returns:
        List of SemanticMemory records.
    """
    stmt = select(SemanticMemory).order_by(SemanticMemory.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_for_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
) -> list[SemanticMemory]:
    """Return semantic memories derived from a specific resource.

    Args:
        session: Active async database session.
        resource_id: UUID of the source resource.

    Returns:
        List of SemanticMemory records for this resource.
    """
    stmt = (
        select(SemanticMemory)
        .where(SemanticMemory.source_resource_id == resource_id)
        .order_by(SemanticMemory.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

"""Repository for episodic_memories table."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.entities.episodic_memory import EpisodicMemory

logger = structlog.get_logger(__name__)


async def create_episode(
    session: AsyncSession,
    *,
    title: str,
    content: str,
    session_id: uuid.UUID | None = None,
    resource_ids: list | None = None,
) -> EpisodicMemory:
    """Create a new episodic memory record.

    Args:
        session: Active async database session.
        title: Short title for the episode.
        content: Detailed narrative content.
        session_id: Optional originating memory session UUID.
        resource_ids: Optional list of related resource UUIDs (as strings).

    Returns:
        The created EpisodicMemory ORM instance.
    """
    ep = EpisodicMemory(
        id=uuid.uuid4(),
        title=title,
        content=content,
        session_id=session_id,
        resource_ids=resource_ids,
    )
    session.add(ep)
    await session.flush()
    logger.info("episodic_memory_created", episode_id=str(ep.id), title=title)
    return ep


async def get_episode(
    session: AsyncSession,
    episode_id: uuid.UUID,
) -> EpisodicMemory | None:
    """Fetch an episodic memory by primary key.

    Args:
        session: Active async database session.
        episode_id: UUID primary key.

    Returns:
        EpisodicMemory or None.
    """
    return await session.get(EpisodicMemory, episode_id)


async def list_episodes(session: AsyncSession) -> list[EpisodicMemory]:
    """Return all episodic memories ordered by most recent first.

    Args:
        session: Active async database session.

    Returns:
        List of EpisodicMemory records.
    """
    stmt = select(EpisodicMemory).order_by(EpisodicMemory.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())

"""Repository for memory_sessions and memory_turns tables."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.memory.entities.memory_session import MemorySession
from src.memory.entities.memory_turn import MemoryTurn

logger = structlog.get_logger(__name__)


async def create_session(
    session: AsyncSession,
    *,
    title: str,
    context: dict | None = None,
) -> MemorySession:
    """Create a new memory session.

    Args:
        session: Active async database session.
        title: Human-readable session title.
        context: Optional arbitrary context metadata.

    Returns:
        The created MemorySession ORM instance.
    """
    ms = MemorySession(id=uuid.uuid4(), title=title, context=context)
    session.add(ms)
    await session.flush()
    logger.info("memory_session_created", session_id=str(ms.id), title=title)
    return ms


async def get_session(
    session: AsyncSession,
    session_id: uuid.UUID,
) -> MemorySession | None:
    """Fetch a memory session by primary key.

    Args:
        session: Active async database session.
        session_id: UUID primary key.

    Returns:
        MemorySession or None.
    """
    return await session.get(MemorySession, session_id)


async def get_session_with_turns(
    session: AsyncSession,
    session_id: uuid.UUID,
) -> MemorySession | None:
    """Fetch a memory session with its turns eagerly loaded.

    Args:
        session: Active async database session.
        session_id: UUID primary key.

    Returns:
        MemorySession with turns or None.
    """
    stmt = (
        select(MemorySession)
        .options(selectinload(MemorySession.turns))
        .where(MemorySession.id == session_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_sessions(session: AsyncSession) -> list[MemorySession]:
    """Return all memory sessions ordered by most recent first.

    Args:
        session: Active async database session.

    Returns:
        List of MemorySession records.
    """
    stmt = select(MemorySession).order_by(MemorySession.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_session(
    session: AsyncSession,
    session_id: uuid.UUID,
) -> bool:
    """Delete a memory session and its turns.

    Args:
        session: Active async database session.
        session_id: UUID primary key.

    Returns:
        True if deleted, False if not found.
    """
    ms = await session.get(MemorySession, session_id)
    if ms is None:
        return False
    await session.delete(ms)
    await session.flush()
    logger.info("memory_session_deleted", session_id=str(session_id))
    return True


async def add_turn(
    session: AsyncSession,
    *,
    session_id: uuid.UUID,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> MemoryTurn:
    """Append a turn to a memory session.

    Args:
        session: Active async database session.
        session_id: UUID of the parent memory session.
        role: "user" or "assistant".
        content: Text content of the turn.
        sources: Optional list of source dicts used to generate the answer.

    Returns:
        The created MemoryTurn ORM instance.
    """
    turn = MemoryTurn(
        id=uuid.uuid4(),
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
    )
    session.add(turn)
    await session.flush()
    logger.info("memory_turn_added", session_id=str(session_id), role=role, turn_id=str(turn.id))
    return turn

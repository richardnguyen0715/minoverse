"""Conversation service — CRUD for memory sessions and turns."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.entities.memory_session import MemorySession
from src.memory.entities.memory_turn import MemoryTurn
from src.memory.repositories import session_repository

logger = structlog.get_logger(__name__)


async def create_session(
    session: AsyncSession,
    title: str,
    context: dict | None = None,
) -> MemorySession:
    """Create a new copilot memory session.

    Args:
        session: Active async database session.
        title: Human-readable session title.
        context: Optional metadata dict.

    Returns:
        Created MemorySession.
    """
    return await session_repository.create_session(session, title=title, context=context)


async def add_turn(
    session: AsyncSession,
    session_id: uuid.UUID,
    role: str,
    content: str,
    sources: list[dict] | None = None,
) -> MemoryTurn:
    """Append a user or assistant turn to a session.

    Args:
        session: Active async database session.
        session_id: UUID of the target session.
        role: "user" or "assistant".
        content: Turn text.
        sources: Optional retrieved source dicts.

    Returns:
        Created MemoryTurn.
    """
    return await session_repository.add_turn(
        session,
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
    )


async def get_session_with_turns(
    session: AsyncSession,
    session_id: uuid.UUID,
) -> MemorySession | None:
    """Retrieve a session with its turns eagerly loaded.

    Args:
        session: Active async database session.
        session_id: UUID of the session.

    Returns:
        MemorySession with turns or None.
    """
    return await session_repository.get_session_with_turns(session, session_id)


async def delete_session(
    session: AsyncSession,
    session_id: uuid.UUID,
) -> bool:
    """Delete a memory session and all its turns.

    Args:
        session: Active async database session.
        session_id: UUID of the session to delete.

    Returns:
        True if deleted, False if not found.
    """
    return await session_repository.delete_session(session, session_id)


async def list_sessions(session: AsyncSession) -> list[MemorySession]:
    """List all memory sessions ordered by most recent first.

    Args:
        session: Active async database session.

    Returns:
        List of MemorySession records.
    """
    return await session_repository.list_sessions(session)

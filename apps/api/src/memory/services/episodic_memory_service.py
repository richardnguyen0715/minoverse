"""Episodic memory service — distils conversation sessions into memories."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.ai.skills.synthesize_episode import run_synthesize_episode
from src.memory.entities.episodic_memory import EpisodicMemory
from src.memory.repositories import episodic_repository, session_repository

logger = structlog.get_logger(__name__)


async def distill_session_to_episode(
    session: AsyncSession,
    session_id: uuid.UUID,
    runtime: LLMRuntime,
) -> EpisodicMemory:
    """Read a session's turns and synthesise an episodic memory entry.

    Args:
        session: Active async database session.
        session_id: UUID of the source memory session.
        runtime: LLMRuntime for AI synthesis.

    Returns:
        Created EpisodicMemory.

    Raises:
        ValueError: If session does not exist or has no turns.
    """
    mem_session = await session_repository.get_session_with_turns(session, session_id)
    if mem_session is None:
        raise ValueError(f"Memory session {session_id} not found")

    if not mem_session.turns:
        raise ValueError(f"Memory session {session_id} has no turns to distil")

    conversation = "\n".join(
        f"{turn.role.upper()}: {turn.content}" for turn in mem_session.turns
    )

    result = await run_synthesize_episode(conversation, runtime)

    episode = await episodic_repository.create_episode(
        session,
        title=result["title"] or f"Session {session_id}",
        content=result["content"],
        session_id=session_id,
    )

    logger.info(
        "episode_distilled",
        session_id=str(session_id),
        episode_id=str(episode.id),
        title=episode.title,
    )
    return episode


async def list_episodes(session: AsyncSession) -> list[EpisodicMemory]:
    """List all episodic memories ordered by most recent first.

    Args:
        session: Active async database session.

    Returns:
        List of EpisodicMemory records.
    """
    return await episodic_repository.list_episodes(session)


async def get_episode(
    session: AsyncSession,
    episode_id: uuid.UUID,
) -> EpisodicMemory | None:
    """Fetch a single episodic memory by primary key.

    Args:
        session: Active async database session.
        episode_id: UUID primary key.

    Returns:
        EpisodicMemory or None.
    """
    return await episodic_repository.get_episode(session, episode_id)

"""Copilot service — orchestrates ask flow: retrieve → AI → persist."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.ai.skills.copilot_ask import run_copilot_ask
from src.memory.repositories import session_repository
from src.memory.schemas.memory_schemas import AskResponse
from src.retrieval.services.contextual_retrieval_service import retrieve_context

logger = structlog.get_logger(__name__)


async def ask(
    session: AsyncSession,
    question: str,
    runtime: LLMRuntime,
    db_session_id: uuid.UUID | None = None,
) -> AskResponse:
    """Answer a question using context from the knowledge vault.

    Steps:
    1. Get or create a memory session.
    2. Retrieve relevant context via keyword search.
    3. Format context string.
    4. Call the copilot_ask AI skill.
    5. Save user turn + assistant turn.
    6. Return AskResponse.

    Args:
        session: Active async database session.
        question: The user's question.
        runtime: LLMRuntime for AI inference.
        db_session_id: Optional existing session UUID to continue.

    Returns:
        AskResponse with answer, sources, session_id, and turn_id.
    """
    # 1. Get or create memory session
    if db_session_id is not None:
        mem_session = await session_repository.get_session(session, db_session_id)
        if mem_session is None:
            logger.warning("copilot_ask_session_not_found", session_id=str(db_session_id))
            mem_session = await session_repository.create_session(
                session, title=question[:80]
            )
    else:
        mem_session = await session_repository.create_session(
            session, title=question[:80]
        )

    # 2. Retrieve context
    sources = await retrieve_context(session, question)

    # 3. Format context string
    if sources:
        context_lines = []
        for i, s in enumerate(sources):
            line = f"[{i + 1}] {s['title']}: {s['excerpt']}"
            entities = s.get("entities", [])
            if entities:
                line += f" (concepts: {', '.join(entities[:5])})"
            context_lines.append(line)
        context_str = "\n\n".join(context_lines)
    else:
        context_str = "No relevant documents found in the knowledge vault."

    # 4. Call AI skill
    result = await run_copilot_ask(question, context_str, runtime)
    answer = result.get("answer") or "I could not generate an answer."

    logger.info(
        "copilot_ask_answered",
        session_id=str(mem_session.id),
        confidence=result.get("confidence"),
        sources=len(sources),
    )

    # 5. Save turns
    await session_repository.add_turn(
        session,
        session_id=mem_session.id,
        role="user",
        content=question,
    )
    assistant_turn = await session_repository.add_turn(
        session,
        session_id=mem_session.id,
        role="assistant",
        content=answer,
        sources=sources,
    )

    return AskResponse(
        answer=answer,
        sources=sources,
        session_id=mem_session.id,
        turn_id=assistant_turn.id,
    )

"""FastAPI routes for the memory / copilot domain (Phase 5)."""
from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai import get_llm_runtime
from src.core.database import get_async_session
from src.core.exceptions import LMStudioUnavailableError
from src.memory.schemas.memory_schemas import (
    AskRequest,
    AskResponse,
    EpisodicMemoryOut,
    MemorySessionDetail,
    MemorySessionOut,
    MemoryTurnOut,
    SemanticMemoryOut,
)
from src.memory.services import copilot_service as _copilot_svc
from src.memory.services import conversation_service as _conv_svc
from src.memory.services import episodic_memory_service as _ep_svc
from src.memory.services import semantic_memory_service as _sem_svc

logger = structlog.get_logger(__name__)

memory_router = APIRouter(prefix="/memory", tags=["memory"])
copilot_router = APIRouter(prefix="/copilot", tags=["copilot"])


# ── Copilot endpoints ─────────────────────────────────────────────────────────


@copilot_router.post("/ask", response_model=AskResponse)
async def ask(
    body: AskRequest,
    session: AsyncSession = Depends(get_async_session),
) -> AskResponse:
    """Answer a question using the knowledge-vault context."""
    runtime = get_llm_runtime()
    try:
        response = await _copilot_svc.ask(
            session,
            question=body.question,
            runtime=runtime,
            db_session_id=body.session_id,
        )
    except LMStudioUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable — LM Studio is not reachable. Please ensure LM Studio is running at the configured address. ({exc})",
        ) from exc
    await session.commit()
    return response


@copilot_router.post("/sessions", response_model=MemorySessionOut)
async def create_session(
    body: dict,
    session: AsyncSession = Depends(get_async_session),
) -> MemorySessionOut:
    """Create a new copilot conversation session."""
    title: str = body.get("title", "New Session")
    ms = await _conv_svc.create_session(session, title=title)
    await session.commit()
    return MemorySessionOut.model_validate(ms)


@copilot_router.get("/sessions", response_model=list[MemorySessionOut])
async def list_sessions(
    session: AsyncSession = Depends(get_async_session),
) -> list[MemorySessionOut]:
    """List all copilot conversation sessions."""
    sessions = await _conv_svc.list_sessions(session)
    return [MemorySessionOut.model_validate(s) for s in sessions]


@copilot_router.get("/sessions/{session_id}", response_model=MemorySessionDetail)
async def get_session(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> MemorySessionDetail:
    """Get a conversation session with all its turns."""
    ms = await _conv_svc.get_session_with_turns(session, session_id)
    if ms is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return MemorySessionDetail(
        id=ms.id,
        title=ms.title,
        context=ms.context,
        turns=[MemoryTurnOut.model_validate(t) for t in ms.turns],
        created_at=ms.created_at,
        updated_at=ms.updated_at,
    )


@copilot_router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete a copilot session and all its turns."""
    deleted = await _conv_svc.delete_session(session, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    await session.commit()


@copilot_router.post("/sessions/{session_id}/distill", response_model=EpisodicMemoryOut)
async def distill_session(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> EpisodicMemoryOut:
    """Distil a conversation session into an episodic memory."""
    runtime = get_llm_runtime()
    try:
        episode = await _ep_svc.distill_session_to_episode(session, session_id, runtime)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await session.commit()
    return EpisodicMemoryOut.model_validate(episode)


# ── Memory CRUD endpoints ─────────────────────────────────────────────────────


@memory_router.get("/episodes", response_model=list[EpisodicMemoryOut])
async def list_episodes(
    session: AsyncSession = Depends(get_async_session),
) -> list[EpisodicMemoryOut]:
    """List all episodic memories."""
    episodes = await _ep_svc.list_episodes(session)
    return [EpisodicMemoryOut.model_validate(e) for e in episodes]


@memory_router.get("/episodes/{episode_id}", response_model=EpisodicMemoryOut)
async def get_episode(
    episode_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> EpisodicMemoryOut:
    """Get a single episodic memory by ID."""
    episode = await _ep_svc.get_episode(session, episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")
    return EpisodicMemoryOut.model_validate(episode)


@memory_router.get("/semantic", response_model=list[SemanticMemoryOut])
async def list_semantic(
    session: AsyncSession = Depends(get_async_session),
) -> list[SemanticMemoryOut]:
    """List all semantic memories."""
    memories = await _sem_svc.list_semantic_memories(session)
    return [SemanticMemoryOut.model_validate(m) for m in memories]


@memory_router.get("/semantic/{memory_id}", response_model=SemanticMemoryOut)
async def get_semantic(
    memory_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> SemanticMemoryOut:
    """Get a single semantic memory by ID."""
    memory = await _sem_svc.get_semantic_memory(session, memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail=f"Semantic memory {memory_id} not found")
    return SemanticMemoryOut.model_validate(memory)


@memory_router.post("/extract/{resource_id}", response_model=SemanticMemoryOut | None)
async def extract_semantic(
    resource_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> SemanticMemoryOut | None:
    """Extract a semantic memory from a resource."""
    runtime = get_llm_runtime()
    memory = await _sem_svc.extract_semantic_from_resource(session, resource_id, runtime)
    if memory is None:
        return None
    await session.commit()
    return SemanticMemoryOut.model_validate(memory)

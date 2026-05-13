"""Unit tests for Phase 5 — AI-native Workflows (no DB, no network).

Tests cover:
- Schema validation for all Phase 5 Pydantic models
- AI skill functions (copilot_ask, synthesize_episode, synthesize_semantic)
- contextual_retrieval_service
- conversation_service, episodic_memory_service, semantic_memory_service
- Route 404 behaviour for unknown IDs
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _make_session(session_id: uuid.UUID | None = None, title: str = "Test Session") -> MagicMock:
    s = MagicMock()
    s.id = session_id or uuid.uuid4()
    s.title = title
    s.context = None
    s.created_at = _NOW
    s.updated_at = _NOW
    s.turns = []
    return s


def _make_turn(
    session_id: uuid.UUID,
    role: str = "user",
    content: str = "Hello",
) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.session_id = session_id
    t.role = role
    t.content = content
    t.sources = None
    t.created_at = _NOW
    return t


def _make_episode(session_id: uuid.UUID | None = None) -> MagicMock:
    e = MagicMock()
    e.id = uuid.uuid4()
    e.title = "Research on Transformers"
    e.content = "Key findings: attention is all you need."
    e.resource_ids = None
    e.session_id = session_id
    e.created_at = _NOW
    e.updated_at = _NOW
    return e


def _make_semantic() -> MagicMock:
    m = MagicMock()
    m.id = uuid.uuid4()
    m.concept = "Attention Mechanism"
    m.content = "Self-attention allows models to relate tokens across the sequence."
    m.source_resource_id = uuid.uuid4()
    m.created_at = _NOW
    m.updated_at = _NOW
    return m


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_memory_session_out_validates(self) -> None:
        from src.memory.schemas.memory_schemas import MemorySessionOut

        ms = MemorySessionOut(
            id=uuid.uuid4(),
            title="My Session",
            context=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
        assert ms.title == "My Session"
        assert ms.context is None

    def test_memory_session_out_with_context(self) -> None:
        from src.memory.schemas.memory_schemas import MemorySessionOut

        ms = MemorySessionOut(
            id=uuid.uuid4(),
            title="Session with context",
            context={"topic": "AI"},
            created_at=_NOW,
            updated_at=_NOW,
        )
        assert ms.context == {"topic": "AI"}

    def test_memory_turn_out_validates(self) -> None:
        from src.memory.schemas.memory_schemas import MemoryTurnOut

        sid = uuid.uuid4()
        t = MemoryTurnOut(
            id=uuid.uuid4(),
            session_id=sid,
            role="user",
            content="What is attention?",
            sources=None,
            created_at=_NOW,
        )
        assert t.role == "user"
        assert t.session_id == sid

    def test_episodic_memory_out_validates(self) -> None:
        from src.memory.schemas.memory_schemas import EpisodicMemoryOut

        ep = EpisodicMemoryOut(
            id=uuid.uuid4(),
            title="AI Research Session",
            content="We discussed transformers and BERT.",
            resource_ids=None,
            session_id=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
        assert ep.title == "AI Research Session"
        assert ep.session_id is None

    def test_semantic_memory_out_validates(self) -> None:
        from src.memory.schemas.memory_schemas import SemanticMemoryOut

        sm = SemanticMemoryOut(
            id=uuid.uuid4(),
            concept="Attention Mechanism",
            content="Self-attention lets models relate tokens globally.",
            source_resource_id=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
        assert sm.concept == "Attention Mechanism"
        assert sm.source_resource_id is None

    def test_ask_request_validates(self) -> None:
        from src.memory.schemas.memory_schemas import AskRequest

        req = AskRequest(question="What is BERT?")
        assert req.question == "What is BERT?"
        assert req.session_id is None

    def test_ask_request_with_session_id(self) -> None:
        from src.memory.schemas.memory_schemas import AskRequest

        sid = uuid.uuid4()
        req = AskRequest(question="Tell me more", session_id=sid)
        assert req.session_id == sid

    def test_ask_response_validates(self) -> None:
        from src.memory.schemas.memory_schemas import AskResponse

        resp = AskResponse(
            answer="BERT is a language model.",
            sources=[{"resource_id": "abc", "title": "BERT paper", "excerpt": "...", "score": 1.0}],
            session_id=uuid.uuid4(),
            turn_id=uuid.uuid4(),
        )
        assert resp.answer == "BERT is a language model."
        assert len(resp.sources) == 1


# ---------------------------------------------------------------------------
# copilot_ask skill
# ---------------------------------------------------------------------------

class TestCopilotAskSkill:
    @pytest.mark.asyncio
    async def test_run_copilot_ask_happy_path(self) -> None:
        """Valid JSON from runtime returns parsed dict."""
        from src.ai.skills.copilot_ask import run_copilot_ask

        payload = json.dumps({
            "answer": "BERT is a transformer model.",
            "confidence": "high",
            "cited_resources": ["BERT paper"],
        })
        runtime = AsyncMock()
        runtime.run_skill = AsyncMock(return_value=payload)

        result = await run_copilot_ask("What is BERT?", "Context: ...", runtime)

        assert result["answer"] == "BERT is a transformer model."
        assert result["confidence"] == "high"
        assert "BERT paper" in result["cited_resources"]

    @pytest.mark.asyncio
    async def test_run_copilot_ask_malformed_json(self) -> None:
        """Malformed JSON returns empty fallback gracefully."""
        from src.ai.skills.copilot_ask import run_copilot_ask

        runtime = AsyncMock()
        runtime.run_skill = AsyncMock(return_value="not {{ valid json")

        result = await run_copilot_ask("What is BERT?", "Context", runtime)

        assert result["answer"] == ""
        assert result["confidence"] == "low"
        assert result["cited_resources"] == []

    @pytest.mark.asyncio
    async def test_run_copilot_ask_runtime_exception(self) -> None:
        """Runtime exception returns empty fallback gracefully."""
        from src.ai.skills.copilot_ask import run_copilot_ask

        runtime = AsyncMock()
        runtime.run_skill = AsyncMock(side_effect=RuntimeError("AI unavailable"))

        result = await run_copilot_ask("Question?", "Context", runtime)

        assert result["answer"] == ""


# ---------------------------------------------------------------------------
# synthesize_episode skill
# ---------------------------------------------------------------------------

class TestSynthesizeEpisodeSkill:
    @pytest.mark.asyncio
    async def test_run_synthesize_episode_happy_path(self) -> None:
        """Valid JSON from runtime returns parsed episode dict."""
        from src.ai.skills.synthesize_episode import run_synthesize_episode

        payload = json.dumps({
            "title": "Transformer Research",
            "content": "Session explored attention mechanisms.",
        })
        runtime = AsyncMock()
        runtime.run_skill = AsyncMock(return_value=payload)

        result = await run_synthesize_episode("USER: What is attention?\nASSISTANT: ...", runtime)

        assert result["title"] == "Transformer Research"
        assert "attention" in result["content"]

    @pytest.mark.asyncio
    async def test_run_synthesize_episode_runtime_exception(self) -> None:
        """Runtime exception returns fallback gracefully without raising."""
        from src.ai.skills.synthesize_episode import run_synthesize_episode

        runtime = AsyncMock()
        runtime.run_skill = AsyncMock(side_effect=ConnectionError("timeout"))

        result = await run_synthesize_episode("conversation text", runtime)

        assert result["title"] == "Research Session"
        assert result["content"] == ""


# ---------------------------------------------------------------------------
# synthesize_semantic skill
# ---------------------------------------------------------------------------

class TestSynthesizeSemanticSkill:
    @pytest.mark.asyncio
    async def test_run_synthesize_semantic_happy_path(self) -> None:
        """Valid JSON from runtime returns parsed semantic dict."""
        from src.ai.skills.synthesize_semantic import run_synthesize_semantic

        payload = json.dumps({
            "concept": "Self-Attention",
            "content": "Allows each token to attend to every other token.",
        })
        runtime = AsyncMock()
        runtime.run_skill = AsyncMock(return_value=payload)

        result = await run_synthesize_semantic("Attention is all you need paper...", runtime)

        assert result["concept"] == "Self-Attention"
        assert "token" in result["content"]


# ---------------------------------------------------------------------------
# contextual_retrieval_service
# ---------------------------------------------------------------------------

class TestContextualRetrievalService:
    @pytest.mark.asyncio
    async def test_retrieve_context_returns_results(self) -> None:
        """Mock DB returns rows; service formats them into dicts."""
        from src.retrieval.services.contextual_retrieval_service import retrieve_context

        row = MagicMock()
        row.resource_id = uuid.uuid4()
        row.title = "Attention Paper"
        row.clean_text = "Attention is all you need. " * 20
        row.score = 3

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row]

        db_session = AsyncMock()
        db_session.execute = AsyncMock(return_value=mock_result)

        results = await retrieve_context(db_session, "attention transformer model")

        assert len(results) == 1
        assert results[0]["title"] == "Attention Paper"
        assert results[0]["score"] == 3.0

    @pytest.mark.asyncio
    async def test_retrieve_context_short_words_ignored(self) -> None:
        """Words shorter than 3 characters are skipped; empty query returns []."""
        from src.retrieval.services.contextual_retrieval_service import retrieve_context

        db_session = AsyncMock()

        results = await retrieve_context(db_session, "a b")

        assert results == []
        db_session.execute.assert_not_called()


# ---------------------------------------------------------------------------
# conversation_service
# ---------------------------------------------------------------------------

class TestConversationService:
    @pytest.mark.asyncio
    async def test_create_session_returns_memory_session(self) -> None:
        """create_session calls the repository and returns the ORM object."""
        from src.memory.services.conversation_service import create_session

        expected = _make_session(title="New chat")
        db_session = AsyncMock()

        with patch(
            "src.memory.services.conversation_service.session_repository.create_session",
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_create:
            result = await create_session(db_session, title="New chat")

        mock_create.assert_awaited_once()
        assert result.title == "New chat"


# ---------------------------------------------------------------------------
# episodic_memory_service
# ---------------------------------------------------------------------------

class TestEpisodicMemoryService:
    @pytest.mark.asyncio
    async def test_distill_session_returns_episode(self) -> None:
        """Turns are formatted; AI synthesises episode; episode is persisted."""
        from src.memory.services.episodic_memory_service import distill_session_to_episode

        sid = uuid.uuid4()
        session_obj = _make_session(session_id=sid)
        session_obj.turns = [
            _make_turn(sid, "user", "What is attention?"),
            _make_turn(sid, "assistant", "It is a mechanism..."),
        ]
        episode = _make_episode(session_id=sid)

        db_session = AsyncMock()

        with (
            patch(
                "src.memory.services.episodic_memory_service.session_repository.get_session_with_turns",
                new_callable=AsyncMock,
                return_value=session_obj,
            ),
            patch(
                "src.memory.services.episodic_memory_service.run_synthesize_episode",
                new_callable=AsyncMock,
                return_value={"title": "Research on Transformers", "content": "Key findings..."},
            ),
            patch(
                "src.memory.services.episodic_memory_service.episodic_repository.create_episode",
                new_callable=AsyncMock,
                return_value=episode,
            ),
        ):
            runtime = AsyncMock()
            result = await distill_session_to_episode(db_session, sid, runtime)

        assert result.id == episode.id
        assert result.title == "Research on Transformers"


# ---------------------------------------------------------------------------
# semantic_memory_service
# ---------------------------------------------------------------------------

class TestSemanticMemoryService:
    @pytest.mark.asyncio
    async def test_extract_semantic_returns_memory(self) -> None:
        """Resource content is read; AI extracts concept; memory is saved."""
        from src.memory.services.semantic_memory_service import extract_semantic_from_resource

        resource_id = uuid.uuid4()
        memory = _make_semantic()

        rc_mock = MagicMock()
        rc_mock.clean_text = "Attention allows tokens to relate to each other."

        db_session = AsyncMock()

        # First execute → resource content; second execute → no enrichment
        rc_result = MagicMock()
        rc_result.scalar_one_or_none.return_value = rc_mock
        ae_result = MagicMock()
        ae_result.scalar_one_or_none.return_value = None
        db_session.execute = AsyncMock(side_effect=[rc_result, ae_result])

        with (
            patch(
                "src.memory.services.semantic_memory_service.run_synthesize_semantic",
                new_callable=AsyncMock,
                return_value={"concept": "Attention Mechanism", "content": "Global token attention."},
            ),
            patch(
                "src.memory.services.semantic_memory_service.semantic_repository.create_semantic",
                new_callable=AsyncMock,
                return_value=memory,
            ),
        ):
            runtime = AsyncMock()
            result = await extract_semantic_from_resource(db_session, resource_id, runtime)

        assert result is not None
        assert result.concept == "Attention Mechanism"


# ---------------------------------------------------------------------------
# Route 404 behaviour
# ---------------------------------------------------------------------------

class TestRoutes404:
    @pytest.mark.asyncio
    async def test_get_session_returns_404_for_unknown_id(self) -> None:
        """get_session_with_turns returns None → route raises 404."""
        from fastapi import HTTPException
        from src.memory.routes import get_session

        db_session = AsyncMock()

        with patch(
            "src.memory.routes._conv_svc.get_session_with_turns",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_session(uuid.uuid4(), session=db_session)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_episode_returns_404_for_unknown_id(self) -> None:
        """get_episode returns None → route raises 404."""
        from fastapi import HTTPException
        from src.memory.routes import get_episode

        db_session = AsyncMock()

        with patch(
            "src.memory.routes._ep_svc.get_episode",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_episode(uuid.uuid4(), session=db_session)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_semantic_returns_404_for_unknown_id(self) -> None:
        """get_semantic_memory returns None → route raises 404."""
        from fastapi import HTTPException
        from src.memory.routes import get_semantic

        db_session = AsyncMock()

        with patch(
            "src.memory.routes._sem_svc.get_semantic_memory",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_semantic(uuid.uuid4(), session=db_session)

        assert exc_info.value.status_code == 404

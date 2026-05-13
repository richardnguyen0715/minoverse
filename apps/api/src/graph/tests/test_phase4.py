"""Unit tests for Phase 4 — Knowledge Graph (no DB, no network).

Tests cover:
- entity_promotion_service
- relation_generation_service
- graph_traversal_service
- graph_schemas validation
- canonical_name normalization helper
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.graph.schemas.graph_schemas import (
    ConceptEntityOut,
    EntityType,
    GraphEdge,
    GraphNode,
    GraphOut,
    RelationType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(
    name: str = "Transformer",
    entity_type: str = "technology",
    description: str | None = None,
    entity_id: uuid.UUID | None = None,
) -> MagicMock:
    e = MagicMock()
    e.id = entity_id or uuid.uuid4()
    e.name = name
    e.entity_type = entity_type
    e.canonical_name = name.lower()
    e.description = description
    return e


def _make_relation(
    src_id: uuid.UUID,
    dst_id: uuid.UUID,
    relation_type: str = "related_to",
    weight: float = 1.0,
) -> MagicMock:
    r = MagicMock()
    r.id = uuid.uuid4()
    r.source_entity_id = src_id
    r.target_entity_id = dst_id
    r.relation_type = relation_type
    r.weight = weight
    return r


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_concept_entity_out_validates_entity_type(self) -> None:
        with pytest.raises(ValidationError):
            ConceptEntityOut(
                id=uuid.uuid4(),
                name="X",
                entity_type="invalid_type",  # type: ignore[arg-type]
                canonical_name="x",
            )

    def test_relation_type_enum_values(self) -> None:
        for val in ("related_to", "inspired_by", "references", "extends"):
            rt = RelationType(val)
            assert rt.value == val

    def test_entity_type_enum_values(self) -> None:
        for val in ("concept", "person", "technology", "framework", "organization", "place"):
            et = EntityType(val)
            assert et.value == val

    def test_graph_out_structure(self) -> None:
        node = GraphNode(
            id=uuid.uuid4(),
            name="Attention",
            entity_type=EntityType.concept,
        )
        edge = GraphEdge(
            source=uuid.uuid4(),
            target=uuid.uuid4(),
            relation_type=RelationType.references,
            weight=1.0,
        )
        graph = GraphOut(nodes=[node], edges=[edge])
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1


# ---------------------------------------------------------------------------
# Canonical name normalization
# ---------------------------------------------------------------------------

class TestCanonicalNormalization:
    def test_lowercase_normalization(self) -> None:
        from src.graph.repositories.concept_entity_repository import _canonical

        assert _canonical("Transformer") == "transformer"
        assert _canonical("GPT-4") == "gpt-4"
        assert _canonical("  BERT  ") == "bert"

    def test_mixed_case(self) -> None:
        from src.graph.repositories.concept_entity_repository import _canonical

        assert _canonical("AlexNet") == "alexnet"


# ---------------------------------------------------------------------------
# entity_promotion_service
# ---------------------------------------------------------------------------

class TestEntityPromotionService:
    @pytest.mark.asyncio
    async def test_promote_entities_creates_concept_entities(self) -> None:
        """Entities in enrichment are upserted and linked to resource."""
        resource_id = uuid.uuid4()
        enrichment = MagicMock()
        enrichment.content = {
            "entities": [
                {"name": "Transformer", "type": "technology"},
                {"name": "Vaswani", "type": "person"},
            ]
        }

        session = AsyncMock()

        with (
            patch(
                "src.graph.services.entity_promotion_service.upsert_concept_entity",
                new_callable=AsyncMock,
            ) as mock_upsert,
            patch(
                "src.graph.services.entity_promotion_service.link_resource_entity",
                new_callable=AsyncMock,
            ) as mock_link,
        ):
            mock_upsert.side_effect = [_make_entity("Transformer"), _make_entity("Vaswani", "person")]

            # Patch the DB select so scalar_one_or_none returns our enrichment
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = enrichment
            session.execute = AsyncMock(return_value=mock_result)

            from src.graph.services.entity_promotion_service import promote_entities_from_enrichment

            result = await promote_entities_from_enrichment(session, resource_id)

        assert len(result) == 2
        assert mock_upsert.call_count == 2
        assert mock_link.call_count == 2

    @pytest.mark.asyncio
    async def test_promote_entities_skips_empty_enrichment(self) -> None:
        """Returns [] when no entities enrichment found."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        from src.graph.services.entity_promotion_service import promote_entities_from_enrichment

        result = await promote_entities_from_enrichment(session, uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_promote_entities_deduplicates_by_canonical_name(self) -> None:
        """Duplicate names (different case) produce only one upsert call."""
        resource_id = uuid.uuid4()
        enrichment = MagicMock()
        enrichment.content = {
            "entities": [
                {"name": "Transformer", "type": "technology"},
                {"name": "transformer", "type": "technology"},  # duplicate
            ]
        }

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = enrichment
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch(
                "src.graph.services.entity_promotion_service.upsert_concept_entity",
                new_callable=AsyncMock,
                return_value=_make_entity("Transformer"),
            ) as mock_upsert,
            patch(
                "src.graph.services.entity_promotion_service.link_resource_entity",
                new_callable=AsyncMock,
            ),
        ):
            from src.graph.services.entity_promotion_service import promote_entities_from_enrichment

            result = await promote_entities_from_enrichment(session, resource_id)

        assert mock_upsert.call_count == 1
        assert len(result) == 1


# ---------------------------------------------------------------------------
# relation_generation_service
# ---------------------------------------------------------------------------

class TestRelationGenerationService:
    @pytest.mark.asyncio
    async def test_generate_relations_calls_ollama(self) -> None:
        """Valid Ollama JSON response causes relation upserts."""
        resource_id = uuid.uuid4()
        e1 = _make_entity("Transformer", "technology")
        e2 = _make_entity("Attention", "concept")
        e3 = _make_entity("Vaswani", "person")

        session = AsyncMock()

        ollama_response = '[{"source": "Transformer", "relation_type": "references", "target": "Attention"}]'
        ollama_client = AsyncMock()
        ollama_client.generate = AsyncMock(return_value=ollama_response)

        with (
            patch(
                "src.graph.services.relation_generation_service.get_entities_for_resource",
                new_callable=AsyncMock,
                return_value=[e1, e2, e3],
            ),
            patch(
                "src.graph.services.relation_generation_service.upsert_concept_relation",
                new_callable=AsyncMock,
                return_value=_make_relation(e1.id, e2.id),
            ) as mock_upsert,
        ):
            from src.graph.services.relation_generation_service import generate_relations_for_resource

            result = await generate_relations_for_resource(session, resource_id, ollama_client)

        assert len(result) == 1
        ollama_client.generate.assert_awaited_once()
        mock_upsert.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_relations_handles_invalid_json(self) -> None:
        """Invalid JSON from Ollama → returns [], no exception raised."""
        resource_id = uuid.uuid4()
        session = AsyncMock()
        ollama_client = AsyncMock()
        ollama_client.generate = AsyncMock(return_value="not valid json {{")

        with patch(
            "src.graph.services.relation_generation_service.get_entities_for_resource",
            new_callable=AsyncMock,
            return_value=[_make_entity(), _make_entity("Attention", "concept")],
        ):
            from src.graph.services.relation_generation_service import generate_relations_for_resource

            result = await generate_relations_for_resource(session, resource_id, ollama_client)

        assert result == []

    @pytest.mark.asyncio
    async def test_generate_relations_skips_single_entity(self) -> None:
        """Only 1 entity → Ollama is never called, returns []."""
        session = AsyncMock()
        ollama_client = AsyncMock()

        with patch(
            "src.graph.services.relation_generation_service.get_entities_for_resource",
            new_callable=AsyncMock,
            return_value=[_make_entity()],
        ):
            from src.graph.services.relation_generation_service import generate_relations_for_resource

            result = await generate_relations_for_resource(session, uuid.uuid4(), ollama_client)

        ollama_client.generate.assert_not_called()
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_relations_handles_ollama_unavailable(self) -> None:
        """OllamaUnavailableError → returns [], no exception propagated."""
        from src.core.exceptions import OllamaUnavailableError

        session = AsyncMock()
        ollama_client = AsyncMock()
        ollama_client.generate = AsyncMock(side_effect=OllamaUnavailableError("down"))

        with patch(
            "src.graph.services.relation_generation_service.get_entities_for_resource",
            new_callable=AsyncMock,
            return_value=[_make_entity(), _make_entity("Attention", "concept")],
        ):
            from src.graph.services.relation_generation_service import generate_relations_for_resource

            result = await generate_relations_for_resource(session, uuid.uuid4(), ollama_client)

        assert result == []


# ---------------------------------------------------------------------------
# graph_traversal_service
# ---------------------------------------------------------------------------

class TestGraphTraversalService:
    @pytest.mark.asyncio
    async def test_get_resource_graph_builds_graph_out(self) -> None:
        """Entities and relations from repo are correctly assembled into GraphOut."""
        e1 = _make_entity("Transformer", "technology")
        e2 = _make_entity("Attention", "concept")
        rel = _make_relation(e1.id, e2.id, "references")

        session = AsyncMock()

        with patch(
            "src.graph.services.graph_traversal_service.repo_get_resource_graph",
            new_callable=AsyncMock,
            return_value=([e1, e2], [rel]),
        ):
            from src.graph.services.graph_traversal_service import get_resource_graph

            graph = await get_resource_graph(session, uuid.uuid4())

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.edges[0].relation_type == RelationType.references

    @pytest.mark.asyncio
    async def test_get_resource_graph_empty_returns_empty_graph(self) -> None:
        """No entities → GraphOut with empty nodes and edges."""
        session = AsyncMock()

        with patch(
            "src.graph.services.graph_traversal_service.repo_get_resource_graph",
            new_callable=AsyncMock,
            return_value=([], []),
        ):
            from src.graph.services.graph_traversal_service import get_resource_graph

            graph = await get_resource_graph(session, uuid.uuid4())

        assert graph.nodes == []
        assert graph.edges == []

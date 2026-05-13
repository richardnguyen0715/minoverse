"""Unit tests for the enrichment pipeline orchestrator.

Tests cover:
- Skipping all steps when AI provider is unavailable
- Continuing after one step fails (partial failure recovery)
- Idempotency (same result on repeated calls)

All tests use mocked LLMRuntime and mocked DB session — no real
Postgres or network connections.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from src.enrichment.pipelines.enrichment_pipeline import (
    EnrichmentPipelineResult,
    run_enrichment_for_resource,
)
from src.enrichment.schemas.enrichment_schemas import EnrichmentType


def _make_mock_session() -> AsyncMock:
    """Build a minimal AsyncMock that simulates an AsyncSession."""
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = "Test content for enrichment."
    session.execute.return_value = execute_result
    return session


def _make_mock_runtime(available: bool = True) -> MagicMock:
    """Build a minimal mock LLMRuntime with a mocked provider."""
    runtime = MagicMock()
    runtime._provider = AsyncMock()
    runtime._provider.is_available = AsyncMock(return_value=available)
    runtime._provider.provider_name = "mock"
    return runtime


@pytest.fixture()
def mock_runtime() -> MagicMock:
    """LLMRuntime mock with provider available."""
    return _make_mock_runtime(available=True)


async def test_pipeline_skips_when_provider_unavailable() -> None:
    """Pipeline returns skipped_ollama_unavailable=True when provider is down."""
    runtime = _make_mock_runtime(available=False)
    session = _make_mock_session()
    resource_id = uuid.uuid4()

    with patch(
        "src.enrichment.pipelines.enrichment_pipeline.upsert_enrichment",
        new_callable=AsyncMock,
    ) as mock_upsert:
        result = await run_enrichment_for_resource(
            resource_id, session, runtime=runtime
        )

    assert isinstance(result, EnrichmentPipelineResult)
    assert result.skipped_ollama_unavailable is True
    assert result.succeeded == []
    mock_upsert.assert_not_called()


async def test_pipeline_continues_when_one_step_fails(mock_runtime: MagicMock) -> None:
    """Pipeline records failed step and continues with remaining steps."""
    resource_id = uuid.uuid4()
    session = _make_mock_session()

    with (
        patch(
            "src.enrichment.pipelines.enrichment_pipeline.run_summarize",
            new_callable=AsyncMock,
            side_effect=RuntimeError("summary exploded"),
        ),
        patch(
            "src.enrichment.pipelines.enrichment_pipeline.run_generate_tags",
            new_callable=AsyncMock,
        ) as mock_tags,
        patch(
            "src.enrichment.pipelines.enrichment_pipeline.run_extract_entities",
            new_callable=AsyncMock,
        ) as mock_entities,
        patch(
            "src.enrichment.pipelines.enrichment_pipeline.find_related_resources",
            new_callable=AsyncMock,
        ) as mock_related,
        patch(
            "src.enrichment.pipelines.enrichment_pipeline.upsert_enrichment",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ),
    ):
        from src.enrichment.schemas.enrichment_schemas import (
            EntityResult,
            RelatedResult,
            TaggingResult,
        )

        mock_tags.return_value = TaggingResult(tags=["ai"])
        mock_entities.return_value = EntityResult(
            tools=[], frameworks=[], papers=[], methodologies=[]
        )
        mock_related.return_value = RelatedResult(resource_ids=[])

        result = await run_enrichment_for_resource(
            resource_id, session, runtime=mock_runtime
        )

    assert EnrichmentType.SUMMARY_CONCISE in result.failed
    assert EnrichmentType.SUMMARY_DETAILED in result.failed
    assert EnrichmentType.KEY_INSIGHTS in result.failed
    assert EnrichmentType.AI_TAGS in result.succeeded
    assert result.skipped_ollama_unavailable is False


async def test_pipeline_is_idempotent(mock_runtime: MagicMock) -> None:
    """Calling the pipeline twice with the same resource produces the same result."""
    resource_id = uuid.uuid4()
    upsert_results: list[EnrichmentPipelineResult] = []

    for _ in range(2):
        session = _make_mock_session()
        with (
            patch(
                "src.enrichment.pipelines.enrichment_pipeline.upsert_enrichment",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ),
            patch(
                "src.enrichment.pipelines.enrichment_pipeline.run_summarize",
                new_callable=AsyncMock,
            ) as ms,
            patch(
                "src.enrichment.pipelines.enrichment_pipeline.run_generate_tags",
                new_callable=AsyncMock,
            ) as mt,
            patch(
                "src.enrichment.pipelines.enrichment_pipeline.run_extract_entities",
                new_callable=AsyncMock,
            ) as me,
            patch(
                "src.enrichment.pipelines.enrichment_pipeline.find_related_resources",
                new_callable=AsyncMock,
            ) as mr,
        ):
            from src.enrichment.schemas.enrichment_schemas import (
                EntityResult,
                RelatedResult,
                SummaryResult,
                TaggingResult,
            )

            ms.return_value = SummaryResult(concise="c", detailed="d", key_insights=[])
            mt.return_value = TaggingResult(tags=[])
            me.return_value = EntityResult(
                tools=[], frameworks=[], papers=[], methodologies=[]
            )
            mr.return_value = RelatedResult(resource_ids=[])

            r = await run_enrichment_for_resource(
                resource_id, session, runtime=mock_runtime
            )
            upsert_results.append(r)

    assert upsert_results[0].succeeded == upsert_results[1].succeeded
    assert upsert_results[0].failed == upsert_results[1].failed

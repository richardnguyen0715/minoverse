"""Unit tests for the summary generation service.

Tests cover:
- Successful JSON parsing path
- Graceful degradation on malformed JSON
- Graceful degradation when Ollama is unavailable

All tests mock OllamaClientProtocol — no DB or network access.
"""
from unittest.mock import AsyncMock

import pytest

from src.core.exceptions import OllamaUnavailableError
from src.enrichment.schemas.enrichment_schemas import SummaryResult
from src.enrichment.services.ollama_client import OllamaClientProtocol
from src.enrichment.services.summary_service import generate_summary


@pytest.fixture()
def mock_client() -> AsyncMock:
    """Return an AsyncMock conforming to OllamaClientProtocol."""
    client = AsyncMock(spec=OllamaClientProtocol)
    client.is_available.return_value = True
    return client


async def test_generate_summary_returns_parsed_result(mock_client: AsyncMock) -> None:
    """generate_summary returns correctly parsed SummaryResult on valid JSON."""
    # Arrange
    mock_client.generate.return_value = (
        '{"concise": "Short summary.", '
        '"detailed": "Long detailed summary.", '
        '"key_insights": ["Insight one", "Insight two"]}'
    )

    # Act
    result = await generate_summary("some content", mock_client)

    # Assert
    assert isinstance(result, SummaryResult)
    assert result.concise == "Short summary."
    assert result.detailed == "Long detailed summary."
    assert result.key_insights == ["Insight one", "Insight two"]


async def test_generate_summary_handles_malformed_json(mock_client: AsyncMock) -> None:
    """generate_summary degrades gracefully when the model returns invalid JSON."""
    # Arrange
    mock_client.generate.return_value = "not json at all"

    # Act
    result = await generate_summary("some content", mock_client)

    # Assert — no exception raised, concise is non-empty
    assert isinstance(result, SummaryResult)
    assert result.concise  # degraded to first 200 chars of raw response
    assert result.key_insights == []


async def test_generate_summary_handles_ollama_unavailable(mock_client: AsyncMock) -> None:
    """generate_summary returns empty SummaryResult when Ollama raises."""
    # Arrange
    mock_client.generate.side_effect = OllamaUnavailableError("connection refused")

    # Act — must not raise
    result = await generate_summary("some content", mock_client)

    # Assert
    assert isinstance(result, SummaryResult)
    assert result.concise == ""
    assert result.detailed == ""
    assert result.key_insights == []

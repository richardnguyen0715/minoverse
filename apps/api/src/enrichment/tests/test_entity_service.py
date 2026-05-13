"""Unit tests for the entity extraction service.

Tests cover:
- Successful structured extraction from valid JSON
- Graceful handling of missing keys (default to empty list)
"""
from unittest.mock import AsyncMock

import pytest

from src.enrichment.schemas.enrichment_schemas import EntityResult
from src.enrichment.services.entity_service import extract_entities
from src.enrichment.services.ollama_client import OllamaClientProtocol


@pytest.fixture()
def mock_client() -> AsyncMock:
    """Return an AsyncMock conforming to OllamaClientProtocol."""
    return AsyncMock(spec=OllamaClientProtocol)


async def test_extract_entities_returns_structured_result(mock_client: AsyncMock) -> None:
    """extract_entities populates all fields from valid JSON response."""
    # Arrange
    mock_client.generate.return_value = (
        '{"tools": ["pytest", "mypy"], '
        '"frameworks": ["FastAPI"], '
        '"papers": ["Attention Is All You Need"], '
        '"methodologies": ["TDD"]}'
    )

    # Act
    result = await extract_entities("content", mock_client)

    # Assert
    assert isinstance(result, EntityResult)
    assert result.tools == ["pytest", "mypy"]
    assert result.frameworks == ["FastAPI"]
    assert result.papers == ["Attention Is All You Need"]
    assert result.methodologies == ["TDD"]


async def test_extract_entities_handles_missing_keys(mock_client: AsyncMock) -> None:
    """extract_entities defaults missing entity keys to empty lists."""
    # Arrange — only 'tools' present
    mock_client.generate.return_value = '{"tools": ["pytest"]}'

    # Act — must not raise
    result = await extract_entities("content", mock_client)

    # Assert
    assert result.tools == ["pytest"]
    assert result.frameworks == []
    assert result.papers == []
    assert result.methodologies == []

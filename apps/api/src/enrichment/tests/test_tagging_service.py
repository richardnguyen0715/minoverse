"""Unit tests for the AI tagging service.

Tests cover:
- Tag normalization (lowercase, strip, dedup)
- Respect of max_tags limit
- Graceful handling of empty or missing 'tags' key
"""
from unittest.mock import AsyncMock

import pytest

from src.enrichment.schemas.enrichment_schemas import TaggingResult
from src.enrichment.services.ollama_client import OllamaClientProtocol
from src.enrichment.services.tagging_service import generate_ai_tags


@pytest.fixture()
def mock_client() -> AsyncMock:
    """Return an AsyncMock conforming to OllamaClientProtocol."""
    return AsyncMock(spec=OllamaClientProtocol)


async def test_generate_ai_tags_normalizes_output(mock_client: AsyncMock) -> None:
    """generate_ai_tags lowercases, strips, and deduplicates tags."""
    # Arrange
    mock_client.generate.return_value = (
        '{"tags": ["Python", "  Machine Learning ", "python"]}'
    )

    # Act
    result = await generate_ai_tags("content", mock_client)

    # Assert
    assert isinstance(result, TaggingResult)
    assert result.tags == ["python", "machine learning"]


async def test_generate_ai_tags_respects_max_tags(mock_client: AsyncMock) -> None:
    """generate_ai_tags caps results at max_tags (default 10)."""
    # Arrange
    tags = [f"tag{i}" for i in range(15)]
    mock_client.generate.return_value = f'{{"tags": {tags}}}'

    # Act
    result = await generate_ai_tags("content", mock_client)

    # Assert
    assert len(result.tags) <= 10


async def test_generate_ai_tags_handles_empty_response(mock_client: AsyncMock) -> None:
    """generate_ai_tags returns empty tags when 'tags' key is absent."""
    # Arrange
    mock_client.generate.return_value = "{}"

    # Act
    result = await generate_ai_tags("content", mock_client)

    # Assert
    assert result.tags == []

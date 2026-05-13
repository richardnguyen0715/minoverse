"""Tests for OllamaProvider."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.providers.ollama import OllamaProvider, strip_thinking
from src.core.exceptions import OllamaUnavailableError


@pytest.mark.asyncio
async def test_is_available_returns_true_when_client_responds() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434")
    mock_client = MagicMock()
    mock_client.list = AsyncMock(return_value=MagicMock())
    provider._client = mock_client

    result = await provider.is_available()

    assert result is True
    mock_client.list.assert_called_once()


@pytest.mark.asyncio
async def test_generate_strips_thinking_traces() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434")
    raw_response = MagicMock()
    raw_response.response = "<think>internal reasoning</think>  actual answer"

    mock_client = MagicMock()
    mock_client.generate = AsyncMock(return_value=raw_response)
    provider._client = mock_client

    result = await provider.generate(model="qwen3", prompt="test")

    assert "<think>" not in result
    assert "actual answer" in result


@pytest.mark.asyncio
async def test_generate_raises_on_connection_error() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434")

    # Connection errors are transient — provider retries then raises
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        side_effect=ConnectionError("connection refused")
    )
    provider._client = mock_client

    with pytest.raises(OllamaUnavailableError):
        await provider.generate(model="qwen3", prompt="test")

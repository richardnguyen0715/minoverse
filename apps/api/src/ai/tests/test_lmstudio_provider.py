"""Tests for LMStudioProvider."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch, patch

import httpx
import pytest

from src.ai.providers.lmstudio import LMStudioProvider, _strip_thinking
from src.core.exceptions import LMStudioUnavailableError


# ── strip_thinking ───────────────────────────────────────────────────────────


def test_strip_thinking_removes_traces() -> None:
    raw = "<think>internal reasoning</think>  actual answer"
    assert _strip_thinking(raw) == "actual answer"


def test_strip_thinking_noop_when_no_traces() -> None:
    raw = "just a normal answer"
    assert _strip_thinking(raw) == "just a normal answer"


def test_strip_thinking_handles_multiline() -> None:
    raw = "<think>\nline1\nline2\n</think>\nfinal answer"
    assert _strip_thinking(raw) == "final answer"


# ── is_available ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_is_available_returns_true_when_service_responds() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False
    mock_client.is_closed = False
    provider._client = mock_client

    # Patch is_available to use the mock client instead of creating fresh one
    with patch("httpx.AsyncClient") as MockClient:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_ctx

        result = await provider.is_available()

    assert result is True


@pytest.mark.asyncio
async def test_is_available_returns_false_on_connection_error() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")

    with patch("httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=ConnectionError("refused"))
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_ctx

        result = await provider.is_available()

    assert result is False


# ── generate ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_returns_stripped_content() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "<think>reasoning</think>  the answer"
                }
            }
        ]
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False
    provider._client = mock_client

    result = await provider.generate(model="test-model", prompt="hello")

    assert result == "the answer"
    assert "<think>" not in result
    # Verify correct endpoint called
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "/v1/chat/completions"


@pytest.mark.asyncio
async def test_generate_sends_system_message() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "ok"}}]
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False
    provider._client = mock_client

    await provider.generate(
        model="test-model", prompt="hello", system="be helpful"
    )

    payload = mock_client.post.call_args[1]["json"]
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][0]["content"] == "be helpful"
    assert payload["messages"][1]["role"] == "user"


@pytest.mark.asyncio
async def test_generate_raises_on_client_error() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad request: model not found"

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False
    provider._client = mock_client

    with pytest.raises(LMStudioUnavailableError, match="400"):
        await provider.generate(model="bad-model", prompt="hello")


@pytest.mark.asyncio
async def test_generate_raises_after_retries_on_connection_error() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=httpx.ConnectError("connection refused")
    )
    mock_client.is_closed = False
    provider._client = mock_client

    with pytest.raises(LMStudioUnavailableError, match="4 attempts"):
        await provider.generate(model="test-model", prompt="hello")

    # Should have tried 4 times (1 initial + 3 retries)
    assert mock_client.post.call_count == 4


# ── embeddings ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_embeddings_returns_vector() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"embedding": [0.1, 0.2, 0.3]}]
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False
    provider._client = mock_client

    result = await provider.embeddings(model="embed-model", text="hello")

    assert result == [0.1, 0.2, 0.3]
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "/v1/embeddings"


@pytest.mark.asyncio
async def test_embeddings_raises_on_error() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False
    provider._client = mock_client

    with pytest.raises(LMStudioUnavailableError, match="500"):
        await provider.embeddings(model="embed-model", text="hello")


# ── provider_name ────────────────────────────────────────────────────────────


def test_provider_name() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234")
    assert provider.provider_name == "lmstudio"


# ── constructor ──────────────────────────────────────────────────────────────


def test_constructor_strips_trailing_slash() -> None:
    provider = LMStudioProvider(base_url="http://localhost:1234/")
    assert provider._base_url == "http://localhost:1234"


def test_constructor_sets_auth_header_when_api_key_provided() -> None:
    provider = LMStudioProvider(
        base_url="http://localhost:1234", api_key="sk-test"
    )
    assert provider._headers["Authorization"] == "Bearer sk-test"

"""Tests for LLMRuntime."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.models.registry import ModelSpec
from src.ai.prompts.loader import PromptTemplate
from src.ai.runtimes.llm_runtime import LLMRuntime


def _make_runtime(generate_return: str = '{"result": "ok"}') -> tuple[LLMRuntime, MagicMock]:
    provider = MagicMock()
    provider.generate = AsyncMock(return_value=generate_return)
    provider.provider_name = "mock"

    registry = MagicMock()
    registry.get.return_value = ModelSpec(
        logical_name="chat_model",
        physical_model="qwen3:test",
        provider="mock",
        temperature=0.3,
        max_tokens=1024,
    )

    template = PromptTemplate(
        name="test_prompt",
        version="v1",
        system="You are a tester.",
        user_template="Test content: {content}",
        temperature=0.3,
        max_tokens=512,
    )
    loader = MagicMock()
    loader.load.return_value = template
    loader.render.return_value = "Test content: hello"

    runtime = LLMRuntime(provider=provider, registry=registry, prompt_loader=loader)
    return runtime, provider


@pytest.mark.asyncio
async def test_run_skill_calls_provider_generate() -> None:
    runtime, provider = _make_runtime()

    await runtime.run_skill(
        prompt_name="test_prompt",
        logical_model="chat_model",
        render_kwargs={"content": "hello"},
    )

    provider.generate.assert_called_once_with(
        model="qwen3:test",
        prompt="Test content: hello",
        system="You are a tester.",
        temperature=0.3,
    )


@pytest.mark.asyncio
async def test_run_skill_logs_telemetry() -> None:
    runtime, _ = _make_runtime()

    with patch("src.ai.runtimes.llm_runtime.logger") as mock_logger:
        await runtime.run_skill(
            prompt_name="test_prompt",
            logical_model="chat_model",
            render_kwargs={"content": "hello"},
        )
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args
        assert call_kwargs[0][0] == "ai_call"
        kw = call_kwargs[1]
        assert kw["prompt"] == "test_prompt"
        assert kw["prompt_version"] == "v1"
        assert kw["model"] == "qwen3:test"
        assert kw["provider"] == "mock"
        assert "latency_ms" in kw
        assert kw["success"] is True


@pytest.mark.asyncio
async def test_run_skill_returns_raw_response() -> None:
    expected = '{"result": "hello world"}'
    runtime, _ = _make_runtime(generate_return=expected)

    result = await runtime.run_skill(
        prompt_name="test_prompt",
        logical_model="chat_model",
        render_kwargs={"content": "hello"},
    )

    assert result == expected

"""Ollama client protocol and async implementation.

Provides a typed Protocol for dependency injection and an async concrete
implementation backed by the ``ollama`` Python package. All callers
should depend on OllamaClientProtocol, not the concrete class, to keep
services testable.
"""
import re
from typing import Protocol

import structlog

import ollama as ollama_lib

from src.core.config import settings
from src.core.exceptions import OllamaUnavailableError

logger = structlog.get_logger(__name__)

_THINKING_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_thinking(text: str) -> str:
    """Remove <think>…</think> reasoning traces produced by thinking models.

    Qwen3 and similar models may prefix their response with a reasoning
    block wrapped in ``<think>`` tags before emitting the actual JSON.
    This helper strips those blocks so that downstream JSON parsing works
    correctly.

    Args:
        text: Raw model response text, possibly containing thinking traces.

    Returns:
        The text with all ``<think>…</think>`` blocks removed and stripped.
    """
    return _THINKING_RE.sub("", text).strip()


class OllamaClientProtocol(Protocol):
    """Structural protocol for Ollama interaction.

    Any object implementing these two methods may be used wherever an
    OllamaClient is expected, enabling easy mocking in tests.
    """

    async def generate(self, model: str, prompt: str, system: str = "") -> str:
        """Send a generation request and return the text response.

        Args:
            model: The Ollama model identifier (e.g. ``"qwen3"``).
            prompt: The user prompt to send.
            system: Optional system-level instruction.

        Returns:
            The model's text response.

        Raises:
            OllamaUnavailableError: If Ollama is unreachable.
        """
        ...

    async def is_available(self) -> bool:
        """Check whether the Ollama service is reachable.

        Returns:
            True if the service responds; False otherwise.
        """
        ...


class AsyncOllamaClient:
    """Async Ollama client backed by the ``ollama`` Python package.

    Args:
        base_url: Base URL of the Ollama service (e.g. ``"http://localhost:11434"``).
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._client = ollama_lib.AsyncClient(host=base_url)

    async def generate(self, model: str, prompt: str, system: str = "") -> str:
        """Send a generation request and return the text response.

        Args:
            model: The Ollama model identifier.
            prompt: The user prompt.
            system: Optional system-level instruction.

        Returns:
            The model's text response string.

        Raises:
            OllamaUnavailableError: On any connection or communication error.
        """
        try:
            response = await self._client.generate(
                model=model,
                prompt=prompt,
                system=system,
                stream=False,
            )
            return strip_thinking(response.response)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("ollama_generate_failed", error=str(exc), model=model)
            raise OllamaUnavailableError(
                f"Ollama generate failed: {exc}",
                context={"model": model, "base_url": self._base_url},
            ) from exc

    async def is_available(self) -> bool:
        """Check whether the Ollama service is reachable.

        Returns:
            True if ``/api/tags`` responds successfully; False otherwise.
        """
        try:
            await self._client.list()
            return True
        except Exception:
            return False


def get_ollama_client() -> AsyncOllamaClient:
    """Factory that creates an AsyncOllamaClient from application settings.

    Returns:
        AsyncOllamaClient: Ready-to-use async Ollama client.
    """
    return AsyncOllamaClient(base_url=settings.ollama_base_url)

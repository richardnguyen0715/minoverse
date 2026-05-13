"""Ollama provider implementation of LLMProvider.

Uses the official ``ollama`` Python SDK with tenacity-based retry logic for
transient failures (connection errors, timeouts). Authentication errors and
model-not-found errors are NOT retried.
"""
import re
from typing import Any

import ollama as ollama_lib
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.exceptions import OllamaUnavailableError

logger = structlog.get_logger(__name__)

_THINKING_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

_RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def strip_thinking(text: str) -> str:
    """Remove ``<think>…</think>`` reasoning traces from model output.

    Args:
        text: Raw model response, possibly containing thinking traces.

    Returns:
        Text with all ``<think>…</think>`` blocks removed and stripped.
    """
    return _THINKING_RE.sub("", text).strip()


def _is_transient(exc: BaseException) -> bool:
    """Return True for transient errors that warrant a retry."""
    if isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    # ollama SDK wraps httpx errors — check message for connection issues
    msg = str(exc).lower()
    return any(
        kw in msg
        for kw in ("connection", "timeout", "connect error", "network")
    )


class OllamaProvider:
    """Concrete LLMProvider backed by a local Ollama service.

    Implements both ``LLMProvider`` (new AI layer) and ``OllamaClientProtocol``
    (legacy enrichment services) so it can be used as a drop-in replacement.

    Args:
        base_url: Base URL of the Ollama service.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._client = ollama_lib.AsyncClient(host=base_url)

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate text with automatic retry on transient failures.

        Args:
            model: Physical model identifier.
            prompt: User prompt.
            system: Optional system instruction.
            temperature: Sampling temperature.

        Returns:
            Generated text with thinking traces stripped.

        Raises:
            OllamaUnavailableError: After all retry attempts are exhausted.
        """
        return await self._generate_with_retry(model, prompt, system, temperature)

    async def _generate_with_retry(
        self, model: str, prompt: str, system: str, temperature: float
    ) -> str:
        attempt = 0
        last_exc: Exception | None = None
        delays = [1.0, 2.0, 4.0]

        for delay in [None, *delays]:
            if delay is not None:
                import asyncio
                await asyncio.sleep(delay)
            try:
                response = await self._client.generate(
                    model=model,
                    prompt=prompt,
                    system=system,
                    stream=False,
                    options={"temperature": temperature},
                )
                return strip_thinking(response.response)  # type: ignore[union-attr]
            except Exception as exc:
                if not _is_transient(exc):
                    logger.warning(
                        "ollama_generate_non_retryable",
                        model=model,
                        error=str(exc),
                    )
                    raise OllamaUnavailableError(
                        f"Ollama generate failed (non-retryable): {exc}",
                        context={"model": model, "base_url": self._base_url},
                    ) from exc
                attempt += 1
                last_exc = exc
                logger.warning(
                    "ollama_generate_retrying",
                    model=model,
                    attempt=attempt,
                    error=str(exc),
                )

        raise OllamaUnavailableError(
            f"Ollama generate failed after {len(delays) + 1} attempts: {last_exc}",
            context={"model": model, "base_url": self._base_url},
        ) from last_exc

    async def embeddings(self, model: str, text: str) -> list[float]:
        """Compute text embeddings.

        Args:
            model: Physical embedding model identifier.
            text: Input text to embed.

        Returns:
            Float embedding vector.

        Raises:
            OllamaUnavailableError: On connection or communication error.
        """
        try:
            response = await self._client.embeddings(model=model, prompt=text)
            return list(response.embedding)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("ollama_embeddings_failed", model=model, error=str(exc))
            raise OllamaUnavailableError(
                f"Ollama embeddings failed: {exc}",
                context={"model": model, "base_url": self._base_url},
            ) from exc

    async def is_available(self) -> bool:
        """Check whether the Ollama service is reachable."""
        try:
            await self._client.list()
            return True
        except Exception:
            return False

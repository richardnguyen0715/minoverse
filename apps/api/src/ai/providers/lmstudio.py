"""LM Studio provider implementation of LLMProvider.

Uses LM Studio's OpenAI-compatible endpoints:
- ``/v1/chat/completions`` for text generation
- ``/v1/embeddings`` for embedding computation
- ``/v1/models`` for availability checks

LM Studio runs locally (default port 1234) and serves any GGUF model.
The provider uses ``httpx`` directly rather than the ``openai`` SDK to
keep dependencies minimal and match the existing httpx-based patterns.

Retry policy:
- Connection / timeout errors → exponential backoff 1 s → 2 s → 4 s
- 5xx server errors → exponential backoff
- 4xx errors → fail fast, no retry
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
import structlog

from src.core.exceptions import LMStudioUnavailableError

logger = structlog.get_logger(__name__)

_THINKING_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

_BACKOFF_DELAYS = [1.0]  # one retry; fail fast on connection errors


def _strip_thinking(text: str) -> str:
    """Remove ``<think>…</think>`` reasoning traces if present."""
    return _THINKING_RE.sub("", text).strip()


def _is_transient(exc: BaseException) -> bool:
    """Return True for transient errors that warrant a retry."""
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    if isinstance(exc, httpx.ConnectError | httpx.TimeoutException):
        return True
    msg = str(exc).lower()
    return any(
        kw in msg
        for kw in ("connection", "timeout", "connect error", "network")
    )


def _is_server_error(status: int) -> bool:
    """Return True for HTTP 5xx status codes."""
    return 500 <= status < 600


class LMStudioProvider:
    """LLMProvider backed by a local LM Studio service.

    Uses the OpenAI-compatible API endpoints which LM Studio exposes
    at ``/v1/chat/completions`` and ``/v1/embeddings``.

    Args:
        base_url: Base URL of the LM Studio service (e.g. ``http://localhost:1234``).
        api_key: Optional API key for authenticated LM Studio instances.
        chat_model: Default chat model identifier.
        embedding_model: Default embedding model identifier.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        chat_model: str = "",
        embedding_model: str = "",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._chat_model = chat_model
        self._embedding_model = embedding_model

        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

        # Lazily created per event loop to avoid cross-loop issues.
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return an httpx client bound to the current event loop.

        Creates a new client if none exists or if the previous one was
        created in a different event loop (common with Dramatiq workers).
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self._headers,
                timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0),
            )
        return self._client

    @property
    def provider_name(self) -> str:
        return "lmstudio"

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate text using LM Studio's OpenAI-compatible chat completions.

        Args:
            model: Physical model identifier loaded in LM Studio.
            prompt: User prompt text.
            system: Optional system instruction.
            temperature: Sampling temperature.

        Returns:
            Generated text with thinking traces stripped.

        Raises:
            LMStudioUnavailableError: After all retry attempts are exhausted.
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        last_exc: Exception | None = None

        for attempt, delay in enumerate(
            [None, *_BACKOFF_DELAYS], start=1
        ):
            if delay is not None:
                await asyncio.sleep(delay)

            try:
                response = await self._get_client().post(
                    "/v1/chat/completions",
                    json=payload,
                )

                if _is_server_error(response.status_code):
                    raise httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                if response.status_code >= 400:
                    body = response.text
                    logger.warning(
                        "lmstudio_generate_client_error",
                        model=model,
                        status=response.status_code,
                        body=body[:500],
                    )
                    raise LMStudioUnavailableError(
                        f"LM Studio generate failed ({response.status_code}): {body[:300]}",
                        context={"model": model, "base_url": self._base_url},
                    )

                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return _strip_thinking(text)

            except LMStudioUnavailableError:
                raise  # non-retryable client errors

            except Exception as exc:
                last_exc = exc
                if not _is_transient(exc) and not (
                    isinstance(exc, httpx.HTTPStatusError)
                    and _is_server_error(exc.response.status_code)
                ):
                    logger.warning(
                        "lmstudio_generate_non_retryable",
                        model=model,
                        error=str(exc),
                    )
                    raise LMStudioUnavailableError(
                        f"LM Studio generate failed (non-retryable): {exc}",
                        context={"model": model, "base_url": self._base_url},
                    ) from exc

                logger.warning(
                    "lmstudio_generate_retrying",
                    model=model,
                    attempt=attempt,
                    error=str(exc),
                )

        raise LMStudioUnavailableError(
            f"LM Studio generate failed after {len(_BACKOFF_DELAYS) + 1} attempts: {last_exc}",
            context={"model": model, "base_url": self._base_url},
        ) from last_exc

    async def embeddings(self, model: str, text: str) -> list[float]:
        """Compute text embeddings using LM Studio's OpenAI-compatible endpoint.

        Args:
            model: Physical embedding model identifier.
            text: Input text to embed.

        Returns:
            Float embedding vector.

        Raises:
            LMStudioUnavailableError: On connection or API errors.
        """
        payload = {
            "model": model,
            "input": text,
        }

        try:
            response = await self._get_client().post(
                "/v1/embeddings",
                json=payload,
            )

            if response.status_code >= 400:
                body = response.text
                raise LMStudioUnavailableError(
                    f"LM Studio embeddings failed ({response.status_code}): {body[:300]}",
                    context={"model": model, "base_url": self._base_url},
                )

            data = response.json()
            return list(data["data"][0]["embedding"])

        except LMStudioUnavailableError:
            raise
        except Exception as exc:
            logger.warning(
                "lmstudio_embeddings_failed",
                model=model,
                error=str(exc),
            )
            raise LMStudioUnavailableError(
                f"LM Studio embeddings failed: {exc}",
                context={"model": model, "base_url": self._base_url},
            ) from exc

    async def is_available(self) -> bool:
        """Check whether the LM Studio service is reachable.

        Uses a fresh httpx client to avoid event loop portability issues
        (e.g., when called from Dramatiq workers via asyncio.run()).
        """
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=5.0
            ) as client:
                response = await client.get("/v1/models")
                return response.status_code == 200
        except Exception:
            return False

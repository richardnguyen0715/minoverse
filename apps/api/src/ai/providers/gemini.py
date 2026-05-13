"""Google Gemini provider implementation of LLMProvider.

Supports two authentication modes:
- **API key rotation**: round-robin across up to N API keys. On auth errors
  (HTTP 403) the provider rotates to the next key. On quota errors (HTTP 429)
  it sleeps for the retry delay specified in the error response, then retries.
- **Service account (optional)**: when ``service_account_path`` is supplied it
  takes precedence over API keys. Uses Vertex AI endpoint; requires
  ``gemini_project_id`` and ``gemini_location`` config values.

Retry policy:
- 429 (quota/rate limit) → sleep retry_delay from error (default 30 s), retry same key
- 403 (auth/forbidden)  → rotate to next API key, retry immediately
- 5xx (server error)    → exponential backoff 1 s → 2 s → 4 s on same/rotated client
- 4xx non-429/403 (bad request, model not found) → fail fast, no retry
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

import structlog
from google import genai
from google.genai import types as genai_types

logger = structlog.get_logger(__name__)

_THINKING_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_RETRY_DELAY_RE = re.compile(r"retry[^\d]+(\d+)s", re.IGNORECASE)

# Max number of times to wait + retry on quota errors (prevents infinite loops)
_MAX_QUOTA_RETRIES = 3
_DEFAULT_QUOTA_SLEEP = 30.0  # seconds to sleep when retry delay not in error msg

# HTTP status codes considered transient (eligible for backoff retry)
_TRANSIENT_STATUS_CODES = {500, 502, 503, 504}

# Retry delays for transient server errors
_BACKOFF_DELAYS = [1.0, 2.0, 4.0]


def _strip_thinking(text: str) -> str:
    """Remove ``<think>…</think>`` reasoning traces if present."""
    return _THINKING_RE.sub("", text).strip()


def _status_code(exc: BaseException) -> int | None:
    """Extract HTTP status code from a google-genai ClientError/ServerError."""
    # google.genai.errors.APIError has a .code attribute (int)
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code
    # Fallback: check status attribute
    status = getattr(exc, "status", None)
    if isinstance(status, int):
        return status
    return None


def _is_quota_error(exc: BaseException) -> bool:
    code = _status_code(exc)
    return code == 429


def _is_auth_error(exc: BaseException) -> bool:
    code = _status_code(exc)
    return code == 403


def _extract_retry_delay(exc: BaseException) -> float:
    """Parse the retry delay (seconds) from a Gemini 429 error message."""
    msg = str(exc)
    m = _RETRY_DELAY_RE.search(msg)
    if m:
        return float(m.group(1))
    return _DEFAULT_QUOTA_SLEEP
    code = _status_code(exc)
    if code in _TRANSIENT_STATUS_CODES:
        return True
    # Network-level errors
    msg = str(exc).lower()
    return any(kw in msg for kw in ("connection", "timeout", "network", "connect error"))


class GeminiProvider:
    """Google Gemini LLMProvider with API key rotation and optional service account auth.

    When ``service_account_path`` is provided it is used exclusively (no API key
    rotation). Otherwise, each call round-robins across the supplied API keys,
    rotating to the next key automatically on 429 / quota errors.

    Args:
        api_keys: List of Gemini API keys (at least one required unless
            ``service_account_path`` is set).
        service_account_path: Optional path to a Google service-account JSON
            file. When set, Vertex AI is used instead of the Gemini Developer API.
        project_id: Google Cloud project ID (required with ``service_account_path``).
        location: Vertex AI region (default: ``"us-central1"``).
        chat_model: Physical Gemini chat model ID.
        embedding_model: Physical Gemini embedding model ID.
    """

    def __init__(
        self,
        api_keys: list[str],
        service_account_path: str | None = None,
        project_id: str | None = None,
        location: str = "us-central1",
        chat_model: str = "gemini-2.0-flash",
        embedding_model: str = "text-embedding-004",
    ) -> None:
        self._api_keys = [k.strip() for k in api_keys if k.strip()]
        self._service_account_path = service_account_path
        self._project_id = project_id
        self._location = location
        self._chat_model = chat_model
        self._embedding_model = embedding_model

        # Build client pool
        self._clients: list[genai.Client] = []
        self._sa_client: genai.Client | None = None
        self._key_index = 0  # current position in rotation
        self._setup()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup(self) -> None:
        if self._service_account_path:
            self._sa_client = self._build_sa_client()
            logger.info(
                "gemini_provider_init",
                auth="service_account",
                path=self._service_account_path,
                project=self._project_id,
                location=self._location,
            )
        elif self._api_keys:
            self._clients = [genai.Client(api_key=k) for k in self._api_keys]
            logger.info(
                "gemini_provider_init",
                auth="api_keys",
                key_count=len(self._clients),
            )
        else:
            raise ValueError(
                "GeminiProvider requires either api_keys or service_account_path."
            )

    def _build_sa_client(self) -> genai.Client:
        from google.auth import credentials as google_creds
        from google.oauth2 import service_account

        creds: google_creds.Credentials = (
            service_account.Credentials.from_service_account_file(
                self._service_account_path,  # type: ignore[arg-type]
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        )
        return genai.Client(
            credentials=creds,
            vertexai=True,
            project=self._project_id,
            location=self._location,
        )

    # ------------------------------------------------------------------
    # Key rotation
    # ------------------------------------------------------------------

    def _current_client(self) -> genai.Client:
        if self._sa_client:
            return self._sa_client
        return self._clients[self._key_index % len(self._clients)]

    def _rotate_key(self) -> None:
        """Advance to the next API key."""
        if self._sa_client:
            return  # no rotation for service-account auth
        self._key_index += 1
        logger.info(
            "gemini_key_rotated",
            new_key_index=self._key_index % len(self._clients),
            total_keys=len(self._clients),
        )

    # ------------------------------------------------------------------
    # LLMProvider protocol
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate text with quota-aware backoff and auth-error key rotation.

        On 429 quota errors, sleeps for the retry delay from the error response
        (all keys share the same project quota, so rotation doesn't help).
        On 403 auth errors, rotates to the next API key.
        On 5xx server errors, waits with exponential backoff.
        On other 4xx errors, raises immediately.

        Args:
            model: Physical Gemini model ID (e.g. ``"gemini-2.0-flash"``).
            prompt: User prompt text.
            system: Optional system instruction.
            temperature: Sampling temperature.

        Returns:
            Generated text with thinking traces stripped.

        Raises:
            RuntimeError: When all retry attempts fail.
        """
        max_auth_rotations = len(self._clients) if not self._sa_client else 1
        auth_rotations = 0
        quota_retries = 0
        backoff_idx = 0
        last_exc: BaseException | None = None

        while True:
            client = self._current_client()

            try:
                config = genai_types.GenerateContentConfig(
                    system_instruction=system or None,
                    temperature=temperature,
                    max_output_tokens=2048,
                )
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                text = response.text or ""
                return _strip_thinking(text)

            except Exception as exc:
                last_exc = exc

                if _is_quota_error(exc):
                    # All keys share the same project quota — sleep, not rotate
                    if quota_retries >= _MAX_QUOTA_RETRIES:
                        raise RuntimeError(
                            f"Gemini quota exhausted after {quota_retries} retries: {exc}"
                        ) from exc
                    delay = _extract_retry_delay(exc)
                    logger.warning(
                        "gemini_quota_error",
                        model=model,
                        key_index=self._key_index % max(len(self._clients), 1),
                        retry_in=delay,
                        attempt=quota_retries + 1,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    quota_retries += 1

                elif _is_auth_error(exc):
                    # 403 = bad key → rotate to next key
                    if auth_rotations >= max_auth_rotations:
                        raise RuntimeError(
                            f"Gemini auth failed on all {max_auth_rotations} key(s): {exc}"
                        ) from exc
                    logger.warning(
                        "gemini_auth_error_rotating",
                        model=model,
                        key_index=self._key_index % max(len(self._clients), 1),
                        error=str(exc),
                    )
                    self._rotate_key()
                    auth_rotations += 1

                elif _is_transient_error(exc):
                    if backoff_idx >= len(_BACKOFF_DELAYS):
                        raise RuntimeError(
                            f"Gemini server error after backoff: {exc}"
                        ) from exc
                    delay = _BACKOFF_DELAYS[backoff_idx]
                    logger.warning(
                        "gemini_transient_error",
                        model=model,
                        attempt=backoff_idx + 1,
                        retry_in=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    backoff_idx += 1

                else:
                    logger.error(
                        "gemini_generate_failed",
                        model=model,
                        error=str(exc),
                    )
                    raise RuntimeError(
                        f"Gemini generate failed (non-retryable): {exc}"
                    ) from exc

    async def embeddings(self, model: str, text: str) -> list[float]:
        """Compute text embeddings using the Gemini Embedding API.

        Args:
            model: Physical embedding model ID (e.g. ``"text-embedding-004"``).
            text: Input text to embed.

        Returns:
            Float embedding vector.

        Raises:
            RuntimeError: On API errors after retries.
        """
        client = self._current_client()
        try:
            response = await client.aio.models.embed_content(
                model=model,
                contents=text,
            )
            if response.embeddings:
                return list(response.embeddings[0].values)
            raise RuntimeError("Gemini embeddings response contained no vectors.")
        except Exception as exc:
            logger.warning("gemini_embeddings_failed", model=model, error=str(exc))
            if _is_quota_error(exc):
                self._rotate_key()
            raise RuntimeError(f"Gemini embeddings failed: {exc}") from exc

    async def is_available(self) -> bool:
        """Check whether the Gemini service is reachable by listing models."""
        try:
            client = self._current_client()
            # Lightweight availability probe
            models = client.models.list()
            return True
        except Exception as exc:
            logger.debug("gemini_unavailable", error=str(exc))
            return False

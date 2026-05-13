"""Domain exception hierarchy for minoverse.

All domain exceptions inherit from MinoverseError to enable
structured error handling at API boundaries.
"""


class MinoverseError(Exception):
    """Base exception for all minoverse domain errors."""

    def __init__(self, message: str, *, context: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class ResourceNotFoundError(MinoverseError):
    """Raised when a requested resource does not exist."""


class VaultFileNotFoundError(MinoverseError):
    """Raised when a vault file cannot be located on the filesystem."""


class EmbeddingModelUnavailableError(MinoverseError):
    """Raised when the embedding model runtime is unreachable."""


class EmbeddingTimeoutError(MinoverseError):
    """Raised when embedding generation exceeds the timeout threshold."""


class IngestionError(MinoverseError):
    """Raised when an ingestion pipeline step fails."""


class ChunkingError(MinoverseError):
    """Raised when content chunking fails."""


class EventPublishError(MinoverseError):
    """Raised when an event cannot be published to the event bus."""


class MarkdownParseError(MinoverseError):
    """Raised when a markdown file cannot be parsed."""


class OllamaUnavailableError(MinoverseError):
    """Raised when the Ollama service is unreachable or times out."""


class LMStudioUnavailableError(MinoverseError):
    """Raised when the LM Studio service is unreachable or times out."""


class EnrichmentError(MinoverseError):
    """Raised when an AI enrichment step fails non-transiently."""

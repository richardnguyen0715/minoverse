"""LLM provider protocol — the only interface the application knows about."""
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Provider-agnostic interface for language model operations.

    Any provider implementation (Ollama, OpenAI, Anthropic, …) must satisfy
    this structural protocol. Business logic must NEVER import a concrete
    provider directly — depend on LLMProvider only.
    """

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Generate a text response.

        Args:
            model: Physical model identifier (e.g. ``"qwen3:0.6b"``).
            prompt: User prompt text.
            system: Optional system-level instruction.
            temperature: Sampling temperature.

        Returns:
            Generated text with thinking traces stripped.
        """
        ...

    async def embeddings(self, model: str, text: str) -> list[float]:
        """Compute text embeddings.

        Args:
            model: Physical embedding model identifier.
            text: Input text to embed.

        Returns:
            Float vector of embeddings.
        """
        ...

    async def is_available(self) -> bool:
        """Check whether the provider service is reachable.

        Returns:
            True if the service responds; False otherwise.
        """
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g. ``"ollama"``).

        Returns:
            Provider name string.
        """
        ...

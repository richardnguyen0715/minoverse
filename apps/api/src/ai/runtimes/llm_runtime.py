"""LLM Runtime — the central execution layer for all AI skill calls.

Coordinates provider, model registry, prompt loader, and telemetry in one
place. Business logic interacts only with this class — never with providers
or models directly.
"""
from __future__ import annotations

import time

import structlog

from src.ai.models.registry import ModelRegistry
from src.ai.prompts.loader import PromptLoader
from src.ai.providers.base import LLMProvider

logger = structlog.get_logger(__name__)


class LLMRuntime:
    """Unified runtime for LLM skill execution.

    Args:
        provider: An LLMProvider implementation.
        registry: ModelRegistry that maps logical to physical model names.
        prompt_loader: PromptLoader for YAML-based prompt files.
    """

    def __init__(
        self,
        provider: LLMProvider,
        registry: ModelRegistry,
        prompt_loader: PromptLoader,
    ) -> None:
        self._provider = provider
        self._registry = registry
        self._prompt_loader = prompt_loader

    async def run_skill(
        self,
        *,
        prompt_name: str,
        logical_model: str,
        render_kwargs: dict[str, object],
    ) -> str:
        """Load a prompt, render it, call the provider, and log telemetry.

        Args:
            prompt_name: Name of the YAML prompt file (without extension).
            logical_model: Logical model alias (e.g. ``"chat_model"``).
            render_kwargs: Template variables for ``{placeholder}`` substitution.

        Returns:
            Raw generated text response.
        """
        template = self._prompt_loader.load(prompt_name)
        spec = self._registry.get(logical_model)
        user_prompt = self._prompt_loader.render(template, **render_kwargs)

        start = time.monotonic()
        success = False
        try:
            response = await self._provider.generate(
                model=spec.physical_model,
                prompt=user_prompt,
                system=template.system,
                temperature=template.temperature,
            )
            success = True
            return response
        finally:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "ai_call",
                prompt=prompt_name,
                prompt_version=template.version,
                model=spec.physical_model,
                provider=self._provider.provider_name,
                latency_ms=latency_ms,
                success=success,
            )

    async def embeddings(
        self,
        text: str,
        logical_model: str = "embedding_model",
    ) -> list[float]:
        """Compute embeddings using the specified logical model.

        Args:
            text: Input text to embed.
            logical_model: Logical model alias (default: ``"embedding_model"``).

        Returns:
            Float embedding vector.
        """
        spec = self._registry.get(logical_model)
        return await self._provider.embeddings(model=spec.physical_model, text=text)

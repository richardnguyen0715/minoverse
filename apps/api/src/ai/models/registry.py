"""Model registry — maps logical model names to physical models and providers.

Loads from ``src/ai/configs/models.yaml`` and resolves placeholder values
(``${CHAT_MODEL}``, ``${GEMINI_CHAT_MODEL}``, ``${LMSTUDIO_CHAT_MODEL}``,
etc.) from application settings.

The active provider section (``ollama``, ``gemini``, or ``lmstudio``) is
selected via the ``AI_PROVIDER`` environment variable so skills always use
the same logical names (``"chat_model"``, ``"embedding_model"``) regardless
of provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_CONFIGS_DIR = Path(__file__).parent.parent / "configs"


@dataclass
class ModelSpec:
    """Specification for a single logical model.

    Attributes:
        logical_name: Logical alias used in business logic (e.g. ``"chat_model"``).
        physical_model: Actual model identifier sent to the provider.
        provider: Provider name (e.g. ``"gemini"`` or ``"ollama"``).
        temperature: Default sampling temperature.
        max_tokens: Default max output tokens.
    """

    logical_name: str
    physical_model: str
    provider: str
    temperature: float = 0.7
    max_tokens: int = 2048


class ModelRegistry:
    """Registry that maps logical model names to ``ModelSpec`` instances.

    Loads YAML on construction. The active provider section is selected from
    ``settings.ai_provider`` (``"gemini"`` or ``"ollama"``), so all skills
    use the same logical names regardless of which provider is active.
    """

    def __init__(self) -> None:
        self._specs: dict[str, ModelSpec] = {}
        self._load()

    def _load(self) -> None:
        from src.core.config import settings

        provider_name = settings.ai_provider.lower()

        _PLACEHOLDER_MAP = {
            "${CHAT_MODEL}": settings.chat_model,
            "${EMBEDDING_MODEL}": settings.embedding_model,
            "${GEMINI_CHAT_MODEL}": settings.gemini_chat_model,
            "${GEMINI_EMBEDDING_MODEL}": settings.gemini_embedding_model,
            "${LMSTUDIO_CHAT_MODEL}": settings.lmstudio_chat_model,
            "${LMSTUDIO_EMBEDDING_MODEL}": settings.lmstudio_embedding_model,
        }

        config_path = _CONFIGS_DIR / "models.yaml"
        raw = yaml.safe_load(config_path.read_text())

        provider_section = raw.get("providers", {}).get(provider_name, {})
        if not provider_section:
            raise KeyError(
                f"No model config found for provider '{provider_name}' in models.yaml. "
                f"Available providers: {list(raw.get('providers', {}).keys())}"
            )

        for logical_name, spec in provider_section.items():
            physical = spec["physical_model"]
            for placeholder, value in _PLACEHOLDER_MAP.items():
                physical = physical.replace(placeholder, value)
            self._specs[logical_name] = ModelSpec(
                logical_name=logical_name,
                physical_model=physical,
                provider=provider_name,
                temperature=float(spec.get("temperature", 0.7)),
                max_tokens=int(spec.get("max_tokens", 2048)),
            )

    def get(self, logical_name: str) -> ModelSpec:
        """Return the ModelSpec for a logical model name.

        Args:
            logical_name: Logical model alias (e.g. ``"chat_model"``).

        Returns:
            Corresponding ModelSpec.

        Raises:
            KeyError: If the logical name is not in the registry.
        """
        if logical_name not in self._specs:
            raise KeyError(
                f"Model '{logical_name}' not found in registry. "
                f"Available: {list(self._specs)}"
            )
        return self._specs[logical_name]

    def physical_model(self, logical_name: str) -> str:
        """Shorthand to get the physical model name for a logical name.

        Args:
            logical_name: Logical model alias.

        Returns:
            Physical model identifier string.
        """
        return self.get(logical_name).physical_model

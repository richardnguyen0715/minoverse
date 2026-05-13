"""Prompt loader — reads versioned YAML prompt files from disk.

Prompt files live in ``src/ai/prompts/tasks/`` and follow the format::

    name: <identifier>
    version: v1
    system: |
      <system instruction>
    user_template: |
      <template with {placeholders}>
    temperature: 0.3
    max_tokens: 1024
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_TASKS_DIR = Path(__file__).parent / "tasks"


@dataclass
class PromptTemplate:
    """A loaded prompt template.

    Attributes:
        name: Prompt identifier (from YAML ``name`` field).
        version: Version string (e.g. ``"v1"``).
        system: System instruction string.
        user_template: User prompt template with ``{placeholder}`` slots.
        temperature: Recommended sampling temperature.
        max_tokens: Recommended max output tokens.
    """

    name: str
    version: str
    system: str
    user_template: str
    temperature: float = 0.3
    max_tokens: int = 2048


class PromptLoader:
    """Loads prompt YAML files from the tasks directory.

    Files are cached in memory after first load for performance.
    """

    def __init__(self) -> None:
        self._cache: dict[str, PromptTemplate] = {}

    def load(self, prompt_name: str) -> PromptTemplate:
        """Load a prompt by name, reading from ``tasks/<prompt_name>.yaml``.

        Args:
            prompt_name: Base name of the YAML file (without extension).

        Returns:
            Parsed PromptTemplate.

        Raises:
            FileNotFoundError: If no matching YAML file exists.
        """
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        path = _TASKS_DIR / f"{prompt_name}.yaml"
        if not path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {path}. "
                f"Available prompts: {[p.stem for p in _TASKS_DIR.glob('*.yaml')]}"
            )

        raw = yaml.safe_load(path.read_text())
        template = PromptTemplate(
            name=raw["name"],
            version=raw["version"],
            system=raw["system"],
            user_template=raw["user_template"],
            temperature=float(raw.get("temperature", 0.3)),
            max_tokens=int(raw.get("max_tokens", 2048)),
        )
        self._cache[prompt_name] = template
        return template

    def render(self, template: PromptTemplate, **kwargs: object) -> str:
        """Render a prompt template by substituting ``{placeholder}`` slots.

        Args:
            template: Loaded PromptTemplate.
            **kwargs: Values to substitute into ``user_template``.

        Returns:
            Rendered user prompt string.
        """
        return template.user_template.format(**kwargs)

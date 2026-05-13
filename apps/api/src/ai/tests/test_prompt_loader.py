"""Tests for PromptLoader."""
from __future__ import annotations

import pytest

from src.ai.prompts.loader import PromptLoader


def test_load_summarize_prompt() -> None:
    loader = PromptLoader()
    template = loader.load("summarize")

    assert template.name == "summarize_resource"
    assert template.version == "v1"
    assert len(template.system) > 0
    assert "{content}" in template.user_template


def test_render_prompt_template() -> None:
    loader = PromptLoader()
    template = loader.load("summarize")
    rendered = loader.render(template, content="my test content")

    assert "my test content" in rendered
    assert "{content}" not in rendered


def test_load_unknown_prompt_raises() -> None:
    loader = PromptLoader()
    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent_prompt_xyz")

"""Skill: extract a durable semantic concept from resource content."""
from __future__ import annotations

import json
import re

import structlog

from src.ai.runtimes.llm_runtime import LLMRuntime

logger = structlog.get_logger(__name__)

_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


async def run_synthesize_semantic(
    content: str,
    runtime: LLMRuntime,
) -> dict:
    """Extract the most reusable knowledge concept from content.

    Args:
        content: Source text to analyse.
        runtime: LLMRuntime instance.

    Returns:
        Dict with keys: concept, content.
        Returns a safe fallback dict on any error.
    """
    _empty: dict = {"concept": "", "content": ""}

    try:
        response = await runtime.run_skill(
            prompt_name="synthesize_semantic",
            logical_model="chat_model",
            render_kwargs={"content": content[:4000]},
        )
    except Exception as exc:
        logger.warning("synthesize_semantic_skill_failed", error=str(exc))
        return _empty

    try:
        data = json.loads(_extract_json(response))
        if not isinstance(data, dict):
            raise ValueError("Response is not a dict")
        return {
            "concept": str(data.get("concept", "")),
            "content": str(data.get("content", "")),
        }
    except (json.JSONDecodeError, ValueError, Exception) as exc:
        logger.warning("synthesize_semantic_json_parse_failed", error=str(exc))
        return _empty

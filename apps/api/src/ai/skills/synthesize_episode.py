"""Skill: synthesize a conversation into an episodic memory entry."""
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


async def run_synthesize_episode(
    conversation: str,
    runtime: LLMRuntime,
) -> dict:
    """Distil a conversation into a compact episodic memory.

    Args:
        conversation: Formatted conversation transcript.
        runtime: LLMRuntime instance.

    Returns:
        Dict with keys: title, content.
        Returns a safe fallback dict on any error.
    """
    _empty: dict = {"title": "Research Session", "content": ""}

    try:
        response = await runtime.run_skill(
            prompt_name="synthesize_episode",
            logical_model="chat_model",
            render_kwargs={"conversation": conversation},
        )
    except Exception as exc:
        logger.warning("synthesize_episode_skill_failed", error=str(exc))
        return _empty

    try:
        data = json.loads(_extract_json(response))
        if not isinstance(data, dict):
            raise ValueError("Response is not a dict")
        return {
            "title": str(data.get("title", "Research Session")),
            "content": str(data.get("content", "")),
        }
    except (json.JSONDecodeError, ValueError, Exception) as exc:
        logger.warning("synthesize_episode_json_parse_failed", error=str(exc))
        return _empty

"""Skill: extract named entities from a resource."""
from __future__ import annotations

import json
import re

import structlog

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.enrichment.schemas.enrichment_schemas import EntityResult

logger = structlog.get_logger(__name__)

_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


async def run_extract_entities(content: str, runtime: LLMRuntime) -> EntityResult:
    """Extract named entities from content using the AI runtime.

    Args:
        content: Raw text to analyse (truncated to 4000 chars internally).
        runtime: LLMRuntime instance.

    Returns:
        EntityResult with tools, frameworks, papers, and methodologies.
        Returns empty lists on any error.
    """
    _empty = EntityResult(tools=[], frameworks=[], papers=[], methodologies=[])

    try:
        response = await runtime.run_skill(
            prompt_name="extract_entities",
            logical_model="chat_model",
            render_kwargs={"content": content[:4000]},
        )
    except Exception as exc:
        logger.warning("extract_entities_skill_failed", error=str(exc))
        return _empty

    try:
        data = json.loads(_extract_json(response))

        def _as_str_list(key: str) -> list[str]:
            val = data.get(key, []) if isinstance(data, dict) else []
            return [str(v) for v in val] if isinstance(val, list) else []

        return EntityResult(
            tools=_as_str_list("tools"),
            frameworks=_as_str_list("frameworks"),
            papers=_as_str_list("papers"),
            methodologies=_as_str_list("methodologies"),
        )
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("extract_entities_skill_json_parse_failed", error=str(exc))
        return _empty

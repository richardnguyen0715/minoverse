"""Skill: generate topic tags for a resource."""
from __future__ import annotations

import json
import re

import structlog

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.enrichment.schemas.enrichment_schemas import TaggingResult

logger = structlog.get_logger(__name__)

_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


async def run_generate_tags(
    content: str,
    runtime: LLMRuntime,
    *,
    max_tags: int = 10,
) -> TaggingResult:
    """Generate topic tags for content using the AI runtime.

    Args:
        content: Raw text to tag (truncated to 4000 chars internally).
        runtime: LLMRuntime instance.
        max_tags: Maximum number of tags to return.

    Returns:
        TaggingResult with normalized tag list.
        Returns empty tags on any error.
    """
    try:
        response = await runtime.run_skill(
            prompt_name="generate_tags",
            logical_model="chat_model",
            render_kwargs={"content": content[:4000]},
        )
    except Exception as exc:
        logger.warning("generate_tags_skill_failed", error=str(exc))
        return TaggingResult(tags=[])

    try:
        data = json.loads(_extract_json(response))
        raw_tags: list[object] = data.get("tags", []) if isinstance(data, dict) else []
        normalized: list[str] = []
        seen: set[str] = set()
        for tag in raw_tags:
            cleaned = str(tag).lower().strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)
        return TaggingResult(tags=normalized[:max_tags])
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("generate_tags_skill_json_parse_failed", error=str(exc))
        return TaggingResult(tags=[])

"""Skill: summarize a resource using the summarize_resource prompt."""
from __future__ import annotations

import json
import re

import structlog

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.enrichment.schemas.enrichment_schemas import SummaryResult

logger = structlog.get_logger(__name__)

_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    """Strip markdown code fences and return the inner JSON string."""
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


async def run_summarize(content: str, runtime: LLMRuntime) -> SummaryResult:
    """Summarize content using the AI runtime.

    Args:
        content: Raw text to summarize (truncated to 4000 chars internally).
        runtime: LLMRuntime instance.

    Returns:
        SummaryResult with concise, detailed, and key_insights fields.
        Returns empty fields on any parse or generation error.
    """
    try:
        response = await runtime.run_skill(
            prompt_name="summarize",
            logical_model="chat_model",
            render_kwargs={"content": content[:4000]},
        )
    except Exception as exc:
        logger.warning("summarize_skill_failed", error=str(exc))
        return SummaryResult(concise="", detailed="", key_insights=[])

    try:
        data = json.loads(_extract_json(response))
        return SummaryResult(
            concise=str(data.get("concise", "")),
            detailed=str(data.get("detailed", "")),
            key_insights=[str(i) for i in data.get("key_insights", [])],
        )
    except json.JSONDecodeError:
        logger.warning("summarize_skill_json_parse_failed")
        return SummaryResult(concise=response[:200], detailed=response, key_insights=[])

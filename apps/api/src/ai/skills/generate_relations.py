"""Skill: generate semantic relations between knowledge graph entities."""
from __future__ import annotations

import json

import structlog

from src.ai.runtimes.llm_runtime import LLMRuntime

logger = structlog.get_logger(__name__)


async def run_generate_relations(
    entity_list_str: str,
    runtime: LLMRuntime,
) -> list[dict[str, str]]:
    """Generate semantic relations between entities using the AI runtime.

    Args:
        entity_list_str: Newline-separated entity list string.
        runtime: LLMRuntime instance.

    Returns:
        List of dicts with ``source``, ``relation_type``, and ``target`` keys.
        Returns empty list on any error.
    """
    try:
        response = await runtime.run_skill(
            prompt_name="generate_relations",
            logical_model="chat_model",
            render_kwargs={"entity_list": entity_list_str},
        )
    except Exception as exc:
        logger.warning("generate_relations_skill_failed", error=str(exc))
        return []

    try:
        parsed = json.loads(response)
        if not isinstance(parsed, list):
            logger.warning("generate_relations_skill_not_a_list")
            return []
        return [item for item in parsed if isinstance(item, dict)]
    except json.JSONDecodeError as exc:
        logger.warning("generate_relations_skill_json_parse_failed", error=str(exc))
        return []

"""Skill: ask the copilot a question using knowledge-vault context."""
from __future__ import annotations

import json
import re

import structlog

from src.ai.runtimes.llm_runtime import LLMRuntime
from src.core.exceptions import LMStudioUnavailableError

logger = structlog.get_logger(__name__)

_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


async def run_copilot_ask(
    question: str,
    context: str,
    runtime: LLMRuntime,
) -> dict:
    """Ask the copilot a question using the provided knowledge-vault context.

    Args:
        question: The user's question.
        context: Formatted context string from contextual retrieval.
        runtime: LLMRuntime instance.

    Returns:
        Dict with keys: answer, confidence, cited_resources.
        Returns a safe fallback dict on any error.
    """
    _empty: dict = {"answer": "", "confidence": "low", "cited_resources": []}

    try:
        response = await runtime.run_skill(
            prompt_name="copilot_ask",
            logical_model="chat_model",
            render_kwargs={"question": question, "context": context},
        )
    except LMStudioUnavailableError:
        raise  # propagate so the route can return 503
    except Exception as exc:
        logger.warning("copilot_ask_skill_failed", error=str(exc))
        return _empty

    try:
        data = json.loads(_extract_json(response))
        if not isinstance(data, dict):
            raise ValueError("Response is not a dict")
        return {
            "answer": str(data.get("answer", "")),
            "confidence": str(data.get("confidence", "low")),
            "cited_resources": list(data.get("cited_resources", [])),
        }
    except (json.JSONDecodeError, ValueError, Exception) as exc:
        logger.warning("copilot_ask_skill_json_parse_failed", error=str(exc), raw=response[:200])
        return _empty

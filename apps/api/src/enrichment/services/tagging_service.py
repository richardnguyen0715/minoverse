"""AI tagging service.

Extracts normalized, deduplicated topic tags from content via an
Ollama-compatible language model. Returns an empty TaggingResult on any
failure to preserve graceful degradation.

Prompts are loaded from ``src/ai/prompts/tasks/generate_tags.yaml`` via
``PromptLoader`` rather than being defined as inline strings.
"""
import json
import time

import structlog

from src.ai.prompts.loader import PromptLoader
from src.enrichment.schemas.enrichment_schemas import TaggingResult
from src.enrichment.services.ollama_client import OllamaClientProtocol

logger = structlog.get_logger(__name__)

_prompt_loader = PromptLoader()


async def generate_ai_tags(
    content: str,
    client: OllamaClientProtocol,
    *,
    model: str = "qwen3",
    max_tags: int = 10,
) -> TaggingResult:
    """Extract normalized topic tags from the provided content.

    Tags are normalized to lowercase, stripped of whitespace, deduplicated,
    and capped at ``max_tags``. Returns empty tags on any error.

    Args:
        content: Raw text content to tag (truncated to 4000 chars).
        client: OllamaClientProtocol implementation used for generation.
        model: Ollama model identifier to use.
        max_tags: Maximum number of tags to return.

    Returns:
        TaggingResult with a normalized list of tag strings.
    """
    template = _prompt_loader.load("generate_tags")
    prompt = _prompt_loader.render(template, content=content[:4000])

    start = time.monotonic()
    try:
        response = await client.generate(model=model, prompt=prompt, system=template.system)
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "ai_call",
            prompt="generate_tags",
            prompt_version=template.version,
            model=model,
            provider="ollama",
            latency_ms=latency_ms,
            success=True,
        )
        data = json.loads(response)
        raw_tags: list[object] = data.get("tags", []) if isinstance(data, dict) else []
        normalized: list[str] = []
        seen: set[str] = set()
        for tag in raw_tags:
            cleaned = str(tag).lower().strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)
        return TaggingResult(tags=normalized[:max_tags])
    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "tagging_generation_failed",
            error=str(exc),
            model=model,
            prompt="generate_tags",
            prompt_version=template.version,
            latency_ms=latency_ms,
        )
        return TaggingResult(tags=[])

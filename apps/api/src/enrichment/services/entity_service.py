"""Entity extraction service.

Identifies named entities (tools, frameworks, papers, methodologies) in
content via an Ollama-compatible language model. Returns an empty
EntityResult on any failure.

Prompts are loaded from ``src/ai/prompts/tasks/extract_entities.yaml`` via
``PromptLoader`` rather than being defined as inline strings.
"""
import json
import time

import structlog

from src.ai.prompts.loader import PromptLoader
from src.enrichment.schemas.enrichment_schemas import EntityResult
from src.enrichment.services.ollama_client import OllamaClientProtocol

logger = structlog.get_logger(__name__)

_prompt_loader = PromptLoader()


async def extract_entities(
    content: str,
    client: OllamaClientProtocol,
    *,
    model: str = "qwen3",
) -> EntityResult:
    """Extract structured named entities from the provided content.

    Missing keys in the model response default to empty lists. Returns
    an empty EntityResult on any error to preserve graceful degradation.

    Args:
        content: Raw text content to analyse (truncated to 4000 chars).
        client: OllamaClientProtocol implementation used for generation.
        model: Ollama model identifier to use.

    Returns:
        EntityResult with tools, frameworks, papers, and methodologies.
    """
    template = _prompt_loader.load("extract_entities")
    prompt = _prompt_loader.render(template, content=content[:4000])

    start = time.monotonic()
    try:
        response = await client.generate(model=model, prompt=prompt, system=template.system)
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "ai_call",
            prompt="extract_entities",
            prompt_version=template.version,
            model=model,
            provider="ollama",
            latency_ms=latency_ms,
            success=True,
        )
        data = json.loads(response)

        def _as_str_list(key: str) -> list[str]:
            val = data.get(key, []) if isinstance(data, dict) else []
            return [str(v) for v in val] if isinstance(val, list) else []

        return EntityResult(
            tools=_as_str_list("tools"),
            frameworks=_as_str_list("frameworks"),
            papers=_as_str_list("papers"),
            methodologies=_as_str_list("methodologies"),
        )
    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "entity_extraction_failed",
            error=str(exc),
            model=model,
            prompt="extract_entities",
            prompt_version=template.version,
            latency_ms=latency_ms,
        )
        return EntityResult(tools=[], frameworks=[], papers=[], methodologies=[])

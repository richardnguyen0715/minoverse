"""Summary generation service.

Produces concise summaries, detailed summaries, and key insights for a
piece of content by calling an Ollama-compatible language model. All
errors are handled gracefully — no exception propagates to the caller.

Prompts are loaded from ``src/ai/prompts/tasks/summarize.yaml`` via
``PromptLoader`` rather than being defined as inline strings.
"""
import json
import time

import structlog

from src.ai.prompts.loader import PromptLoader
from src.enrichment.schemas.enrichment_schemas import SummaryResult
from src.enrichment.services.ollama_client import OllamaClientProtocol

logger = structlog.get_logger(__name__)

_prompt_loader = PromptLoader()


async def generate_summary(
    content: str,
    client: OllamaClientProtocol,
    *,
    model: str = "qwen3",
) -> SummaryResult:
    """Generate a structured summary for the provided content.

    Sends a single prompt to the language model requesting JSON output
    with three keys. Falls back to a degraded result on any error to
    ensure enrichment never blocks ingestion.

    Args:
        content: Raw text content to summarize (truncated to 4000 chars).
        client: OllamaClientProtocol implementation used for generation.
        model: Ollama model identifier to use.

    Returns:
        SummaryResult with concise, detailed, and key_insights fields.
        Fields may be empty or partial on degraded / error paths.
    """
    template = _prompt_loader.load("summarize")
    prompt = _prompt_loader.render(template, content=content[:4000])

    start = time.monotonic()
    try:
        response = await client.generate(model=model, prompt=prompt, system=template.system)
    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "summary_generation_failed",
            error=str(exc),
            model=model,
            prompt="summarize",
            prompt_version=template.version,
            latency_ms=latency_ms,
        )
        return SummaryResult(concise="", detailed="", key_insights=[])

    latency_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        "ai_call",
        prompt="summarize",
        prompt_version=template.version,
        model=model,
        provider="ollama",
        latency_ms=latency_ms,
        success=True,
    )

    try:
        data = json.loads(response)
        return SummaryResult(
            concise=str(data.get("concise", "")),
            detailed=str(data.get("detailed", "")),
            key_insights=[str(i) for i in data.get("key_insights", [])],
        )
    except json.JSONDecodeError:
        logger.warning("summary_json_parse_failed", model=model)
        return SummaryResult(
            concise=response[:200],
            detailed=response,
            key_insights=[],
        )

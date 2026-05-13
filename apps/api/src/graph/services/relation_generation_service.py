"""Relation generation service — uses Ollama to infer semantic relations between entities.

For each resource, fetches its concept entities and asks the LLM to identify
directed relations. Results are upserted as ConceptRelation records.

Prompts are loaded from ``src/ai/prompts/tasks/generate_relations.yaml`` via
``PromptLoader`` rather than being defined as inline strings.
"""
from __future__ import annotations

import json
import time
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.prompts.loader import PromptLoader
from src.core.config import settings
from src.core.exceptions import OllamaUnavailableError
from src.enrichment.services.ollama_client import OllamaClientProtocol, strip_thinking
from src.graph.entities.concept_relation import ConceptRelation
from src.graph.repositories.concept_entity_repository import get_entities_for_resource
from src.graph.repositories.concept_relation_repository import upsert_concept_relation

logger = structlog.get_logger(__name__)

_VALID_RELATION_TYPES = frozenset({"related_to", "inspired_by", "references", "extends"})

_prompt_loader = PromptLoader()


async def generate_relations_for_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
    ollama_client: OllamaClientProtocol,
) -> list[ConceptRelation]:
    """Generate and persist semantic relations between entities for a resource.

    Fetches the resource's concept entities, prompts Ollama for relations,
    and upserts each valid relation into concept_relations.

    Gracefully handles Ollama errors and invalid JSON — logs a warning and
    returns an empty list rather than crashing the worker.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource.
        ollama_client: OllamaClientProtocol implementation (injected for testability).

    Returns:
        List of upserted ConceptRelation records (may be empty).
    """
    entities = await get_entities_for_resource(session, resource_id)

    if len(entities) < 2:
        logger.debug(
            "skipping_relation_generation_too_few_entities",
            resource_id=str(resource_id),
            count=len(entities),
        )
        return []

    entity_name_to_id = {e.name.lower(): e.id for e in entities}
    entity_list = "\n".join(f"- {e.name} ({e.entity_type})" for e in entities)

    template = _prompt_loader.load("generate_relations")
    prompt = _prompt_loader.render(template, entity_list=entity_list)

    start = time.monotonic()
    try:
        raw = await ollama_client.generate(
            model=settings.chat_model,
            prompt=prompt,
            system=template.system,
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "ai_call",
            prompt="generate_relations",
            prompt_version=template.version,
            model=settings.chat_model,
            provider="ollama",
            latency_ms=latency_ms,
            success=True,
        )
    except OllamaUnavailableError as exc:
        logger.warning(
            "relation_generation_ollama_unavailable",
            resource_id=str(resource_id),
            error=str(exc),
        )
        return []
    except Exception as exc:
        logger.warning(
            "relation_generation_unexpected_error",
            resource_id=str(resource_id),
            error=str(exc),
        )
        return []

    try:
        parsed = json.loads(strip_thinking(raw).strip())
        if not isinstance(parsed, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            "relation_generation_invalid_json",
            resource_id=str(resource_id),
            error=str(exc),
            raw_response=raw[:200],
        )
        return []

    created: list[ConceptRelation] = []
    for item in parsed:
        source_name = str(item.get("source", "")).strip().lower()
        target_name = str(item.get("target", "")).strip().lower()
        relation_type = str(item.get("relation_type", "")).strip().lower()

        if relation_type not in _VALID_RELATION_TYPES:
            continue

        src_id = entity_name_to_id.get(source_name)
        dst_id = entity_name_to_id.get(target_name)

        if src_id is None or dst_id is None or src_id == dst_id:
            continue

        relation = await upsert_concept_relation(
            session,
            src_id=src_id,
            dst_id=dst_id,
            relation_type=relation_type,
            weight=1.0,
            resource_id=resource_id,
            generated_by="ollama",
        )
        created.append(relation)

    logger.info(
        "relations_generated",
        resource_id=str(resource_id),
        count=len(created),
    )
    return created

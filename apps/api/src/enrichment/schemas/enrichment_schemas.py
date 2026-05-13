"""Pydantic schemas and enumerations for AI enrichment output.

Defines the canonical enrichment types, per-type result models,
and the unified EnrichmentOutput schema used at API boundaries.
"""
from enum import StrEnum

from pydantic import BaseModel


class EnrichmentType(StrEnum):
    """Canonical set of AI enrichment types produced by the pipeline."""

    SUMMARY_CONCISE = "summary_concise"
    SUMMARY_DETAILED = "summary_detailed"
    KEY_INSIGHTS = "key_insights"
    AI_TAGS = "ai_tags"
    ENTITIES = "entities"
    RELATED = "related"


class SummaryResult(BaseModel):
    """Structured result of the summary enrichment step.

    Attributes:
        concise: Two to three sentence summary.
        detailed: Comprehensive paragraph-length summary.
        key_insights: List of actionable or notable insight strings.
    """

    concise: str
    detailed: str
    key_insights: list[str]


class TaggingResult(BaseModel):
    """Structured result of the AI tagging step.

    Attributes:
        tags: Normalized, deduplicated list of tag strings (max 10).
    """

    tags: list[str]


class EntityResult(BaseModel):
    """Structured result of the entity extraction step.

    Attributes:
        tools: Software tools mentioned.
        frameworks: ML or software frameworks mentioned.
        papers: Paper titles or arXiv IDs mentioned.
        methodologies: Techniques or algorithms mentioned.
    """

    tools: list[str]
    frameworks: list[str]
    papers: list[str]
    methodologies: list[str]


class RelatedResult(BaseModel):
    """Structured result of the related-resource discovery step.

    Attributes:
        resource_ids: UUIDs (as strings) of related resources.
    """

    resource_ids: list[str]


class EnrichmentOutput(BaseModel):
    """Unified enrichment record returned at API boundaries.

    Attributes:
        resource_id: UUID of the enriched resource.
        enrichment_type: The type of enrichment.
        content: Raw AI output stored as a dictionary.
        model_name: Identifier of the model that produced this enrichment.
        prompt_version: Prompt template version used.
        processing_ms: Wall-clock time in milliseconds for generation.
    """

    resource_id: str
    enrichment_type: EnrichmentType
    content: dict  # type: ignore[type-arg]
    model_name: str
    prompt_version: str
    processing_ms: int

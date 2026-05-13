"""Pydantic schemas for the knowledge graph domain (Phase 4)."""
from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict


class EntityType(str, Enum):
    concept = "concept"
    person = "person"
    technology = "technology"
    framework = "framework"
    organization = "organization"
    place = "place"


class RelationType(str, Enum):
    related_to = "related_to"
    inspired_by = "inspired_by"
    references = "references"
    extends = "extends"


class ConceptEntityOut(BaseModel):
    id: uuid.UUID
    name: str
    entity_type: EntityType
    canonical_name: str
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ConceptRelationOut(BaseModel):
    id: uuid.UUID
    source_entity_id: uuid.UUID
    target_entity_id: uuid.UUID
    relation_type: RelationType
    weight: float
    generated_by: str
    model_config = ConfigDict(from_attributes=True)


class GraphNode(BaseModel):
    id: uuid.UUID
    name: str
    entity_type: EntityType
    description: str | None = None


class GraphEdge(BaseModel):
    source: uuid.UUID
    target: uuid.UUID
    relation_type: RelationType
    weight: float


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

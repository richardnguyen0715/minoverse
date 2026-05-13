"""Pydantic v2 schemas for the memory / copilot domain (Phase 5)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemorySessionOut(BaseModel):
    id: uuid.UUID
    title: str
    context: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryTurnOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemorySessionDetail(BaseModel):
    id: uuid.UUID
    title: str
    context: dict | None = None
    turns: list[MemoryTurnOut]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EpisodicMemoryOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    resource_ids: list | None = None
    session_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SemanticMemoryOut(BaseModel):
    id: uuid.UUID
    concept: str
    content: str
    source_resource_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AskRequest(BaseModel):
    question: str
    session_id: uuid.UUID | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    session_id: uuid.UUID
    turn_id: uuid.UUID

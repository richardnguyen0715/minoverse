"""Pydantic schemas for the sync / event-log domain (Phase 6)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SyncEventCreate(BaseModel):
    event_type: str
    resource_id: uuid.UUID | None = None
    resource_path: str | None = None
    device_id: str | None = None
    payload: dict | None = None


class SyncEventRead(BaseModel):
    id: uuid.UUID
    event_type: str
    resource_id: uuid.UUID | None = None
    resource_path: str | None = None
    operation_id: uuid.UUID
    device_id: str | None = None
    vector_clock: dict
    payload: dict | None = None
    applied: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SyncEventFilter(BaseModel):
    event_type: str | None = None
    resource_id: uuid.UUID | None = None
    applied: bool | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class SyncEventPage(BaseModel):
    items: list[SyncEventRead]
    total: int

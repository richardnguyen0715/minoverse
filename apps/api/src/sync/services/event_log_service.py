"""Event log service — emit, list, and replay sync events."""
from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.sync.repositories import sync_event_repository as _repo
from src.sync.schemas.sync_schemas import SyncEventFilter, SyncEventPage, SyncEventRead

logger = structlog.get_logger(__name__)


async def emit(
    db: AsyncSession,
    event_type: str,
    resource_id: uuid.UUID | None = None,
    resource_path: str | None = None,
    payload: dict | None = None,
    device_id: str | None = None,
) -> SyncEventRead:
    event = await _repo.log_event(db, event_type, resource_id, resource_path, payload, device_id)
    return SyncEventRead.model_validate(event)


async def list_events(db: AsyncSession, f: SyncEventFilter) -> SyncEventPage:
    items = await _repo.list_events(db, f)
    total = await _repo.count_events(db, f)
    return SyncEventPage(
        items=[SyncEventRead.model_validate(e) for e in items],
        total=total,
    )


async def replay_events(
    db: AsyncSession,
    since: datetime,
    event_types: list[str] | None = None,
) -> list[SyncEventRead]:
    events = await _repo.get_events_since(db, since, event_types)
    replayed = []
    for event in events:
        if not event.applied:
            await _repo.mark_applied(db, event.id)
            event.applied = True
        replayed.append(SyncEventRead.model_validate(event))
    logger.info("sync_replay_complete", count=len(replayed))
    return replayed

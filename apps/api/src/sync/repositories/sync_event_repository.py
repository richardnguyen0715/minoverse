"""Sync event repository — CRUD for sync_events table."""
from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.sync.entities.sync_event import SyncEvent
from src.sync.schemas.sync_schemas import SyncEventFilter

logger = structlog.get_logger(__name__)


async def log_event(
    db: AsyncSession,
    event_type: str,
    resource_id: uuid.UUID | None = None,
    resource_path: str | None = None,
    payload: dict | None = None,
    device_id: str | None = None,
) -> SyncEvent:
    event = SyncEvent(
        event_type=event_type,
        resource_id=resource_id,
        resource_path=resource_path,
        payload=payload,
        device_id=device_id,
    )
    db.add(event)
    await db.flush()
    logger.info("sync_event_logged", event_type=event_type, event_id=str(event.id))
    return event


async def list_events(db: AsyncSession, f: SyncEventFilter) -> list[SyncEvent]:
    q = select(SyncEvent).order_by(SyncEvent.created_at.desc())
    if f.event_type:
        q = q.where(SyncEvent.event_type == f.event_type)
    if f.resource_id:
        q = q.where(SyncEvent.resource_id == f.resource_id)
    if f.applied is not None:
        q = q.where(SyncEvent.applied == f.applied)
    q = q.offset(f.offset).limit(f.limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def count_events(db: AsyncSession, f: SyncEventFilter) -> int:
    q = select(func.count()).select_from(SyncEvent)
    if f.event_type:
        q = q.where(SyncEvent.event_type == f.event_type)
    if f.resource_id:
        q = q.where(SyncEvent.resource_id == f.resource_id)
    if f.applied is not None:
        q = q.where(SyncEvent.applied == f.applied)
    result = await db.execute(q)
    return result.scalar_one()


async def mark_applied(db: AsyncSession, event_id: uuid.UUID) -> SyncEvent | None:
    await db.execute(
        update(SyncEvent).where(SyncEvent.id == event_id).values(applied=True)
    )
    result = await db.execute(select(SyncEvent).where(SyncEvent.id == event_id))
    return result.scalar_one_or_none()


async def get_events_since(
    db: AsyncSession,
    created_after: datetime,
    event_types: list[str] | None = None,
) -> list[SyncEvent]:
    q = (
        select(SyncEvent)
        .where(SyncEvent.created_at >= created_after)
        .order_by(SyncEvent.created_at.asc())
    )
    if event_types:
        q = q.where(SyncEvent.event_type.in_(event_types))
    result = await db.execute(q)
    return list(result.scalars().all())

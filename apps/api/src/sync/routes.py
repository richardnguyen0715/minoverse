"""FastAPI routes for the sync / event-log domain (Phase 6)."""
from __future__ import annotations

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.sync.schemas.sync_schemas import (
    SyncEventCreate,
    SyncEventFilter,
    SyncEventPage,
    SyncEventRead,
)
from src.sync.services import event_log_service as _svc

logger = structlog.get_logger(__name__)
sync_router = APIRouter(prefix="/sync", tags=["sync"])


@sync_router.get("/events", response_model=SyncEventPage)
async def list_events(
    event_type: str | None = Query(None),
    applied: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
) -> SyncEventPage:
    f = SyncEventFilter(event_type=event_type, applied=applied, limit=limit, offset=offset)
    return await _svc.list_events(db, f)


@sync_router.post("/emit", response_model=SyncEventRead)
async def emit_event(
    body: SyncEventCreate,
    db: AsyncSession = Depends(get_async_session),
) -> SyncEventRead:
    return await _svc.emit(
        db,
        body.event_type,
        body.resource_id,
        body.resource_path,
        body.payload,
        body.device_id,
    )


@sync_router.post("/replay", response_model=list[SyncEventRead])
async def replay_events(
    since: datetime = Query(..., description="Replay events created after this timestamp"),
    event_types: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> list[SyncEventRead]:
    return await _svc.replay_events(db, since, event_types)

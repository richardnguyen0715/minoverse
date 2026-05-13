"""Unit tests for Phase 6 — Event Sourcing (no DB, no network).

Tests cover:
- Pydantic schema validation for all Phase 6 schemas
- sync_event_repository functions (mocked AsyncSession)
- event_log_service.emit, list_events, replay_events
- FastAPI routes: GET /sync/events, POST /sync/emit, POST /sync/replay
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

_NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sync_event(
    event_type: str = "resource.upserted",
    applied: bool = False,
    resource_id: uuid.UUID | None = None,
) -> MagicMock:
    e = MagicMock()
    e.id = uuid.uuid4()
    e.event_type = event_type
    e.resource_id = resource_id or uuid.uuid4()
    e.resource_path = "/vault/notes/test.md"
    e.operation_id = uuid.uuid4()
    e.device_id = "device-abc"
    e.vector_clock = {}
    e.payload = None
    e.applied = applied
    e.created_at = _NOW
    return e


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_sync_event_create_minimal(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventCreate

        obj = SyncEventCreate(event_type="resource.created")
        assert obj.event_type == "resource.created"
        assert obj.resource_id is None
        assert obj.resource_path is None
        assert obj.device_id is None
        assert obj.payload is None

    def test_sync_event_create_all_fields(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventCreate

        rid = uuid.uuid4()
        obj = SyncEventCreate(
            event_type="resource.updated",
            resource_id=rid,
            resource_path="/vault/notes/foo.md",
            device_id="my-device",
            payload={"key": "value"},
        )
        assert obj.resource_id == rid
        assert obj.device_id == "my-device"
        assert obj.payload == {"key": "value"}

    def test_sync_event_read_model_validate(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventRead

        mock_event = _make_sync_event()
        read = SyncEventRead.model_validate(mock_event)
        assert read.id == mock_event.id
        assert read.event_type == mock_event.event_type
        assert read.applied is False
        assert read.vector_clock == {}

    def test_sync_event_filter_defaults(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventFilter

        f = SyncEventFilter()
        assert f.event_type is None
        assert f.resource_id is None
        assert f.applied is None
        assert f.limit == 50
        assert f.offset == 0

    def test_sync_event_filter_validation(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventFilter

        with pytest.raises(ValidationError):
            SyncEventFilter(limit=0)

        with pytest.raises(ValidationError):
            SyncEventFilter(offset=-1)

        f = SyncEventFilter(limit=500, offset=100)
        assert f.limit == 500
        assert f.offset == 100

    def test_sync_event_page_structure(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventPage, SyncEventRead

        mock = _make_sync_event()
        read = SyncEventRead.model_validate(mock)
        page = SyncEventPage(items=[read], total=1)
        assert page.total == 1
        assert len(page.items) == 1
        assert page.items[0].event_type == mock.event_type

    def test_sync_event_read_device_id_and_vector_clock(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventRead

        mock = _make_sync_event()
        mock.device_id = "device-xyz"
        mock.vector_clock = {"node1": 3}
        read = SyncEventRead.model_validate(mock)
        assert read.device_id == "device-xyz"
        assert read.vector_clock == {"node1": 3}


# ---------------------------------------------------------------------------
# event_log_service tests
# ---------------------------------------------------------------------------

class TestEventLogService:
    @pytest.mark.asyncio
    async def test_emit_calls_log_event_and_returns_read(self) -> None:
        from src.sync.services.event_log_service import emit

        db = AsyncMock()
        mock_event = _make_sync_event()

        with patch(
            "src.sync.services.event_log_service._repo.log_event",
            new_callable=AsyncMock,
            return_value=mock_event,
        ) as mock_log:
            result = await emit(db, "resource.created")

        mock_log.assert_awaited_once()
        assert result.event_type == "resource.upserted"

    @pytest.mark.asyncio
    async def test_list_events_returns_page(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventFilter
        from src.sync.services.event_log_service import list_events

        db = AsyncMock()
        mock_event = _make_sync_event()
        f = SyncEventFilter(limit=10)

        with (
            patch(
                "src.sync.services.event_log_service._repo.list_events",
                new_callable=AsyncMock,
                return_value=[mock_event],
            ),
            patch(
                "src.sync.services.event_log_service._repo.count_events",
                new_callable=AsyncMock,
                return_value=1,
            ),
        ):
            page = await list_events(db, f)

        assert page.total == 1
        assert len(page.items) == 1
        assert page.items[0].event_type == mock_event.event_type

    @pytest.mark.asyncio
    async def test_list_events_applied_filter(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventFilter
        from src.sync.services.event_log_service import list_events

        db = AsyncMock()
        f = SyncEventFilter(applied=True)

        with (
            patch(
                "src.sync.services.event_log_service._repo.list_events",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "src.sync.services.event_log_service._repo.count_events",
                new_callable=AsyncMock,
                return_value=0,
            ),
        ):
            page = await list_events(db, f)

        assert page.total == 0
        assert page.items == []

    @pytest.mark.asyncio
    async def test_replay_events_marks_unapplied(self) -> None:
        from src.sync.services.event_log_service import replay_events

        db = AsyncMock()
        unapplied = _make_sync_event(applied=False)
        applied = _make_sync_event(applied=True)

        with (
            patch(
                "src.sync.services.event_log_service._repo.get_events_since",
                new_callable=AsyncMock,
                return_value=[unapplied, applied],
            ),
            patch(
                "src.sync.services.event_log_service._repo.mark_applied",
                new_callable=AsyncMock,
                return_value=unapplied,
            ) as mock_mark,
        ):
            result = await replay_events(db, _NOW)

        # Only the unapplied event triggers mark_applied
        mock_mark.assert_awaited_once_with(db, unapplied.id)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

def _make_test_app():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.core.database import get_async_session
    from src.sync.routes import sync_router

    app = FastAPI()
    app.include_router(sync_router)

    db_mock = AsyncMock()

    async def override_db():
        yield db_mock

    app.dependency_overrides[get_async_session] = override_db
    return TestClient(app), db_mock


class TestRoutes:
    def test_get_events_returns_200(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventPage
        from src.sync.services import event_log_service as svc

        client, _ = _make_test_app()

        page = SyncEventPage(items=[], total=0)

        with patch.object(svc, "list_events", new=AsyncMock(return_value=page)):
            resp = client.get("/sync/events")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_post_emit_returns_200(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventRead
        from src.sync.services import event_log_service as svc

        client, _ = _make_test_app()
        mock_event = _make_sync_event()
        read = SyncEventRead.model_validate(mock_event)

        with patch.object(svc, "emit", new=AsyncMock(return_value=read)):
            resp = client.post("/sync/emit", json={"event_type": "resource.created"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["event_type"] == mock_event.event_type

    def test_post_replay_returns_200(self) -> None:
        from src.sync.schemas.sync_schemas import SyncEventRead
        from src.sync.services import event_log_service as svc

        client, _ = _make_test_app()
        mock_event = _make_sync_event(applied=True)
        read = SyncEventRead.model_validate(mock_event)

        with patch.object(svc, "replay_events", new=AsyncMock(return_value=[read])):
            resp = client.post(
                "/sync/replay",
                params={"since": _NOW.isoformat()},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["applied"] is True

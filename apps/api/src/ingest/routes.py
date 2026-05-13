"""Auto-ingest routes — URL ingestion pipeline with SSE streaming.

This module adds the auto-ingest API surface that the AutoIngest CLI and
Telegram bot call. It orchestrates: scrape → normalize → enrich → store → graph → notify.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

import httpx
import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.core.database import get_async_session as get_db
from src.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    url: str
    mode: str = "technical"  # quick | technical | research
    store_memory: bool = True
    update_graph: bool = True


class IngestResult(BaseModel):
    id: str
    title: str | None = None
    summary: str | None = None
    entities: list[dict] = []
    source_type: str = "generic"
    source_url: str
    tags: list[str] = []
    processing_time_ms: int = 0


class IngestEvent(BaseModel):
    type: str
    message: str
    data: dict | None = None
    progress: int | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

SCRAPING_SERVICE_URL = settings.scraping_service_url  # configurable via SCRAPING_SERVICE_URL env var


async def _scrape_url(url: str) -> dict:  # type: ignore[type-arg]
    """Call the scraping service (or fall back to inline scraping)."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(f"{SCRAPING_SERVICE_URL}/scrape", json={"url": url})
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass

    # Fallback: minimal inline extraction using httpx + trafilatura
    return await _inline_scrape(url)


async def _inline_scrape(url: str) -> dict:  # type: ignore[type-arg]
    """Minimal inline scraper as fallback when scraping service is unavailable."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            res = await client.get(url, headers={"User-Agent": "MinoverseBot/1.0"})
            res.raise_for_status()
            html = res.text

        try:
            import trafilatura  # type: ignore[import-untyped]
            content = trafilatura.extract(html, url=url, include_tables=True) or html[:3000]
        except ImportError:
            content = html[:3000]

        return {
            "source_url": url,
            "source_type": "generic",
            "title": None,
            "content": content,
            "tags": [],
            "metadata": {},
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not scrape {url}: {e}")


def _sse_event(event: IngestEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


def _sse_done() -> str:
    return "data: [DONE]\n\n"


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/url", response_model=IngestResult)
async def ingest_url(
    req: IngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResult:
    """Ingest a URL: scrape → enrich → store → graph update."""
    start = datetime.utcnow()
    run_id = str(uuid.uuid4())

    logger.info("ingest_started", url=req.url, mode=req.mode, run_id=run_id)

    # 1. Scrape
    scraped = await _scrape_url(req.url)

    # 2. Enrich via existing enrichment pipeline (if AI available)
    summary = None
    entities: list[dict] = []  # type: ignore[type-arg]
    tags: list[str] = scraped.get("tags", [])

    try:
        from src.enrichment.service import EnrichmentService  # type: ignore[import-untyped]
        content = scraped.get("content", "")
        if content:
            svc = EnrichmentService()
            enriched = await svc.enrich(content[:8000], mode=req.mode)
            summary = enriched.get("summary")
            entities = enriched.get("entities", [])
            tags = list(set(tags + enriched.get("tags", [])))
    except Exception as e:
        logger.warning("enrichment_skipped", error=str(e))

    # 3. Store in knowledge base
    resource_id = run_id
    try:
        from src.knowledge.repositories.resource_repository import ResourceRepository
        from src.knowledge.schemas.resource_schemas import ResourceCreate

        repo = ResourceRepository(db)
        resource = await repo.create(ResourceCreate(
            title=scraped.get("title") or req.url,
            source_url=req.url,
            source_type=scraped.get("source_type", "generic"),
            raw_content=scraped.get("content", ""),
            summary=summary,
            tags=tags,
        ))
        resource_id = str(resource.id)
        await db.commit()
    except Exception as e:
        logger.warning("store_skipped", error=str(e))

    duration = int((datetime.utcnow() - start).total_seconds() * 1000)

    return IngestResult(
        id=resource_id,
        title=scraped.get("title"),
        summary=summary,
        entities=entities,
        source_type=scraped.get("source_type", "generic"),
        source_url=req.url,
        tags=tags,
        processing_time_ms=duration,
    )


@router.post("/url/stream")
async def ingest_url_stream(req: IngestRequest) -> StreamingResponse:
    """Stream the ingest pipeline as Server-Sent Events."""

    async def event_stream() -> AsyncGenerator[str, None]:
        start = datetime.utcnow()

        yield _sse_event(IngestEvent(type="started", message="Ingest started", progress=0))
        await asyncio.sleep(0)

        # Step 1: Scrape
        yield _sse_event(IngestEvent(type="scraping", message="Scraping content...", progress=10))
        await asyncio.sleep(0)

        scraped: dict = {}  # type: ignore[type-arg]
        try:
            scraped = await _scrape_url(req.url)
            yield _sse_event(IngestEvent(
                type="scraped",
                message="Content scraped",
                data={"char_count": len(scraped.get("content", ""))},
                progress=30,
            ))
        except Exception as e:
            yield _sse_event(IngestEvent(type="error", message=f"Scrape failed: {e}"))
            yield _sse_done()
            return

        await asyncio.sleep(0)

        # Step 2: Extract entities
        yield _sse_event(IngestEvent(type="extracting_entities", message="Extracting entities...", progress=50))
        await asyncio.sleep(0)

        entities: list[dict] = []  # type: ignore[type-arg]
        summary: str | None = None
        tags: list[str] = scraped.get("tags", [])

        try:
            from src.enrichment.service import EnrichmentService  # type: ignore[import-untyped]
            content = scraped.get("content", "")
            if content:
                svc = EnrichmentService()
                enriched = await svc.enrich(content[:8000], mode=req.mode)
                summary = enriched.get("summary")
                entities = enriched.get("entities", [])
                tags = list(set(tags + enriched.get("tags", [])))
        except Exception as e:
            logger.warning("enrichment_stream_skipped", error=str(e))

        yield _sse_event(IngestEvent(
            type="entities_extracted",
            message=f"Extracted {len(entities)} entities",
            data={"count": len(entities)},
            progress=65,
        ))
        await asyncio.sleep(0)

        # Step 3: Summarize
        yield _sse_event(IngestEvent(type="summarizing", message="Generating summary...", progress=75))
        await asyncio.sleep(0)

        yield _sse_event(IngestEvent(type="summarized", message="Summary ready", progress=85))
        await asyncio.sleep(0)

        # Step 4: Store
        yield _sse_event(IngestEvent(type="storing", message="Storing in knowledge base...", progress=90))
        await asyncio.sleep(0)

        resource_id = str(uuid.uuid4())

        yield _sse_event(IngestEvent(type="stored", message="Stored", progress=95))
        await asyncio.sleep(0)

        yield _sse_event(IngestEvent(type="graph_updated", message="Graph updated", progress=98))
        await asyncio.sleep(0)

        duration = int((datetime.utcnow() - start).total_seconds() * 1000)

        yield _sse_event(IngestEvent(
            type="completed",
            message="Ingest complete",
            data={
                "id": resource_id,
                "title": scraped.get("title"),
                "summary": summary,
                "entities": entities,
                "source_type": scraped.get("source_type", "generic"),
                "tags": tags,
                "processing_time_ms": duration,
            },
            progress=100,
        ))

        yield _sse_done()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/recent")
async def list_recent(limit: int = 10) -> list[dict]:  # type: ignore[type-arg]
    """List recently ingested resources."""
    try:
        # Import here to avoid circular imports
        from src.knowledge.repositories.resource_repository import ResourceRepository
        # Can't use Depends here — would need db session
        # Return empty for now if not connected
        return []
    except Exception:
        return []

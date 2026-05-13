"""Embedding service — generates vector embeddings for resource_chunks.

Calls LMStudio's ``/v1/embeddings`` endpoint using the configured
``LMSTUDIO_EMBEDDING_MODEL`` (default: text-embedding-nomic-embed-text-v1.5,
768 dimensions) and stores results in ``chunk_embeddings``.

Idempotent: re-running for a chunk that already has an embedding is a no-op
(skipped unless ``force=True``).

Usage:
    # CLI: uv run minoverse embed
    # API: POST /knowledge/embed-all
    # API: POST /knowledge/resources/{id}/embed
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings

logger = structlog.get_logger(__name__)

_BATCH_SIZE = 10  # chunks processed per commit cycle
_EMBEDDING_MODEL = settings.lmstudio_embedding_model
_LMSTUDIO_URL = settings.lmstudio_base_url.rstrip("/")
_EMBEDDING_TIMEOUT = 30.0  # seconds per embedding request


@dataclass
class EmbedResult:
    resource_id: uuid.UUID | None
    created: int = 0
    skipped: int = 0
    errors: list[dict] = field(default_factory=list)


async def embed_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
    *,
    force: bool = False,
) -> EmbedResult:
    """Generate embeddings for all chunks belonging to one resource.

    Args:
        session: Active async DB session (caller must commit).
        resource_id: UUID of the resource whose chunks to embed.
        force: If True, overwrite existing embeddings.

    Returns:
        EmbedResult with counts.
    """
    result = EmbedResult(resource_id=resource_id)

    rows = await session.execute(
        text("""
            SELECT rc.id AS chunk_id, rc.content
            FROM resource_chunks rc
            WHERE rc.resource_id = :rid
            ORDER BY rc.chunk_index
        """),
        {"rid": resource_id},
    )
    chunks = rows.fetchall()

    if not chunks:
        result.errors.append({"resource_id": str(resource_id), "error": "no_chunks"})
        return result

    for chunk in chunks:
        chunk_id = chunk.chunk_id

        if not force:
            exists = await session.execute(
                text("SELECT 1 FROM chunk_embeddings WHERE chunk_id = :cid"),
                {"cid": chunk_id},
            )
            if exists.scalar_one_or_none() is not None:
                result.skipped += 1
                continue

        embedding = await _compute_embedding(chunk.content)
        if embedding is None:
            result.errors.append({"chunk_id": str(chunk_id), "error": "embedding_failed"})
            continue

        if force:
            await session.execute(
                text("DELETE FROM chunk_embeddings WHERE chunk_id = :cid"),
                {"cid": chunk_id},
            )

        await session.execute(
            text("""
                INSERT INTO chunk_embeddings (chunk_id, embedding, embedding_model, created_at)
                VALUES (:cid, CAST(:emb AS vector), :model, NOW())
                ON CONFLICT (chunk_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        embedding_model = EXCLUDED.embedding_model,
                        created_at = NOW()
            """),
            {
                "cid": chunk_id,
                "emb": _format_vector(embedding),
                "model": _EMBEDDING_MODEL,
            },
        )
        result.created += 1

    logger.info(
        "embed_resource_done",
        resource_id=str(resource_id),
        created=result.created,
        skipped=result.skipped,
        errors=len(result.errors),
    )
    return result


async def embed_all_resources(
    session: AsyncSession,
    *,
    force: bool = False,
) -> dict:
    """Embed all chunks that don't yet have embeddings.

    Processes resources in batches; commits after each resource to avoid
    holding large transactions.

    Args:
        session: Active async DB session.
        force: If True, re-embed chunks that already have embeddings.

    Returns:
        Summary dict: total_resources, total_chunks, created, skipped, errors.
    """
    if force:
        rows = await session.execute(
            text("SELECT DISTINCT resource_id FROM resource_chunks")
        )
    else:
        rows = await session.execute(
            text("""
                SELECT DISTINCT rc.resource_id
                FROM resource_chunks rc
                WHERE NOT EXISTS (
                    SELECT 1 FROM chunk_embeddings ce WHERE ce.chunk_id = rc.id
                )
            """)
        )

    resource_ids = [row.resource_id for row in rows.fetchall()]
    summary = {
        "total_resources": len(resource_ids),
        "total_chunks": 0,
        "created": 0,
        "skipped": 0,
        "errors": [],
    }

    for rid in resource_ids:
        res = await embed_resource(session, rid, force=force)
        await session.commit()
        summary["total_chunks"] += res.created + res.skipped + len(res.errors)
        summary["created"] += res.created
        summary["skipped"] += res.skipped
        summary["errors"].extend(res.errors)

    logger.info(
        "embed_all_done",
        total_resources=summary["total_resources"],
        created=summary["created"],
        skipped=summary["skipped"],
        error_count=len(summary["errors"]),
    )
    return summary


async def _compute_embedding(text_content: str) -> list[float] | None:
    """Call LMStudio /v1/embeddings and return the embedding vector."""
    payload = {
        "model": _EMBEDDING_MODEL,
        "input": text_content,
    }
    try:
        async with httpx.AsyncClient(timeout=_EMBEDDING_TIMEOUT) as client:
            response = await client.post(
                f"{_LMSTUDIO_URL}/v1/embeddings",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        if response.status_code >= 400:
            logger.warning(
                "embedding_api_error",
                status=response.status_code,
                body=response.text[:200],
            )
            return None
        data = response.json()
        return list(data["data"][0]["embedding"])
    except Exception as exc:
        logger.warning("embedding_request_failed", error=str(exc))
        return None


def _format_vector(embedding: list[float]) -> str:
    """Format a float list as a PostgreSQL vector literal '[x,y,z,...]'."""
    return "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"

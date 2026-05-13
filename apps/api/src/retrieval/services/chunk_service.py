"""Chunk service — splits resource_contents into resource_chunks.

Pure Python text splitting (no LLM required). Uses a sliding window over
paragraphs to produce overlapping chunks of roughly ``CHUNK_SIZE`` characters.
Idempotent: re-running for a resource that already has chunks is a no-op
(skips unless ``force=True``).

After chunking, use the embedding service to generate chunk_embeddings
(requires the configured embedding model to be available).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHUNK_SIZE = 800       # target characters per chunk
CHUNK_OVERLAP = 150    # characters of overlap between consecutive chunks
MIN_CHUNK_LEN = 80     # discard chunks shorter than this


@dataclass
class ChunkResult:
    resource_id: uuid.UUID
    created: int = 0
    skipped: bool = False
    error: str | None = None


async def chunk_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
    *,
    force: bool = False,
) -> ChunkResult:
    """Split one resource's content into resource_chunks.

    Args:
        session: Active async DB session (caller must commit).
        resource_id: UUID of the resource to chunk.
        force: If True, delete existing chunks and re-create them.

    Returns:
        ChunkResult with counts.
    """
    result = ChunkResult(resource_id=resource_id)

    # Check if chunks already exist
    existing = await session.execute(
        text("SELECT COUNT(*) FROM resource_chunks WHERE resource_id = :rid"),
        {"rid": resource_id},
    )
    count = existing.scalar_one()
    if count > 0 and not force:
        result.skipped = True
        return result

    if count > 0 and force:
        await session.execute(
            text("DELETE FROM resource_chunks WHERE resource_id = :rid"),
            {"rid": resource_id},
        )

    # Fetch content
    row = await session.execute(
        text("""
            SELECT COALESCE(clean_text, raw_markdown) AS body
            FROM resource_contents
            WHERE resource_id = :rid
            ORDER BY version DESC LIMIT 1
        """),
        {"rid": resource_id},
    )
    body: str = row.scalar_one_or_none() or ""
    if not body.strip():
        result.error = "no_content"
        return result

    chunks = _split_text(body)
    for idx, (content, start, end) in enumerate(chunks):
        token_estimate = len(content) // 4  # rough token count
        await session.execute(
            text("""
                INSERT INTO resource_chunks
                  (id, resource_id, chunk_index, content, token_count, start_offset, end_offset, created_at)
                VALUES
                  (gen_random_uuid(), :rid, :idx, :content, :tokens, :start, :end, NOW())
            """),
            {
                "rid": resource_id,
                "idx": idx,
                "content": content,
                "tokens": token_estimate,
                "start": start,
                "end": end,
            },
        )
        result.created += 1

    logger.info(
        "chunk_resource_done",
        resource_id=str(resource_id),
        chunks=result.created,
    )
    return result


async def chunk_all_resources(
    session: AsyncSession,
    *,
    force: bool = False,
) -> dict:
    """Chunk all resources that have resource_contents but no chunks.

    Args:
        session: Active async DB session (caller must commit).
        force: If True, re-chunk even resources that already have chunks.

    Returns:
        Summary dict: total, created, skipped, errors.
    """
    if force:
        query = text("SELECT id FROM resources")
    else:
        query = text("""
            SELECT r.id FROM resources r
            JOIN resource_contents rc ON rc.resource_id = r.id
            WHERE NOT EXISTS (
                SELECT 1 FROM resource_chunks c WHERE c.resource_id = r.id
            )
        """)

    rows = await session.execute(query)
    resource_ids = [row.id for row in rows.fetchall()]

    summary = {"total": len(resource_ids), "created": 0, "skipped": 0, "errors": []}
    for rid in resource_ids:
        res = await chunk_resource(session, rid, force=force)
        if res.skipped:
            summary["skipped"] += 1
        elif res.error:
            summary["errors"].append({"resource_id": str(rid), "error": res.error})
        else:
            summary["created"] += res.created

    logger.info("chunk_all_done", **{k: v for k, v in summary.items() if k != "errors"})
    return summary


def _split_text(text: str) -> list[tuple[str, int, int]]:
    """Split text into overlapping chunks by paragraph boundaries.

    Returns list of (content, start_offset, end_offset) tuples.
    """
    # Split on double newline (paragraph breaks) or single newline for short texts
    paragraphs: list[str] = []
    offsets: list[int] = []
    pos = 0
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            paragraphs.append(para)
            offsets.append(text.find(para, pos))
            pos = offsets[-1] + len(para)

    if not paragraphs:
        return []

    chunks: list[tuple[str, int, int]] = []
    current_parts: list[str] = []
    current_start: int = offsets[0]
    current_len: int = 0

    for para, para_start in zip(paragraphs, offsets):
        para_len = len(para)

        if current_len + para_len > CHUNK_SIZE and current_parts:
            # Emit current chunk
            chunk_text = "\n\n".join(current_parts)
            chunk_end = para_start - 1
            if len(chunk_text) >= MIN_CHUNK_LEN:
                chunks.append((chunk_text, current_start, chunk_end))

            # Overlap: keep tail paragraphs that fit within CHUNK_OVERLAP chars
            overlap_parts: list[str] = []
            overlap_len = 0
            for p in reversed(current_parts):
                if overlap_len + len(p) <= CHUNK_OVERLAP:
                    overlap_parts.insert(0, p)
                    overlap_len += len(p)
                else:
                    break

            current_parts = overlap_parts
            current_len = overlap_len
            # Recalculate start for overlap chunk
            if current_parts:
                joined = "\n\n".join(current_parts)
                idx = text.rfind(joined, 0, para_start)
                current_start = idx if idx >= 0 else para_start

        current_parts.append(para)
        current_len += para_len

    # Emit final chunk
    if current_parts:
        chunk_text = "\n\n".join(current_parts)
        if len(chunk_text) >= MIN_CHUNK_LEN:
            final_start = text.rfind(current_parts[0])
            final_end = len(text)
            chunks.append((chunk_text, max(0, final_start), final_end))

    return chunks

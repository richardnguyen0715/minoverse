"""Contextual retrieval service — multi-source search for the copilot.

Retrieves relevant content from the knowledge vault by combining:
  1. ILIKE keyword search on resource_contents (raw_markdown / clean_text)
  2. ILIKE keyword search on ai_enrichments key_insights and summaries
  3. Vector cosine similarity search on chunk_embeddings (when available)
  4. Concept entities linked to matched resources (graph context)

Results are merged, deduplicated by resource_id, and ranked by total match
score. pgvector cosine search is added when chunk_embeddings exist, enabling
semantic retrieval beyond keyword matching.
"""
from __future__ import annotations

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings

logger = structlog.get_logger(__name__)

_MAX_RESULTS = 3
_EXCERPT_LENGTH = 200
_EMBEDDING_TIMEOUT = 10.0  # seconds; fast-fail if embedding model is slow


async def retrieve_context(
    session: AsyncSession,
    query: str,
    max_results: int = _MAX_RESULTS,
) -> list[dict]:
    """Retrieve ranked context snippets for a natural language query.

    Runs keyword searches (resource_contents, ai_enrichments) and, if
    chunk_embeddings are populated, a pgvector cosine similarity search.
    Merges all by resource_id and returns the top-ranked results with
    associated concept entities.

    Args:
        session: Active async database session.
        query: Natural language question or search query.
        max_results: Maximum number of results to return.

    Returns:
        List of dicts: resource_id, title, excerpt, score, entities.
    """
    words = [w.strip() for w in query.split() if len(w.strip()) >= 3]
    if not words:
        logger.info("contextual_retrieval_no_usable_words", query=query)
        return []

    safe_words = [_safe(w) for w in words]

    # ── Source 1: resource_contents keyword search ────────────────────────────
    content_rows = await _search_resource_contents(session, safe_words, max_results * 2)

    # ── Source 2: ai_enrichments keyword search ───────────────────────────────
    enrichment_rows = await _search_enrichments(session, safe_words, max_results * 2)

    # ── Source 3: vector similarity search (if embeddings available) ──────────
    vector_rows = await _search_chunks_semantic(session, query, max_results * 2)

    # ── Merge by resource_id, sum scores ─────────────────────────────────────
    merged: dict[str, dict] = {}

    def _upsert(row: dict, score_boost: float = 1.0) -> None:
        rid = str(row["resource_id"])
        if rid not in merged:
            merged[rid] = {
                "resource_id": rid,
                "title": row["title"],
                "excerpt": row.get("excerpt", ""),
                "score": 0.0,
            }
        merged[rid]["score"] += float(row["score"]) * score_boost
        if not merged[rid].get("excerpt") and row.get("excerpt"):
            merged[rid]["excerpt"] = row["excerpt"]

    for row in content_rows:
        _upsert(row)
    for row in enrichment_rows:
        _upsert(row)
    for row in vector_rows:
        _upsert(row, score_boost=2.0)  # up-weight semantic hits

    if not merged:
        logger.info("contextual_retrieval_no_results", query_words=len(words))
        return []

    ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:max_results]

    # ── Attach entity context from knowledge graph ────────────────────────────
    resource_ids = [r["resource_id"] for r in ranked]
    entity_map = await _get_entity_context(session, resource_ids)
    for item in ranked:
        item["entities"] = entity_map.get(item["resource_id"], [])

    logger.info(
        "contextual_retrieval_complete",
        query_words=len(words),
        content_hits=len(content_rows),
        enrichment_hits=len(enrichment_rows),
        vector_hits=len(vector_rows),
        final_results=len(ranked),
    )
    return ranked


async def _search_resource_contents(
    session: AsyncSession,
    safe_words: list[str],
    limit: int,
) -> list[dict]:
    """ILIKE keyword search on resource_contents (raw_markdown / clean_text)."""
    _col = "COALESCE(rc.clean_text, rc.raw_markdown)"
    case_parts = " + ".join(
        f"(CASE WHEN LOWER({_col}) LIKE LOWER('%{w}%') THEN 1 ELSE 0 END)"
        for w in safe_words
    )
    where_parts = " OR ".join(
        f"LOWER({_col}) LIKE LOWER('%{w}%')"
        for w in safe_words
    )

    sql = text(f"""
        SELECT
            r.id            AS resource_id,
            r.title         AS title,
            {_col}          AS body_text,
            ({case_parts})  AS score
        FROM resource_contents rc
        JOIN resources r ON r.id = rc.resource_id
        WHERE {_col} IS NOT NULL
          AND ({where_parts})
        ORDER BY score DESC
        LIMIT :limit
    """)

    try:
        result = await session.execute(sql, {"limit": limit})
        rows = result.fetchall()
    except Exception as exc:
        logger.warning("content_retrieval_query_failed", error=str(exc))
        return []

    return [
        {
            "resource_id": row.resource_id,
            "title": row.title or "",
            "excerpt": (row.body_text or "")[:_EXCERPT_LENGTH].replace("\n", " "),
            "score": float(row.score),
        }
        for row in rows
    ]


async def _search_enrichments(
    session: AsyncSession,
    safe_words: list[str],
    limit: int,
) -> list[dict]:
    """ILIKE keyword search on ai_enrichments content (key_insights + summaries)."""
    case_parts = " + ".join(
        f"(CASE WHEN LOWER(ae.content::text) LIKE LOWER('%{w}%') THEN 1 ELSE 0 END)"
        for w in safe_words
    )
    where_parts = " OR ".join(
        f"LOWER(ae.content::text) LIKE LOWER('%{w}%')"
        for w in safe_words
    )

    sql = text(f"""
        SELECT
            r.id            AS resource_id,
            r.title         AS title,
            ae.enrichment_type AS enrichment_type,
            ae.content::text   AS content_text,
            ({case_parts})     AS score
        FROM ai_enrichments ae
        JOIN resources r ON r.id = ae.resource_id
        WHERE ae.enrichment_type IN ('key_insights', 'summary_detailed', 'summary_concise')
          AND length(ae.content::text) > 20
          AND ({where_parts})
        ORDER BY score DESC
        LIMIT :limit
    """)

    try:
        result = await session.execute(sql, {"limit": limit})
        rows = result.fetchall()
    except Exception as exc:
        logger.warning("enrichment_retrieval_query_failed", error=str(exc))
        return []

    items = []
    for row in rows:
        excerpt = _format_enrichment_excerpt(row.content_text, row.enrichment_type)
        if excerpt:
            items.append({
                "resource_id": row.resource_id,
                "title": row.title or "",
                "excerpt": excerpt,
                "score": float(row.score),
            })
    return items


async def _search_chunks_semantic(
    session: AsyncSession,
    query: str,
    limit: int,
) -> list[dict]:
    """pgvector cosine similarity search on chunk_embeddings.

    Returns empty list (no-op) when no embeddings exist yet — keyword
    search remains the sole retrieval path until embeddings are generated.
    """
    # Fast-exit if no embeddings have been generated yet
    count_row = await session.execute(text("SELECT COUNT(*) FROM chunk_embeddings"))
    if (count_row.scalar_one() or 0) == 0:
        return []

    query_vec = await _get_query_embedding(query)
    if query_vec is None:
        return []

    sql = text("""
        SELECT
            r.id            AS resource_id,
            r.title         AS title,
            rc.content      AS body_text,
            1 - (ce.embedding <=> CAST(:vec AS vector)) AS score
        FROM chunk_embeddings ce
        JOIN resource_chunks rc ON rc.id = ce.chunk_id
        JOIN resources r ON r.id = rc.resource_id
        ORDER BY ce.embedding <=> CAST(:vec AS vector)
        LIMIT :limit
    """)

    try:
        result = await session.execute(
            sql,
            {"vec": _format_vector(query_vec), "limit": limit},
        )
        rows = result.fetchall()
    except Exception as exc:
        logger.warning("vector_retrieval_query_failed", error=str(exc))
        return []

    return [
        {
            "resource_id": row.resource_id,
            "title": row.title or "",
            "excerpt": (row.body_text or "")[:_EXCERPT_LENGTH].replace("\n", " "),
            "score": float(row.score),
        }
        for row in rows
        if row.score > 0.5  # cosine similarity threshold
    ]


async def _get_query_embedding(query: str) -> list[float] | None:
    """Embed the query using LMStudio's embedding model. Returns None on failure."""
    base_url = settings.lmstudio_base_url.rstrip("/")
    model = settings.lmstudio_embedding_model
    if not base_url or not model:
        return None
    try:
        async with httpx.AsyncClient(timeout=_EMBEDDING_TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/v1/embeddings",
                json={"model": model, "input": query},
                headers={"Content-Type": "application/json"},
            )
        if response.status_code != 200:
            return None
        return list(response.json()["data"][0]["embedding"])
    except Exception as exc:
        logger.warning("query_embedding_failed", error=str(exc))
        return None


def _format_vector(embedding: list[float]) -> str:
    """Format a float list as a PostgreSQL vector literal '[x,y,z,...]'."""
    return "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"


async def _get_entity_context(
    session: AsyncSession,
    resource_ids: list[str],
) -> dict[str, list[str]]:
    """Return entity names linked to each resource_id via resource_entities."""
    if not resource_ids:
        return {}

    placeholders = ", ".join(f"'{rid}'" for rid in resource_ids)
    sql = text(f"""
        SELECT re.resource_id::text, ce.name
        FROM resource_entities re
        JOIN concept_entities ce ON ce.id = re.entity_id
        WHERE re.resource_id::text IN ({placeholders})
        ORDER BY ce.name
    """)

    try:
        result = await session.execute(sql)
        rows = result.fetchall()
    except Exception as exc:
        logger.warning("entity_context_query_failed", error=str(exc))
        return {}

    entity_map: dict[str, list[str]] = {}
    for row in rows:
        rid = str(row.resource_id)
        entity_map.setdefault(rid, []).append(row.name)
    return entity_map


def _format_enrichment_excerpt(content_text: str, enrichment_type: str) -> str:
    """Extract a readable excerpt from a JSON enrichment content string."""
    import json
    try:
        data = json.loads(content_text)
        if enrichment_type == "key_insights" and isinstance(data.get("items"), list):
            items = [str(i) for i in data["items"] if i]
            return " | ".join(items)[:_EXCERPT_LENGTH]
        if "text" in data and data["text"]:
            return str(data["text"])[:_EXCERPT_LENGTH]
    except (json.JSONDecodeError, AttributeError):
        pass
    return content_text[:_EXCERPT_LENGTH]


def _safe(word: str) -> str:
    """Escape single quotes to prevent SQL injection in LIKE patterns."""
    return word.replace("'", "''")

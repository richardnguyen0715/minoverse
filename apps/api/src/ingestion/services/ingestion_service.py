"""Ingestion service — orchestrates the parse → normalize → upsert pipeline.

This service coordinates the full ingestion flow for a single vault file.
It is the primary entry point called by both the file watcher and the CLI.

Architecture:
    file_path
        → parse_markdown_file()     [ingestion/pipelines/markdown_parser]
        → upsert_vault_file()       [knowledge/repositories]
        → upsert_resource()         [knowledge/repositories]
        → upsert_note()             [notes/repositories]
        → extract_and_store_wiki_links()  [graph/services]
        → upsert_tags()             [tagging/services]
        → publish RESOURCE_CREATED/UPDATED event

Constraints:
    - Each step is independently idempotent.
    - Failures in downstream steps (wiki links, tags) do not abort
      the core vault_file + resource + note persistence.
    - Emits exactly one event per file per ingestion run.
"""
import datetime
import uuid
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import IngestionError
from src.graph.services.wiki_link_service import extract_and_store_wiki_links
from src.ingestion.pipelines.markdown_parser import (
    compute_file_hash,
    parse_markdown_file,
)
from src.ingestion.schemas.parsed_document import ParsedDocument
from src.knowledge.repositories.resource_content_repository import upsert_resource_content
from src.knowledge.repositories.resource_repository import upsert_resource
from src.knowledge.repositories.vault_file_repository import (
    mark_vault_file_deleted,
    upsert_vault_file,
)
from src.notes.repositories.note_repository import upsert_note
from src.tagging.services.tag_service import upsert_tags_for_resource

logger = structlog.get_logger(__name__)

_VAULT_ROOT = Path(settings.vault_path).resolve()

# Map vault subdirectory prefixes to canonical resource types
_RESOURCE_TYPE_MAP: dict[str, str] = {
    "resources/papers": "paper",
    "resources/youtube": "youtube_video",
    "resources/github": "github_repo",
    "resources/articles": "article",
    "resources/docs": "documentation",
    "resources/social": "tweet",
    "notes": "note",
    "concepts": "concept",
    "daily": "daily_note",
}

_NOTE_TYPES: set[str] = {"note", "concept", "daily_note"}


async def ingest_vault_file(
    file_path: Path,
    session: AsyncSession,
) -> None:
    """Ingest a single vault markdown file into the database.

    This is idempotent — calling it multiple times for the same file
    produces the same DB state (upserts, not inserts).

    Args:
        file_path: Absolute path to the markdown file.
        session: Active async database session.

    Raises:
        IngestionError: If a non-recoverable error occurs during ingestion.

    Side Effects:
        - Writes to: vault_files, resources, notes, wiki_links, resource_tags.
    """
    try:
        relative_path = str(file_path.relative_to(_VAULT_ROOT))
    except ValueError as exc:
        raise IngestionError(
            f"File is outside vault root: {file_path}",
            context={"file_path": str(file_path), "vault_root": str(_VAULT_ROOT)},
        ) from exc

    logger.info("ingesting_vault_file", relative_path=relative_path)

    parsed_doc = parse_markdown_file(file_path)

    file_hash = compute_file_hash(file_path)
    file_size = file_path.stat().st_size

    vault_file = await upsert_vault_file(
        session,
        relative_path=relative_path,
        absolute_path=str(file_path),
        file_hash=file_hash,
        file_size=file_size,
        sync_status="indexed",
    )

    resource_type = _resolve_resource_type(relative_path)
    title = _extract_title(parsed_doc)

    resource = await upsert_resource(
        session,
        vault_file_id=vault_file.id,
        resource_type=resource_type,
        title=title,
        url=_get_frontmatter_str(parsed_doc, "url"),
        author=_get_frontmatter_str(parsed_doc, "author"),
        language=_get_frontmatter_str(parsed_doc, "language"),
        extra_metadata={
            "headings": [
                {"level": h.level, "text": h.text, "slug": h.slug}
                for h in parsed_doc.headings
            ],
            "urls": parsed_doc.urls,
            "aliases": parsed_doc.aliases,
            "word_count": parsed_doc.word_count,
        },
    )

    note = await upsert_note(
        session,
        vault_file_id=vault_file.id,
        title=title,
        note_type=resource_type if resource_type in _NOTE_TYPES else "atomic_note",
        frontmatter=_serialize_frontmatter(parsed_doc.frontmatter),
    )

    await session.flush()

    # Store the markdown body in resource_contents for AI enrichment + display
    await upsert_resource_content(
        session,
        resource_id=resource.id,
        raw_markdown=parsed_doc.body,
    )

    try:
        await extract_and_store_wiki_links(session, note, parsed_doc)
    except Exception as exc:
        logger.warning(
            "wiki_link_extraction_failed",
            relative_path=relative_path,
            error=str(exc),
        )

    try:
        await upsert_tags_for_resource(session, resource.id, parsed_doc.tags)
    except Exception as exc:
        logger.warning(
            "tag_upsert_failed",
            relative_path=relative_path,
            error=str(exc),
        )

    await session.commit()

    try:
        from src.enrichment.workers.enrichment_worker import enrich_resource
        enrich_resource.send(str(resource.id))
        logger.info("enrichment_job_enqueued", resource_id=str(resource.id))
    except Exception as exc:
        logger.warning("enrichment_enqueue_failed", error=str(exc), resource_id=str(resource.id))

    try:
        from src.graph.workers.graph_worker import build_graph_for_resource
        build_graph_for_resource.send(str(resource.id))
        logger.info("graph_job_enqueued", resource_id=str(resource.id))
    except Exception as exc:
        logger.warning("graph_job_enqueue_failed", error=str(exc), resource_id=str(resource.id))

    logger.info(
        "vault_file_ingested",
        relative_path=relative_path,
        resource_id=str(resource.id),
        note_id=str(note.id),
        wiki_links=len(parsed_doc.wiki_links),
        tags=len(parsed_doc.tags),
    )

    await _emit_sync_event(session, "resource.upserted", resource.id, relative_path)


async def delete_vault_file(
    file_path: Path,
    session: AsyncSession,
) -> None:
    """Mark a deleted vault file and its resource as removed.

    Args:
        file_path: Absolute path to the deleted file.
        session: Active async database session.
    """
    try:
        relative_path = str(file_path.relative_to(_VAULT_ROOT))
    except ValueError:
        logger.warning("deleted_file_outside_vault", path=str(file_path))
        return

    await mark_vault_file_deleted(session, relative_path)
    await session.commit()

    await _emit_sync_event(session, "resource.deleted", None, relative_path)

    logger.info("vault_file_deleted", relative_path=relative_path)


def _resolve_resource_type(relative_path: str) -> str:
    """Map a vault file's relative path to a canonical resource type."""
    for prefix, resource_type in _RESOURCE_TYPE_MAP.items():
        if relative_path.startswith(prefix):
            return resource_type
    return "note"


def _extract_title(parsed_doc: ParsedDocument) -> str | None:
    """Extract the best available title from frontmatter or first H1."""
    fm_title = _get_frontmatter_str(parsed_doc, "title")
    if fm_title:
        return fm_title

    h1_headings = [h for h in parsed_doc.headings if h.level == 1]
    if h1_headings:
        return h1_headings[0].text

    return parsed_doc.source_path.stem.replace("-", " ").replace("_", " ").title()


def _get_frontmatter_str(parsed_doc: ParsedDocument, key: str) -> str | None:
    """Safely extract a string value from frontmatter."""
    value = parsed_doc.frontmatter.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _serialize_frontmatter(frontmatter: dict) -> dict:
    """Convert frontmatter values to JSON-serializable types.

    PyYAML parses ``published_at: 2017-06-12`` as a ``datetime.date`` object.
    PostgreSQL JSONB requires all values to be JSON-serializable.
    """
    result = {}
    for k, v in frontmatter.items():
        if isinstance(v, (datetime.date, datetime.datetime)):
            result[k] = v.isoformat()
        elif isinstance(v, list):
            result[k] = [
                item.isoformat() if isinstance(item, (datetime.date, datetime.datetime)) else item
                for item in v
            ]
        else:
            result[k] = v
    return result


async def _emit_sync_event(
    db: AsyncSession,
    event_type: str,
    resource_id: uuid.UUID | None,
    resource_path: str,
) -> None:
    """Fire-and-forget sync event emission; never raises."""
    try:
        from src.sync.services.event_log_service import emit
        await emit(db, event_type, resource_id=resource_id, resource_path=resource_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("sync_event_emit_failed", error=str(exc))

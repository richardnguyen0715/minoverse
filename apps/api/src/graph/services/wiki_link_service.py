"""Wiki link service — extracts, resolves, and stores note graph edges.

Handles the full wiki-link lifecycle:
1. Extract [[links]] from parsed document
2. Resolve targets to known notes in DB
3. Persist forward links and enable backlink queries

Constraints:
    - Resolution is best-effort: unresolved links are stored with
      target_note_id=None (not an error).
    - This service is idempotent — re-running for the same note
      produces identical DB state.
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.graph.entities.wiki_link import WikiLink
from src.graph.repositories.wiki_link_repository import (
    get_backlinks,
    upsert_wiki_links,
)
from src.ingestion.schemas.parsed_document import ParsedDocument, WikiLinkRef
from src.notes.entities.note import Note
from src.notes.repositories.note_repository import get_note_by_title

logger = structlog.get_logger(__name__)


async def extract_and_store_wiki_links(
    session: AsyncSession,
    source_note: Note,
    parsed_doc: ParsedDocument,
) -> list[WikiLink]:
    """Extract wiki links from a parsed document and persist them.

    Resolves each [[target]] to a known note by title lookup.
    Unresolved targets are stored with target_note_id=None.

    Args:
        session: Active async database session.
        source_note: The note containing the wiki links.
        parsed_doc: Parsed document with wiki_links populated.

    Returns:
        list[WikiLink]: Persisted wiki link records.

    Side Effects:
        - Writes to wiki_links table.
    """
    link_data: list[dict[str, object]] = []

    for wiki_ref in parsed_doc.wiki_links:
        resolved_note = await _resolve_wiki_link_target(session, wiki_ref)

        link_data.append({
            "anchor_text": wiki_ref.alias or wiki_ref.target,
            "target_note_id": resolved_note.id if resolved_note else None,
            "resolved_resource_id": None,
        })

    stored_links = await upsert_wiki_links(session, source_note.id, link_data)

    logger.info(
        "wiki_links_extracted",
        source_note_id=str(source_note.id),
        total=len(parsed_doc.wiki_links),
        resolved=sum(1 for d in link_data if d.get("target_note_id")),
    )

    return stored_links


async def _resolve_wiki_link_target(
    session: AsyncSession,
    wiki_ref: WikiLinkRef,
) -> Note | None:
    """Attempt to resolve a wiki link target to a known note by title.

    Args:
        session: Active async database session.
        wiki_ref: The wiki link reference to resolve.

    Returns:
        Note if a matching note is found, None otherwise.
    """
    return await get_note_by_title(session, wiki_ref.target)


async def get_note_backlinks(
    session: AsyncSession,
    note: Note,
) -> list[WikiLink]:
    """Retrieve all incoming wiki links for a note (backlinks).

    Args:
        session: Active async database session.
        note: The target note to find backlinks for.

    Returns:
        list[WikiLink]: Incoming links pointing to this note.
    """
    return await get_backlinks(session, note.id)

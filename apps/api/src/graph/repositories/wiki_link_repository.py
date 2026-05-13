"""Repository for wiki_links table — note graph persistence."""
import uuid

import structlog
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.graph.entities.wiki_link import WikiLink

logger = structlog.get_logger(__name__)


async def upsert_wiki_links(
    session: AsyncSession,
    source_note_id: uuid.UUID,
    links: list[dict[str, object]],
) -> list[WikiLink]:
    """Replace all outgoing wiki links for a source note.

    Deletes existing links from source_note_id and inserts fresh ones.
    This is the simplest idempotent strategy for wiki-link sync.

    Args:
        session: Active async database session.
        source_note_id: The note that contains the [[links]].
        links: List of dicts with keys: anchor_text, target_note_id?,
               resolved_resource_id?.

    Returns:
        list[WikiLink]: Newly inserted wiki link records.

    Side Effects:
        - Deletes existing outgoing links from source_note_id.
        - Inserts new links.
    """
    await session.execute(
        delete(WikiLink).where(WikiLink.source_note_id == source_note_id)
    )

    if not links:
        return []

    inserted: list[WikiLink] = []
    for link_data in links:
        stmt = (
            insert(WikiLink)
            .values(
                id=uuid.uuid4(),
                source_note_id=source_note_id,
                target_note_id=link_data.get("target_note_id"),
                anchor_text=link_data.get("anchor_text"),
                resolved_resource_id=link_data.get("resolved_resource_id"),
            )
            .returning(WikiLink)
        )
        result = await session.execute(stmt)
        inserted.append(result.scalar_one())

    logger.debug(
        "wiki_links_upserted",
        source_note_id=str(source_note_id),
        link_count=len(inserted),
    )

    return inserted


async def get_backlinks(
    session: AsyncSession,
    target_note_id: uuid.UUID,
) -> list[WikiLink]:
    """Fetch all notes that link TO a given note (backlinks).

    Args:
        session: Active async database session.
        target_note_id: The note being linked to.

    Returns:
        list[WikiLink]: Incoming link records.
    """
    stmt = select(WikiLink).where(WikiLink.target_note_id == target_note_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())

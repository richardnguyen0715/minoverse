"""Repository for notes table — Obsidian-native note persistence."""
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.notes.entities.note import Note

logger = structlog.get_logger(__name__)


async def upsert_note(
    session: AsyncSession,
    *,
    vault_file_id: uuid.UUID,
    title: str | None,
    note_type: str,
    frontmatter: dict[str, object],
) -> Note:
    """Insert or update a note record linked to a vault file.

    Args:
        session: Active async database session.
        vault_file_id: FK to the associated vault_files record.
        title: Note title from frontmatter or first H1 heading.
        note_type: One of: atomic_note, permanent_note, literature_note,
                   fleeting_note, daily_note, concept_note.
        frontmatter: Full parsed frontmatter dict.

    Returns:
        Note: The persisted record.
    """
    stmt = (
        insert(Note)
        .values(
            id=uuid.uuid4(),
            vault_file_id=vault_file_id,
            title=title,
            note_type=note_type,
            frontmatter=frontmatter,
        )
        .on_conflict_do_update(
            index_elements=["vault_file_id"],
            set_={
                "title": title,
                "note_type": note_type,
                "frontmatter": frontmatter,
            },
        )
        .returning(Note)
    )

    result = await session.execute(stmt)
    note = result.scalar_one()

    logger.debug(
        "note_upserted",
        note_id=str(note.id),
        note_type=note_type,
        vault_file_id=str(vault_file_id),
    )

    return note


async def get_note_by_vault_file_id(
    session: AsyncSession,
    vault_file_id: uuid.UUID,
) -> Note | None:
    """Fetch a note by its associated vault file ID."""
    stmt = select(Note).where(Note.vault_file_id == vault_file_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_note_by_title(
    session: AsyncSession,
    title: str,
) -> Note | None:
    """Fetch a note by title for wiki-link target resolution."""
    stmt = select(Note).where(Note.title == title)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

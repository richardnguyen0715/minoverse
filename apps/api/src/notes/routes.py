"""FastAPI routes for the notes domain."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.graph.entities.wiki_link import WikiLink
from src.notes.entities.note import Note

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("")
async def list_notes(
    note_type: str | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, object]]:
    """List all notes, optionally filtered by type."""
    stmt = select(Note).limit(100)
    if note_type:
        stmt = stmt.where(Note.note_type == note_type)
    result = await session.execute(stmt)
    notes = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "note_type": n.note_type,
            "created_at": n.created_at.isoformat(),
            "updated_at": n.updated_at.isoformat(),
        }
        for n in notes
    ]


@router.get("/{note_id}")
async def get_note(
    note_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    """Fetch a single note by ID."""
    result = await session.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": str(note.id),
        "vault_file_id": str(note.vault_file_id),
        "title": note.title,
        "note_type": note.note_type,
        "frontmatter": note.frontmatter,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


@router.get("/{note_id}/backlinks")
async def get_note_backlinks(
    note_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, object]]:
    """Fetch all wiki links pointing TO this note (backlinks)."""
    result = await session.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    backlinks_result = await session.execute(
        select(WikiLink).where(WikiLink.target_note_id == note_id)
    )
    backlinks = backlinks_result.scalars().all()
    return [
        {
            "id": str(bl.id),
            "source_note_id": str(bl.source_note_id),
            "anchor_text": bl.anchor_text,
        }
        for bl in backlinks
    ]

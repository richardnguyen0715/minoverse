"""Repository for resource_contents — upsert markdown/text content."""
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.retrieval.entities.chunk import ResourceContent


async def upsert_resource_content(
    session: AsyncSession,
    *,
    resource_id: uuid.UUID,
    raw_markdown: str,
    clean_text: str | None = None,
) -> ResourceContent:
    """Upsert the content record for a resource.

    One content row per resource (keyed by resource_id).
    Overwrites raw_markdown and clean_text on conflict.
    """
    stmt = (
        pg_insert(ResourceContent)
        .values(
            resource_id=resource_id,
            raw_markdown=raw_markdown,
            clean_text=clean_text,
            char_count=len(raw_markdown),
        )
        .on_conflict_do_update(
            index_elements=["resource_id"],
            set_={
                "raw_markdown": raw_markdown,
                "clean_text": clean_text,
                "char_count": len(raw_markdown),
            },
        )
        .returning(ResourceContent)
    )
    result = await session.execute(stmt)
    return result.scalar_one()

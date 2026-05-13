"""Tag service — creates and associates tags with resources.

Handles both manual tags (from frontmatter) and future AI-generated tags.
"""
import re
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.tagging.entities.resource_tag import ResourceTag
from src.tagging.entities.tag import Tag

logger = structlog.get_logger(__name__)


def _slugify_tag(name: str) -> str:
    """Convert a tag name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


async def _get_or_create_tag(session: AsyncSession, name: str) -> Tag:
    """Fetch an existing tag or create it if it doesn't exist.

    Args:
        session: Active async database session.
        name: Tag name (will be slugified for the slug field).

    Returns:
        Tag: Existing or newly created tag record.
    """
    slug = _slugify_tag(name)

    stmt = select(Tag).where(Tag.slug == slug)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    new_tag_stmt = (
        insert(Tag)
        .values(id=uuid.uuid4(), name=name, slug=slug)
        .on_conflict_do_update(
            index_elements=["slug"],
            set_={"name": name},
        )
        .returning(Tag)
    )
    result = await session.execute(new_tag_stmt)
    return result.scalar_one()


async def upsert_tags_for_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
    tag_names: list[str],
    *,
    generated_by_ai: bool = False,
) -> list[ResourceTag]:
    """Create tags and associate them with a resource.

    Idempotent — safe to call multiple times for the same resource.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource to tag.
        tag_names: List of tag name strings from frontmatter.
        generated_by_ai: True if tags were AI-generated.

    Returns:
        list[ResourceTag]: Association records created or updated.

    Side Effects:
        - May create new tag records.
        - Creates resource_tags junction records.
    """
    if not tag_names:
        return []

    associations: list[ResourceTag] = []

    for name in tag_names:
        tag = await _get_or_create_tag(session, name)

        stmt = (
            insert(ResourceTag)
            .values(
                resource_id=resource_id,
                tag_id=tag.id,
                generated_by_ai=generated_by_ai,
            )
            .on_conflict_do_nothing()
            .returning(ResourceTag)
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            associations.append(row)

    logger.debug(
        "tags_upserted",
        resource_id=str(resource_id),
        tag_count=len(tag_names),
    )

    return associations

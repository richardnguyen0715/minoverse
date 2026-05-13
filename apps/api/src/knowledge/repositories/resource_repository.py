"""Repository for resources table — universal knowledge object persistence."""
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.knowledge.entities.resource import Resource

logger = structlog.get_logger(__name__)


async def upsert_resource(
    session: AsyncSession,
    *,
    vault_file_id: uuid.UUID,
    resource_type: str,
    title: str | None = None,
    url: str | None = None,
    author: str | None = None,
    language: str | None = None,
    published_at: datetime | None = None,
    extra_metadata: dict[str, object] | None = None,
) -> Resource:
    """Insert or update a resource record linked to a vault file.

    Args:
        session: Active async database session.
        vault_file_id: FK to the associated vault_files record.
        resource_type: One of the canonical resource types.
        title: Display title extracted from frontmatter or heading.
        url: Source URL if available.
        author: Author name if available.
        language: ISO 639-1 language code (e.g. 'en', 'vi').
        published_at: Publication timestamp if available.
        extra_metadata: Additional JSONB metadata.

    Returns:
        Resource: The persisted record.
    """
    stmt = (
        insert(Resource)
        .values(
            id=uuid.uuid4(),
            vault_file_id=vault_file_id,
            resource_type=resource_type,
            title=title,
            url=url,
            author=author,
            language=language,
            published_at=published_at,
            extra_metadata=extra_metadata,
            saved_at=datetime.utcnow(),
        )
        .on_conflict_do_update(
            index_elements=["vault_file_id"],
            set_={
                "resource_type": resource_type,
                "title": title,
                "url": url,
                "author": author,
                "language": language,
                "published_at": published_at,
                "metadata": extra_metadata,  # DB column name differs from attr
            },
        )
        .returning(Resource)
    )

    result = await session.execute(stmt)
    resource = result.scalar_one()

    logger.debug(
        "resource_upserted",
        resource_id=str(resource.id),
        resource_type=resource_type,
        vault_file_id=str(vault_file_id),
    )

    return resource


async def get_resource_by_vault_file_id(
    session: AsyncSession,
    vault_file_id: uuid.UUID,
) -> Resource | None:
    """Fetch a resource by its associated vault file ID.

    Args:
        session: Active async database session.
        vault_file_id: The vault file UUID to look up.

    Returns:
        Resource if found, None otherwise.
    """
    stmt = select(Resource).where(Resource.vault_file_id == vault_file_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

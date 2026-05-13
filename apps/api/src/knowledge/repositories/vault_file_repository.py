"""Repository for vault_files table — filesystem index persistence.

Repositories contain ONLY persistence logic. No business logic here.
"""
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.knowledge.entities.vault_file import VaultFile

logger = structlog.get_logger(__name__)


async def upsert_vault_file(
    session: AsyncSession,
    *,
    relative_path: str,
    absolute_path: str,
    file_hash: str,
    file_size: int,
    sync_status: str = "indexed",
) -> VaultFile:
    """Insert or update a vault file record.

    Uses PostgreSQL ON CONFLICT DO UPDATE for idempotent upserts.
    Safe to call multiple times for the same file.

    Args:
        session: Active async database session.
        relative_path: Path relative to vault root (unique key).
        absolute_path: Absolute filesystem path.
        file_hash: SHA-256 hash for change detection.
        file_size: File size in bytes.
        sync_status: Current sync status ('indexed', 'pending', 'error').

    Returns:
        VaultFile: The persisted (inserted or updated) record.
    """
    stmt = (
        insert(VaultFile)
        .values(
            id=uuid.uuid4(),
            relative_path=relative_path,
            absolute_path=absolute_path,
            file_hash=file_hash,
            file_size=file_size,
            sync_status=sync_status,
        )
        .on_conflict_do_update(
            index_elements=["relative_path"],
            set_={
                "absolute_path": absolute_path,
                "file_hash": file_hash,
                "file_size": file_size,
                "sync_status": sync_status,
            },
        )
        .returning(VaultFile)
    )

    result = await session.execute(stmt)
    vault_file = result.scalar_one()

    logger.debug(
        "vault_file_upserted",
        relative_path=relative_path,
        vault_file_id=str(vault_file.id),
    )

    return vault_file


async def get_vault_file_by_path(
    session: AsyncSession,
    relative_path: str,
) -> VaultFile | None:
    """Fetch a vault file record by its relative path.

    Args:
        session: Active async database session.
        relative_path: Path relative to vault root.

    Returns:
        VaultFile if found, None otherwise.
    """
    stmt = select(VaultFile).where(VaultFile.relative_path == relative_path)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def mark_vault_file_deleted(
    session: AsyncSession,
    relative_path: str,
) -> None:
    """Mark a vault file as deleted (sync_status = 'deleted').

    Does not physically remove the DB record — preserves history.

    Args:
        session: Active async database session.
        relative_path: Path of the deleted file.
    """
    vault_file = await get_vault_file_by_path(session, relative_path)
    if vault_file is not None:
        vault_file.sync_status = "deleted"
        logger.info("vault_file_marked_deleted", relative_path=relative_path)

"""Vault indexing service — scans and indexes all vault markdown files.

Used by the CLI `index` command and on-demand re-indexing.
"""
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from src.core.database import AsyncSessionFactory
from src.ingestion.services.ingestion_service import ingest_vault_file

logger = structlog.get_logger(__name__)


@dataclass
class IndexingResult:
    """Result of a vault indexing run.

    Attributes:
        total_files: Number of markdown files found.
        indexed: Successfully indexed file count.
        failed: Files that failed with errors.
        errors: Error messages for failed files.
    """

    total_files: int = 0
    indexed: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


async def index_vault(vault_path: Path) -> IndexingResult:
    """Scan the vault directory and ingest all markdown files.

    Each file is ingested in its own DB session and transaction.
    Failures on individual files are logged and counted but do not
    abort the overall indexing run.

    Args:
        vault_path: Absolute path to the vault root directory.

    Returns:
        IndexingResult: Summary of the indexing run.

    Side Effects:
        - Writes to all knowledge-domain tables.
    """
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    md_files = list(vault_path.rglob("*.md"))
    result = IndexingResult(total_files=len(md_files))

    logger.info(
        "vault_indexing_started",
        vault_path=str(vault_path),
        total=len(md_files),
    )

    for file_path in md_files:
        try:
            async with AsyncSessionFactory() as session:
                await ingest_vault_file(file_path, session)
            result.indexed += 1
        except Exception as exc:
            result.failed += 1
            error_msg = f"{file_path.name}: {exc}"
            result.errors.append(error_msg)
            logger.error(
                "vault_file_ingestion_failed",
                path=str(file_path),
                error=str(exc),
            )

    logger.info(
        "vault_indexing_completed",
        total=result.total_files,
        indexed=result.indexed,
        failed=result.failed,
    )

    return result

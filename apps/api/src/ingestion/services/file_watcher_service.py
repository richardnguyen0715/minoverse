"""File watcher service for the markdown vault.

Uses watchfiles to monitor the vault directory for filesystem events.
The watcher ONLY emits events — it never parses or writes to the DB.
All processing happens downstream in the ingestion pipeline.

Constraints:
    - No parsing logic in this module.
    - No direct DB access in this module.
    - Each change emits exactly one event to the event bus.
"""
from collections.abc import Callable, Coroutine
from enum import StrEnum
from pathlib import Path
from typing import Any

import structlog
from watchfiles import Change, awatch

logger = structlog.get_logger(__name__)


class VaultChangeType(StrEnum):
    """Type of filesystem change detected in the vault."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class VaultChangeEvent:
    """A filesystem change event for a vault file.

    Attributes:
        change_type: What kind of change occurred.
        file_path: Absolute path to the changed file.
    """

    def __init__(self, change_type: VaultChangeType, file_path: Path) -> None:
        self.change_type = change_type
        self.file_path = file_path

    def __repr__(self) -> str:
        return f"VaultChangeEvent({self.change_type}, {self.file_path})"


# Callback type for change handlers
ChangeHandler = Callable[[VaultChangeEvent], Coroutine[Any, Any, None]]


async def watch_vault(
    vault_path: Path,
    on_change: ChangeHandler,
    *,
    glob_pattern: str = "**/*.md",
) -> None:
    """Watch a vault directory and invoke a callback on every markdown change.

    This is the long-running watcher loop. It filters non-markdown files
    and emits structured VaultChangeEvent objects to the provided callback.

    The callback must be an async function. It is awaited for each event
    sequentially. For high-throughput scenarios, enqueue to a task queue
    inside the callback rather than doing heavy work there.

    Args:
        vault_path: Absolute path to the vault root directory.
        on_change: Async callback invoked for each markdown file change.
        glob_pattern: Glob pattern to filter watched files.

    Side Effects:
        - Reads filesystem events continuously until cancelled.
        - Invokes on_change for each matched event.

    Raises:
        FileNotFoundError: If vault_path does not exist.
    """
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault path not found: {vault_path}")

    logger.info("vault_watcher_started", vault_path=str(vault_path))

    async for changes in awatch(vault_path):
        for change_type, raw_path in changes:
            file_path = Path(raw_path)

            if not file_path.suffix == ".md":
                continue

            vault_change = _map_change_type(change_type, file_path)
            if vault_change is None:
                continue

            logger.info(
                "vault_file_changed",
                change_type=vault_change.change_type,
                path=str(vault_change.file_path),
            )

            await on_change(vault_change)


def _map_change_type(
    change: Change, file_path: Path
) -> VaultChangeEvent | None:
    """Map a watchfiles Change enum to a VaultChangeEvent.

    Args:
        change: The watchfiles change type.
        file_path: Path of the changed file.

    Returns:
        VaultChangeEvent or None if the change type is unhandled.
    """
    match change:
        case Change.added:
            return VaultChangeEvent(VaultChangeType.CREATED, file_path)
        case Change.modified:
            return VaultChangeEvent(VaultChangeType.MODIFIED, file_path)
        case Change.deleted:
            return VaultChangeEvent(VaultChangeType.DELETED, file_path)
        case _:
            return None

"""Alembic environment configuration for async SQLAlchemy."""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all ORM models so Alembic can detect them
from src.core.database import Base
from src.knowledge.entities.vault_file import VaultFile  # noqa: F401
from src.knowledge.entities.resource import Resource  # noqa: F401
from src.retrieval.entities.chunk import ResourceContent, ResourceChunk  # noqa: F401
from src.embedding.entities.chunk_embedding import ChunkEmbedding  # noqa: F401
from src.notes.entities.note import Note  # noqa: F401
from src.graph.entities.wiki_link import WikiLink  # noqa: F401
from src.graph.entities.concept_entity import ConceptEntity  # noqa: F401
from src.graph.entities.resource_entity import ResourceEntity  # noqa: F401
from src.graph.entities.concept_relation import ConceptRelation  # noqa: F401
from src.tagging.entities.tag import Tag  # noqa: F401
from src.tagging.entities.resource_tag import ResourceTag  # noqa: F401
from src.ingestion.entities.ingestion_job import IngestionJob  # noqa: F401
from src.memory.entities.memory_session import MemorySession  # noqa: F401
from src.memory.entities.memory_turn import MemoryTurn  # noqa: F401
from src.memory.entities.episodic_memory import EpisodicMemory  # noqa: F401
from src.memory.entities.semantic_memory import SemanticMemory  # noqa: F401
from src.sync.entities.sync_event import SyncEvent  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations against an active connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

"""Minoverse CLI — vault management and knowledge operations.

Commands:
    index   Scan and index all vault markdown files into the database.
    watch   Start the file watcher daemon for live vault sync.
    graph   Display knowledge graph statistics.
    rebuild Rebuild embeddings (Phase 3+, stub).
    search  Search the vault (Phase 2+, stub).

Usage:
    uv run minoverse index
    uv run minoverse watch
    uv run minoverse graph
"""
import asyncio
from pathlib import Path

import structlog
import typer

from src.core.config import settings
from src.core.logging import configure_logging

app = typer.Typer(
    name="minoverse",
    help="Minoverse — AI-native Knowledge OS CLI",
    no_args_is_help=True,
)

logger = structlog.get_logger(__name__)


def _get_vault_path() -> Path:
    """Resolve the vault path from settings."""
    vault_path = Path(settings.vault_path).resolve()
    if not vault_path.exists():
        typer.echo(f"❌ Vault not found: {vault_path}", err=True)
        raise typer.Exit(code=1)
    return vault_path


@app.command()
def index(
    vault: str = typer.Option(None, "--vault", "-v", help="Override vault path"),
) -> None:
    """Scan and index all markdown files in the vault into the database."""
    configure_logging(debug=settings.debug)

    from src.knowledge.services.vault_indexing_service import index_vault

    vault_path = Path(vault).resolve() if vault else _get_vault_path()

    typer.echo(f"📚 Indexing vault: {vault_path}")

    async def _run() -> None:
        result = await index_vault(vault_path)
        typer.echo(f"✅ Indexed {result.indexed}/{result.total_files} files")
        if result.failed:
            typer.echo(f"⚠️  {result.failed} files failed:", err=True)
            for error in result.errors:
                typer.echo(f"   • {error}", err=True)

    asyncio.run(_run())


@app.command()
def watch(
    vault: str = typer.Option(None, "--vault", "-v", help="Override vault path"),
) -> None:
    """Start the live file watcher daemon for vault sync."""
    configure_logging(debug=settings.debug)

    from src.core.database import AsyncSessionFactory
    from src.ingestion.services.file_watcher_service import (
        VaultChangeEvent,
        VaultChangeType,
        watch_vault,
    )
    from src.ingestion.services.ingestion_service import (
        delete_vault_file,
        ingest_vault_file,
    )

    vault_path = Path(vault).resolve() if vault else _get_vault_path()

    typer.echo(f"👁  Watching vault: {vault_path}  (Ctrl+C to stop)")

    async def handle_change(event: VaultChangeEvent) -> None:
        async with AsyncSessionFactory() as session:
            if event.change_type == VaultChangeType.DELETED:
                await delete_vault_file(event.file_path, session)
            else:
                await ingest_vault_file(event.file_path, session)

    async def _run() -> None:
        await watch_vault(vault_path, handle_change)

    asyncio.run(_run())


@app.command()
def graph() -> None:
    """Display knowledge graph statistics (node and edge counts)."""
    configure_logging(debug=settings.debug)

    async def _run() -> None:
        from sqlalchemy import func, select

        from src.core.database import AsyncSessionFactory
        from src.graph.entities.wiki_link import WikiLink
        from src.knowledge.entities.resource import Resource
        from src.knowledge.entities.vault_file import VaultFile
        from src.notes.entities.note import Note

        async with AsyncSessionFactory() as session:
            vault_files = (
                await session.execute(select(func.count(VaultFile.id)))
            ).scalar()
            resources = (
                await session.execute(select(func.count(Resource.id)))
            ).scalar()
            notes = (
                await session.execute(select(func.count(Note.id)))
            ).scalar()
            links = (
                await session.execute(select(func.count(WikiLink.id)))
            ).scalar()

        typer.echo("📊 Knowledge Graph Stats")
        typer.echo(f"   Vault files : {vault_files}")
        typer.echo(f"   Resources   : {resources}")
        typer.echo(f"   Notes       : {notes}")
        typer.echo(f"   Wiki links  : {links}")

    asyncio.run(_run())


@app.command()
def embed(
    force: bool = typer.Option(False, "--force", "-f", help="Re-embed already-embedded chunks"),
) -> None:
    """Generate vector embeddings for all resource_chunks (requires LMStudio).

    Calls the configured LMSTUDIO_EMBEDDING_MODEL for each chunk and stores
    results in chunk_embeddings. Run ``minoverse chunk`` first.
    """
    configure_logging(debug=settings.debug)

    async def _run() -> None:
        from src.core.database import AsyncSessionFactory
        from src.embedding.services.embedding_service import embed_all_resources

        typer.echo(f"🔢 Embedding chunks via LMStudio ({settings.lmstudio_embedding_model})…")
        async with AsyncSessionFactory() as session:
            summary = await embed_all_resources(session, force=force)

        typer.echo(
            f"✅ Done — {summary['created']} embeddings created across "
            f"{summary['total_resources']} resources"
        )
        if summary["skipped"]:
            typer.echo(f"   ↩ {summary['skipped']} chunks skipped (already embedded)")
        if summary["errors"]:
            typer.echo(f"⚠️  {len(summary['errors'])} errors:", err=True)
            for e in summary["errors"]:
                typer.echo(f"   • {e}", err=True)

    asyncio.run(_run())


@app.command()
def rebuild(
    force: bool = typer.Option(False, "--force", "-f", help="Re-embed even existing embeddings"),
) -> None:
    """Rebuild all chunk embeddings (re-chunk then re-embed all resources).

    Equivalent to running ``minoverse chunk --force`` then ``minoverse embed --force``.
    """
    configure_logging(debug=settings.debug)

    async def _run() -> None:
        from src.core.database import AsyncSessionFactory
        from src.embedding.services.embedding_service import embed_all_resources
        from src.retrieval.services.chunk_service import chunk_all_resources

        typer.echo("✂️  Re-chunking all resources…")
        async with AsyncSessionFactory() as session:
            chunk_summary = await chunk_all_resources(session, force=True)
            await session.commit()
        typer.echo(f"   {chunk_summary['created']} chunks created")

        typer.echo(f"🔢 Re-embedding via LMStudio ({settings.lmstudio_embedding_model})…")
        async with AsyncSessionFactory() as session:
            embed_summary = await embed_all_resources(session, force=True)
        typer.echo(
            f"✅ Done — {embed_summary['created']} embeddings created across "
            f"{embed_summary['total_resources']} resources"
        )
        if embed_summary["errors"]:
            typer.echo(f"⚠️  {len(embed_summary['errors'])} errors:", err=True)
            for e in embed_summary["errors"]:
                typer.echo(f"   • {e}", err=True)

    asyncio.run(_run())


@app.command()
def chunk(
    force: bool = typer.Option(False, "--force", "-f", help="Re-chunk already-chunked resources"),
) -> None:
    """Split all resource_contents into resource_chunks (no LLM required).

    Must be run after indexing and before embeddings can be generated.
    """
    configure_logging(debug=settings.debug)

    async def _run() -> None:
        from src.core.database import AsyncSessionFactory
        from src.retrieval.services.chunk_service import chunk_all_resources

        typer.echo("✂️  Chunking all resources…")
        async with AsyncSessionFactory() as session:
            summary = await chunk_all_resources(session, force=force)
            await session.commit()

        typer.echo(f"✅ Done — {summary['created']} chunks created across {summary['total']} resources")
        if summary["skipped"]:
            typer.echo(f"   ↩ {summary['skipped']} resources skipped (already chunked)")
        if summary["errors"]:
            typer.echo(f"⚠️  {len(summary['errors'])} errors:", err=True)
            for e in summary["errors"]:
                typer.echo(f"   • {e['resource_id']}: {e['error']}", err=True)

    asyncio.run(_run())


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
) -> None:
    """Search the knowledge vault (Phase 2+ — not yet implemented)."""
    typer.echo("⏳ Hybrid retrieval is implemented in Phase 2.")
    raise typer.Exit(code=0)

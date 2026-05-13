"""FastAPI routes for the knowledge domain — vault files and resources."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.embedding.services.embedding_service import embed_all_resources, embed_resource
from src.knowledge.entities.resource import Resource
from src.knowledge.entities.vault_file import VaultFile
from src.retrieval.entities.chunk import ResourceContent
from src.retrieval.services.chunk_service import chunk_all_resources, chunk_resource

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/vault-files")
async def list_vault_files(
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, object]]:
    """List all indexed vault files."""
    result = await session.execute(select(VaultFile).limit(100))
    files = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "relative_path": f.relative_path,
            "sync_status": f.sync_status,
            "file_hash": f.file_hash,
            "file_size": f.file_size,
        }
        for f in files
    ]


@router.get("/resources")
async def list_resources(
    resource_type: str | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, object]]:
    """List resources, optionally filtered by type."""
    stmt = select(Resource).where(Resource.deleted_at.is_(None)).limit(100)
    if resource_type:
        stmt = stmt.where(Resource.resource_type == resource_type)
    result = await session.execute(stmt)
    resources = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "resource_type": r.resource_type,
            "title": r.title,
            "url": r.url,
            "author": r.author,
            "is_favorite": r.is_favorite,
            "is_archived": r.is_archived,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        }
        for r in resources
    ]


@router.get("/resources/{resource_id}")
async def get_resource(
    resource_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    """Fetch a single resource by ID."""
    result = await session.execute(
        select(Resource).where(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {
        "id": str(resource.id),
        "vault_file_id": str(resource.vault_file_id),
        "resource_type": resource.resource_type,
        "title": resource.title,
        "url": resource.url,
        "author": resource.author,
        "language": resource.language,
        "extra_metadata": resource.extra_metadata,
        "is_favorite": resource.is_favorite,
        "is_archived": resource.is_archived,
        "created_at": resource.created_at.isoformat(),
        "updated_at": resource.updated_at.isoformat(),
    }


@router.get("/resources/{resource_id}/content")
async def get_resource_content(
    resource_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    """Return stored markdown/text content for a resource."""
    result = await session.execute(
        select(ResourceContent).where(ResourceContent.resource_id == resource_id)
    )
    content = result.scalar_one_or_none()
    if content is None:
        return {"resource_id": str(resource_id), "raw_markdown": None, "clean_text": None}
    return {
        "resource_id": str(resource_id),
        "raw_markdown": content.raw_markdown,
        "clean_text": content.clean_text,
        "char_count": content.char_count,
    }


@router.post("/chunk-all")
async def trigger_chunk_all(
    force: bool = False,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Split all resource_contents into resource_chunks (pure text splitting, no LLM).

    This is idempotent. Use ``force=true`` to re-chunk resources that already
    have chunks. Must be called before embeddings can be generated.

    Returns a summary: total, created, skipped, errors.
    """
    summary = await chunk_all_resources(session, force=force)
    await session.commit()
    return summary


@router.post("/resources/{resource_id}/chunk")
async def trigger_chunk_resource(
    resource_id: uuid.UUID,
    force: bool = False,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Split a single resource's content into chunks.

    Args:
        resource_id: UUID of the resource.
        force: If true, delete existing chunks and re-create them.
    """
    result = await session.execute(
        select(Resource).where(Resource.id == resource_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    chunk_result = await chunk_resource(session, resource_id, force=force)
    await session.commit()
    return {
        "resource_id": str(resource_id),
        "created": chunk_result.created,
        "skipped": chunk_result.skipped,
        "error": chunk_result.error,
    }


@router.post("/embed-all")
async def trigger_embed_all(
    force: bool = False,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Generate vector embeddings for all resource_chunks without embeddings.

    Calls LMStudio's embedding model (nomic-embed-text-v1.5, 768-dim).
    Idempotent — use ``force=true`` to re-embed existing embeddings.

    Returns a summary: total_resources, total_chunks, created, skipped, errors.
    """
    summary = await embed_all_resources(session, force=force)
    return summary


@router.post("/resources/{resource_id}/embed")
async def trigger_embed_resource(
    resource_id: uuid.UUID,
    force: bool = False,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Generate embeddings for all chunks of a single resource.

    Args:
        resource_id: UUID of the resource to embed.
        force: If true, overwrite existing embeddings.
    """
    result = await session.execute(
        select(Resource).where(Resource.id == resource_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    embed_result = await embed_resource(session, resource_id, force=force)
    return {
        "resource_id": str(resource_id),
        "created": embed_result.created,
        "skipped": embed_result.skipped,
        "errors": embed_result.errors,
    }

"""FastAPI routes for the knowledge graph domain (Phase 4)."""
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.graph.repositories.concept_entity_repository import (
    get_concept_entity,
    list_concept_entities,
)
from src.graph.schemas.graph_schemas import ConceptEntityOut, GraphOut
from src.graph.services import graph_traversal_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/entities", response_model=list[ConceptEntityOut])
async def list_entities(
    entity_type: str | None = Query(default=None, description="Filter by entity_type"),
    session: AsyncSession = Depends(get_async_session),
) -> list[ConceptEntityOut]:
    """List all concept entities, optionally filtered by type."""
    entities = await list_concept_entities(session, entity_type=entity_type)
    return [ConceptEntityOut.model_validate(e) for e in entities]


@router.get("/entities/{entity_id}", response_model=ConceptEntityOut)
async def get_entity(
    entity_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> ConceptEntityOut:
    """Get a single concept entity by ID."""
    entity = await get_concept_entity(session, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    return ConceptEntityOut.model_validate(entity)


@router.get("/entities/{entity_id}/neighbors", response_model=GraphOut)
async def get_entity_neighbors(
    entity_id: uuid.UUID,
    depth: int = Query(default=1, ge=1, le=3, description="Traversal depth"),
    session: AsyncSession = Depends(get_async_session),
) -> GraphOut:
    """Return the subgraph centred on a single entity."""
    return await graph_traversal_service.get_neighbors(session, entity_id, depth=depth)


@router.get("/resource/{resource_id}", response_model=GraphOut)
async def get_resource_graph(
    resource_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> GraphOut:
    """Return the concept graph for a specific resource."""
    return await graph_traversal_service.get_resource_graph(session, resource_id)


@router.get("/full", response_model=GraphOut)
async def get_full_graph(
    session: AsyncSession = Depends(get_async_session),
) -> GraphOut:
    """Return the complete global knowledge graph."""
    return await graph_traversal_service.get_full_graph(session)


@router.post("/resource/{resource_id}/build", response_model=dict[str, str])
async def trigger_graph_build(resource_id: uuid.UUID) -> dict[str, str]:
    """Manually trigger a graph build job for a resource."""
    from src.graph.workers.graph_worker import build_graph_for_resource

    build_graph_for_resource.send(str(resource_id))
    logger.info("graph_build_triggered_via_api", resource_id=str(resource_id))
    return {"status": "queued", "resource_id": str(resource_id)}

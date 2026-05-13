"""Graph traversal service — composes repository data into GraphOut responses."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.graph.repositories.concept_entity_repository import (
    get_concept_entity,
    get_entities_for_resource,
)
from src.graph.repositories.concept_relation_repository import (
    get_full_graph as repo_get_full_graph,
    get_resource_graph as repo_get_resource_graph,
    list_neighbors,
    list_relations_for_entity,
)
from src.graph.schemas.graph_schemas import GraphEdge, GraphNode, GraphOut, RelationType


def _build_graph_out(entities, relations) -> GraphOut:  # type: ignore[no-untyped-def]
    """Convert ORM lists into a GraphOut response object."""
    from src.graph.schemas.graph_schemas import EntityType

    nodes = [
        GraphNode(
            id=e.id,
            name=e.name,
            entity_type=EntityType(e.entity_type),
            description=e.description,
        )
        for e in entities
    ]

    entity_ids = {e.id for e in entities}
    edges = [
        GraphEdge(
            source=r.source_entity_id,
            target=r.target_entity_id,
            relation_type=RelationType(r.relation_type),
            weight=r.weight,
        )
        for r in relations
        if r.source_entity_id in entity_ids and r.target_entity_id in entity_ids
        and r.relation_type in RelationType._value2member_map_
    ]

    return GraphOut(nodes=nodes, edges=edges)


async def get_neighbors(
    session: AsyncSession,
    entity_id: uuid.UUID,
    depth: int = 1,
) -> GraphOut:
    """Return a subgraph centred on a single entity.

    Args:
        session: Active async database session.
        entity_id: UUID of the focal entity.
        depth: Traversal depth (only depth=1 supported).

    Returns:
        GraphOut with the focal entity plus its immediate neighbors and edges.
    """
    focal = await get_concept_entity(session, entity_id)
    if focal is None:
        return GraphOut(nodes=[], edges=[])

    neighbors_with_relations = await list_neighbors(session, entity_id, depth=depth)
    neighbor_entities = [pair[0] for pair in neighbors_with_relations]
    relations = await list_relations_for_entity(session, entity_id)

    all_entities = [focal, *neighbor_entities]
    return _build_graph_out(all_entities, relations)


async def get_resource_graph(
    session: AsyncSession,
    resource_id: uuid.UUID,
) -> GraphOut:
    """Return the concept graph for a specific resource.

    Args:
        session: Active async database session.
        resource_id: UUID of the resource.

    Returns:
        GraphOut with all entities and relations scoped to the resource.
    """
    entities, relations = await repo_get_resource_graph(session, resource_id)
    return _build_graph_out(entities, relations)


async def get_full_graph(
    session: AsyncSession,
) -> GraphOut:
    """Return the global knowledge graph with all entities and relations.

    Args:
        session: Active async database session.

    Returns:
        GraphOut containing every concept entity and relation.
    """
    entities, relations = await repo_get_full_graph(session)
    return _build_graph_out(entities, relations)

"""
Graph API Endpoints:
Exposes visual nodes and directional relationship edges for the knowledge graph visualizer.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.app.api.chat import _shared_memory_service

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    user_id: str


class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    weight: float


class KnowledgeGraphResponse(BaseModel):
    user_id: str
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]


@router.get("/", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    user_id: str = Query(default="default_user", description="Filter graph by user ID"),
):
    """Returns the full knowledge graph network nodes and edges for visualization."""
    raw_nodes = _shared_memory_service.graph_store.get_all_nodes(user_id=user_id)
    raw_edges = _shared_memory_service.graph_store.get_all_edges(user_id=user_id)

    nodes = [
        GraphNodeResponse(
            id=n.id,
            label=n.name,
            type=n.entity_type.value,
            user_id=n.user_id,
        )
        for n in raw_nodes
    ]

    edges = [
        GraphEdgeResponse(
            id=e.id,
            source=e.source_node_id,
            target=e.target_node_id,
            relation=e.relation.value,
            weight=e.weight,
        )
        for e in raw_edges
    ]

    return KnowledgeGraphResponse(
        user_id=user_id,
        nodes=nodes,
        edges=edges,
    )


@router.get("/associative")
async def get_associative_recall(
    query: str = Query(..., description="Query topic to expand"),
    user_id: str = Query(default="default_user"),
    hops: int = Query(default=2, ge=1, le=4),
):
    """Performs multi-hop associative recall starting from matched seed entities."""
    return _shared_memory_service.retrieve_associative(
        query=query,
        user_id=user_id,
        max_hops=hops,
    )

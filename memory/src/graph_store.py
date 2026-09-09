"""
In-Memory Knowledge Graph Store:
Maintains entity nodes and directional relationship edges with indexing for fast traversal.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Set
from .graph_schemas import KnowledgeNode, KnowledgeEdge, GraphTriple, EntityType, RelationType


class KnowledgeGraphStore:
    """
    Graph index maintaining:
    - nodes: node_id -> KnowledgeNode
    - edges: edge_id -> KnowledgeEdge
    - adjacency: node_id -> set of outgoing edge_ids
    - entity_index: (canonical_name, user_id) -> node_id
    """

    def __init__(self):
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}
        self._adjacency: Dict[str, List[str]] = {}
        self._entity_index: Dict[tuple[str, str], str] = {}

    def get_or_create_node(
        self,
        name: str,
        entity_type: EntityType,
        user_id: str = "default_user",
    ) -> KnowledgeNode:
        canonical = name.strip().title()
        key = (canonical.lower(), user_id)
        if key in self._entity_index:
            node_id = self._entity_index[key]
            return self._nodes[node_id]

        node = KnowledgeNode(
            name=canonical,
            entity_type=entity_type,
            user_id=user_id,
        )
        self._nodes[node.id] = node
        self._entity_index[key] = node.id
        self._adjacency[node.id] = []
        return node

    def add_triple(
        self,
        triple: GraphTriple,
        user_id: str = "default_user",
    ) -> KnowledgeEdge:
        src = self.get_or_create_node(triple.subject, triple.subject_type, user_id)
        tgt = self.get_or_create_node(triple.object, triple.object_type, user_id)

        # Check existing edge
        for edge_id in self._adjacency.get(src.id, []):
            edge = self._edges[edge_id]
            if edge.target_node_id == tgt.id and edge.relation == triple.relation:
                edge.weight = min(1.0, edge.weight + 0.1)
                return edge

        new_edge = KnowledgeEdge(
            source_node_id=src.id,
            target_node_id=tgt.id,
            relation=triple.relation,
            confidence=triple.confidence,
            source_memory_id=triple.source_memory_id,
            user_id=user_id,
        )
        self._edges[new_edge.id] = new_edge
        self._adjacency[src.id].append(new_edge.id)
        return new_edge

    def get_neighbors(self, node_id: str) -> List[tuple[KnowledgeEdge, KnowledgeNode]]:
        results = []
        edge_ids = self._adjacency.get(node_id, [])
        for eid in edge_ids:
            edge = self._edges.get(eid)
            if edge and edge.target_node_id in self._nodes:
                target_node = self._nodes[edge.target_node_id]
                results.append((edge, target_node))
        return results

    def get_all_nodes(self, user_id: Optional[str] = None) -> List[KnowledgeNode]:
        if user_id:
            return [n for n in self._nodes.values() if n.user_id == user_id]
        return list(self._nodes.values())

    def get_all_edges(self, user_id: Optional[str] = None) -> List[KnowledgeEdge]:
        if user_id:
            return [e for e in self._edges.values() if e.user_id == user_id]
        return list(self._edges.values())

    def clear(self, user_id: Optional[str] = None) -> None:
        if user_id:
            to_del_nodes = [nid for nid, n in self._nodes.items() if n.user_id == user_id]
            for nid in to_del_nodes:
                del self._nodes[nid]
                if nid in self._adjacency:
                    del self._adjacency[nid]
            to_del_edges = [eid for eid, e in self._edges.items() if e.user_id == user_id]
            for eid in to_del_edges:
                del self._edges[eid]
            self._entity_index = {k: v for k, v in self._entity_index.items() if k[1] != user_id}
        else:
            self._nodes.clear()
            self._edges.clear()
            self._adjacency.clear()
            self._entity_index.clear()

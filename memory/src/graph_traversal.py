"""
Multi-hop Associative Graph Traversal Algorithm:
Expands semantic query context by navigating outward from seed nodes.
"""
from __future__ import annotations
from typing import List, Set, Dict, Any
from .graph_store import KnowledgeGraphStore
from .graph_schemas import KnowledgeNode, KnowledgeEdge


class GraphTraversalEngine:
    """
    Executes breadth-first multi-hop associative recall.
    Starting from recognized seed entities, it surfaces 1st and 2nd degree
    related facts to broaden the context window.
    """

    def __init__(self, graph_store: KnowledgeGraphStore):
        self.graph_store = graph_store

    def find_seed_nodes(self, query: str, user_id: str = "default_user") -> List[KnowledgeNode]:
        """Finds graph nodes whose canonical name appears in the query string."""
        q_lower = query.lower()
        all_nodes = self.graph_store.get_all_nodes(user_id=user_id)
        seeds = [n for n in all_nodes if n.name.lower() in q_lower]
        return seeds

    def traverse(
        self,
        query: str,
        user_id: str = "default_user",
        max_hops: int = 2,
        max_results: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Traverses outward from seed nodes and returns formatted associative relations.
        """
        seeds = self.find_seed_nodes(query, user_id)
        if not seeds:
            return []

        visited_nodes: Set[str] = {s.id for s in seeds}
        visited_edges: Set[str] = set()
        queue: List[tuple[KnowledgeNode, int]] = [(s, 0) for s in seeds]
        results: List[Dict[str, Any]] = []

        while queue and len(results) < max_results:
            current_node, depth = queue.pop(0)
            if depth >= max_hops:
                continue

            neighbors = self.graph_store.get_neighbors(current_node.id)
            for edge, target in neighbors:
                if edge.id in visited_edges:
                    continue
                visited_edges.add(edge.id)

                results.append({
                    "subject": current_node.name,
                    "relation": edge.relation.value,
                    "object": target.name,
                    "hop": depth + 1,
                    "weight": edge.weight,
                    "source_memory_id": edge.source_memory_id,
                })

                if target.id not in visited_nodes:
                    visited_nodes.add(target.id)
                    queue.append((target, depth + 1))

                if len(results) >= max_results:
                    break

        return results

"""
High-level memory orchestrator coordinating extraction, storage,
and now vector-indexed retrieval with recency decay, user governance,
and privacy toggles.
"""
from __future__ import annotations
from typing import Optional, Dict

from .schemas import MemoryItem, ExtractionResult, MemoryCategory
from .extractor import MemoryExtractor
from .store import MemoryStore
from .retriever import MemoryRetriever
from .graph_store import KnowledgeGraphStore
from .graph_extractor import GraphTripleExtractor
from .graph_traversal import GraphTraversalEngine


class MemoryService:
    """
    Central coordinator:
      1. process_turn() -> extract durable facts -> store -> index in Qdrant
      2. retrieve() -> semantic search + recency boost -> ranked results
      3. Governance & Privacy: view, filter, manual edit, delete, clear, pause/resume learning
    """

    def __init__(
        self,
        store: Optional[MemoryStore] = None,
        extractor: Optional[MemoryExtractor] = None,
        retriever: Optional[MemoryRetriever] = None,
    ):
        self.store = store or MemoryStore()
        self.extractor = extractor or MemoryExtractor()
        self.retriever = retriever or MemoryRetriever()
        self.graph_store = KnowledgeGraphStore()
        self.graph_extractor = GraphTripleExtractor()
        self.graph_traversal = GraphTraversalEngine(self.graph_store)
        # Per-user learning state: user_id -> is_learning_enabled (default True)
        self._user_learning_enabled: Dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Privacy & Governance Controls
    # ------------------------------------------------------------------

    def is_learning_enabled(self, user_id: str = "default_user") -> bool:
        return self._user_learning_enabled.get(user_id, True)

    def set_learning_enabled(self, user_id: str, enabled: bool) -> bool:
        self._user_learning_enabled[user_id] = enabled
        return enabled

    # ------------------------------------------------------------------
    # Extraction + Storage
    # ------------------------------------------------------------------

    def process_turn(
        self,
        user_message: str,
        assistant_message: Optional[str] = None,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        source_agent: str = "personal_assistant",
    ) -> tuple[list[MemoryItem], ExtractionResult]:
        # If user paused learning, return empty without extracting/storing
        if not self.is_learning_enabled(user_id):
            return [], ExtractionResult(memories=[], raw_turn=user_message)

        existing = self.store.get_all(user_id=user_id)

        extraction_result = self.extractor.extract_from_turn(
            user_message=user_message,
            assistant_message=assistant_message,
            existing_memories=existing,
        )

        applied_items = self.store.apply_extraction(
            result=extraction_result,
            user_id=user_id,
            source_agent=source_agent,
            session_id=session_id,
        )

        # Incrementally index newly written memories into vector store & knowledge graph
        for item in applied_items:
            self.retriever.index_single(item)
            triples = self.graph_extractor.extract_triples(
                text=item.content,
                user_name=user_id,
                source_memory_id=item.id,
            )
            for t in triples:
                self.graph_store.add_triple(t, user_id=user_id)

        return applied_items, extraction_result

    # ------------------------------------------------------------------
    # Semantic Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 5,
        recency_boost: bool = True,
    ) -> list[tuple[MemoryItem, float]]:
        return self.retriever.search(
            query=query,
            user_id=user_id,
            category=category,
            limit=limit,
            recency_boost=recency_boost,
        )

    def rebuild_index(self, user_id: Optional[str] = None) -> None:
        all_memories = self.store.get_all(user_id=user_id)
        self.retriever.index_memories(all_memories)

    def retrieve_associative(
        self,
        query: str,
        user_id: str = "default_user",
        max_hops: int = 2,
    ) -> list[dict]:
        """Retrieves multi-hop associative relationships from the knowledge graph."""
        return self.graph_traversal.traverse(query=query, user_id=user_id, max_hops=max_hops)

    # ------------------------------------------------------------------
    # Delegated Store Operations (CRUD & Governance)
    # ------------------------------------------------------------------

    def add_manual_memory(
        self,
        content: str,
        category: MemoryCategory,
        user_id: str = "default_user",
        source_agent: str = "user_direct",
        metadata: Optional[dict] = None,
    ) -> MemoryItem:
        item = self.store.add(
            content=content,
            category=category,
            user_id=user_id,
            source_agent=source_agent,
            metadata=metadata or {},
        )
        self.retriever.index_single(item)
        return item

    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        return self.store.get(memory_id)

    def update_memory(
        self,
        memory_id: str,
        content: str,
        category: Optional[MemoryCategory] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[MemoryItem]:
        updated = self.store.update(
            memory_id=memory_id,
            content=content,
            category=category,
            metadata=metadata,
        )
        if updated:
            self.rebuild_index()
        return updated

    def delete_memory(self, memory_id: str) -> bool:
        self.retriever.remove(memory_id)
        return self.store.delete(memory_id)

    def get_all(
        self,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        search_query: Optional[str] = None,
    ) -> list[MemoryItem]:
        mems = self.store.get_all(user_id=user_id, category=category)
        if search_query:
            q_lower = search_query.lower()
            mems = [m for m in mems if q_lower in m.content.lower()]
        return mems

    def clear_all(self, user_id: Optional[str] = None) -> int:
        count = self.store.clear_all(user_id=user_id)
        self.rebuild_index()
        return count

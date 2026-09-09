"""
High-level memory orchestrator coordinating extraction, storage,
and now vector-indexed retrieval with recency decay.
"""
from __future__ import annotations
from typing import Optional

from .schemas import MemoryItem, ExtractionResult, MemoryCategory
from .extractor import MemoryExtractor
from .store import MemoryStore
from .retriever import MemoryRetriever


class MemoryService:
    """
    Central coordinator:
      1. process_turn() → extract durable facts → store → index in Qdrant
      2. retrieve() → semantic search + recency boost → ranked results
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

    # ------------------------------------------------------------------
    # Phase 1: Extraction + Storage
    # ------------------------------------------------------------------

    def process_turn(
        self,
        user_message: str,
        assistant_message: Optional[str] = None,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        source_agent: str = "personal_assistant",
    ) -> tuple[list[MemoryItem], ExtractionResult]:
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

        # Phase 2: incrementally index any newly written memories
        for item in applied_items:
            self.retriever.index_single(item)

        return applied_items, extraction_result

    # ------------------------------------------------------------------
    # Phase 2: Semantic Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 5,
        recency_boost: bool = True,
    ) -> list[tuple[MemoryItem, float]]:
        """
        Retrieve memories most relevant to the query string.
        Returns a ranked list of (MemoryItem, score) tuples.
        """
        return self.retriever.search(
            query=query,
            user_id=user_id,
            category=category,
            limit=limit,
            recency_boost=recency_boost,
        )

    def rebuild_index(self, user_id: Optional[str] = None) -> None:
        """Full rebuild of the vector index from the current store contents."""
        all_memories = self.store.get_all(user_id=user_id)
        self.retriever.index_memories(all_memories)

    # ------------------------------------------------------------------
    # Delegated store operations (privacy controls, CRUD)
    # ------------------------------------------------------------------

    def delete_memory(self, memory_id: str) -> bool:
        self.retriever.remove(memory_id)
        return self.store.delete(memory_id)

    def get_all(
        self,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
    ) -> list[MemoryItem]:
        return self.store.get_all(user_id=user_id, category=category)

    def clear_all(self, user_id: Optional[str] = None) -> int:
        count = self.store.clear_all(user_id=user_id)
        # Rebuild empty index
        self.retriever.index_memories([])
        return count

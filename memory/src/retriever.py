"""
Retrieval layer — wraps a Qdrant in-memory collection with:
  - Vector similarity search over TF-IDF embeddings
  - Recency decay bonus (newer memories score slightly higher)
  - User/category scoping via Qdrant payload filters
"""
from __future__ import annotations
from typing import Optional
import datetime

from .schemas import MemoryItem, MemoryCategory
from .embedder import TFIDFEmbedder


class MemoryRetriever:
    """
    Semantic retriever backed by an in-memory Qdrant collection.
    QdrantClient(":memory:") runs entirely in-process — no server needed.
    Switch to QdrantClient(url=...) for production.

    Uses query_points() (qdrant-client v1.x API).
    """

    COLLECTION_NAME = "memory_bank"
    RECENCY_WEIGHT = 0.08           # 8% bonus for very fresh memories
    RECENCY_HALF_LIFE_DAYS = 90     # score decays to 50% after 90 days

    def __init__(
        self,
        embedder: Optional[TFIDFEmbedder] = None,
        qdrant_location: str = ":memory:",
    ):
        self._embedder = embedder or TFIDFEmbedder()
        self._qdrant_location = qdrant_location
        self._client = None            # lazy init
        self._dim: Optional[int] = None
        self._indexed: dict[str, MemoryItem] = {}  # id -> item

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _init_client(self, dim: int) -> None:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self._client = QdrantClient(self._qdrant_location)
        self._dim = dim

        if self._client.collection_exists(self.COLLECTION_NAME):
            self._client.delete_collection(self.COLLECTION_NAME)

        self._client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_memories(self, memories: list[MemoryItem]) -> None:
        """Re-fit the embedder on all memories and bulk index into Qdrant."""
        if not memories:
            return

        texts = [m.content for m in memories]
        self._embedder.fit(texts)
        vectors = self._embedder.encode(texts)
        dim = len(vectors[0])

        if self._client is None or self._dim != dim:
            self._init_client(dim)

        from qdrant_client.models import PointStruct

        points = []
        for memory, vector in zip(memories, vectors):
            self._indexed[memory.id] = memory
            points.append(
                PointStruct(
                    id=self._stable_int_id(memory.id),
                    vector=vector,
                    payload={
                        "memory_id": memory.id,
                        "user_id": memory.user_id,
                        "category": memory.category.value,
                        "created_at": memory.created_at,
                    },
                )
            )

        self._client.upsert(collection_name=self.COLLECTION_NAME, points=points)

    def index_single(self, memory: MemoryItem) -> None:
        """Incrementally add one memory (re-fits on full corpus for IDF accuracy)."""
        existing = list(self._indexed.values())
        existing_ids = {m.id for m in existing}
        if memory.id not in existing_ids:
            existing.append(memory)
        self.index_memories(existing)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 5,
        recency_boost: bool = True,
    ) -> list[tuple[MemoryItem, float]]:
        """
        Return top-k memories ranked by cosine similarity + optional recency bonus.
        Returns list of (MemoryItem, final_score) tuples.
        """
        if self._client is None or not self._indexed:
            return []

        query_vector = self._embedder.encode_single(query)
        if not any(query_vector):
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        must_conditions = []
        if user_id:
            must_conditions.append(
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            )
        if category:
            must_conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category.value))
            )

        qdrant_filter = Filter(must=must_conditions) if must_conditions else None

        # query_points replaces the deprecated search() in qdrant-client v1.x
        response = self._client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=limit * 2,          # over-fetch for recency reranking
            with_payload=True,
        )

        hit_list = response.points if hasattr(response, "points") else response

        # Rerank with recency decay
        scored: list[tuple[MemoryItem, float]] = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for hit in hit_list:
            mem_id = hit.payload.get("memory_id")
            if not mem_id or mem_id not in self._indexed:
                continue
            item = self._indexed[mem_id]
            cos_score = hit.score         # cosine already 0-1

            final_score = cos_score
            if recency_boost:
                try:
                    created = datetime.datetime.fromisoformat(item.created_at)
                    if created.tzinfo is None:
                        created = created.replace(tzinfo=datetime.timezone.utc)
                    age_days = (now - created).total_seconds() / 86400
                    decay = 0.5 ** (age_days / self.RECENCY_HALF_LIFE_DAYS)
                    final_score = cos_score * (1 + self.RECENCY_WEIGHT * decay)
                except (ValueError, AttributeError):
                    pass

            scored.append((item, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _stable_int_id(self, memory_id: str) -> int:
        """Convert string ID to a stable integer for Qdrant point IDs."""
        return abs(hash(memory_id)) % (2 ** 31)

    def remove(self, memory_id: str) -> None:
        """Remove a memory from the vector index and the internal map."""
        if memory_id in self._indexed:
            del self._indexed[memory_id]
        if self._client:
            from qdrant_client.models import PointIdsList
            self._client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=PointIdsList(
                    points=[self._stable_int_id(memory_id)]
                ),
            )

"""
Memory Rollback Service.

Provides high-level orchestration for:
  1. Recording updates with contradiction scoring
  2. Querying full version histories
  3. Rolling back memories to any prior version
  4. Generating explainability notes for each contradiction
"""
from __future__ import annotations
from typing import Optional

from .versioned_store import VersionedMemoryStore
from .contradiction_scorer import ContradictionScorer
from .versioning_schemas import (
    VersionedMemoryHistory, MemorySnapshot, MemoryDiff,
    VersionTrigger
)
from .schemas import MemoryItem, MemoryCategory


class MemoryRollbackService:
    """
    High-level service for memory versioning, contradiction resolution,
    and historical restoration.

    Usage:
        store = VersionedMemoryStore()
        svc = MemoryRollbackService(store)

        # Add a memory
        mem = svc.add_memory("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL, topic_key="location")

        # Update with contradiction scoring
        svc.update_memory(mem.id, "User lives in Zurich", topic_key="location")

        # View history
        history = svc.get_history(mem.id)

        # Roll back to v1
        svc.rollback(mem.id, to_version=1)
    """

    def __init__(self, store: Optional[VersionedMemoryStore] = None):
        self._store = store or VersionedMemoryStore()
        self._scorer = ContradictionScorer()

    @property
    def store(self) -> VersionedMemoryStore:
        return self._store

    # ------------------------------------------------------------------
    # Memory Lifecycle
    # ------------------------------------------------------------------

    def add_memory(
        self,
        content: str,
        category: MemoryCategory,
        user_id: str = "default_user",
        source_agent: str = "personal_assistant",
        session_id: Optional[str] = None,
        topic_key: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryItem:
        """Add a new memory and record its initial snapshot."""
        return self._store.add(
            content=content,
            category=category,
            user_id=user_id,
            source_agent=source_agent,
            session_id=session_id,
            topic_key=topic_key,
            metadata=metadata or {},
        )

    def update_memory(
        self,
        memory_id: str,
        new_content: str,
        category: Optional[MemoryCategory] = None,
        topic_key: str = "",
        triggered_by: str = "user",
        metadata: Optional[dict] = None,
    ) -> Optional[MemoryItem]:
        """
        Update a memory with full contradiction scoring.
        Automatically computes ContradictionSeverity and records a MemoryDiff.
        """
        existing = self._store.get(memory_id)
        if not existing:
            return None

        conf, explanation = self._scorer.score(
            existing_content=existing.content,
            new_content=new_content,
            category=existing.category,
            topic_key=topic_key or (existing.topic_key or ""),
        )

        return self._store.update(
            memory_id=memory_id,
            content=new_content,
            category=category,
            metadata=metadata,
            trigger=VersionTrigger.AUTO_CONTRADICTION if conf >= 0.4 else VersionTrigger.USER_UPDATE,
            triggered_by=triggered_by,
            contradiction_confidence=conf,
            explanation=explanation,
        )

    def rollback(
        self,
        memory_id: str,
        to_version: int,
        triggered_by: str = "user",
    ) -> Optional[MemoryItem]:
        """Roll back a memory to a specific historical version."""
        return self._store.rollback(memory_id, to_version, triggered_by)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_history(self, memory_id: str) -> Optional[VersionedMemoryHistory]:
        """Return the complete version history for a memory."""
        return self._store.get_history(memory_id)

    def get_snapshots(self, memory_id: str) -> list[MemorySnapshot]:
        """Return ordered list of all snapshots for a memory."""
        return self._store.list_snapshots(memory_id)

    def get_diffs(self, memory_id: str) -> list[MemoryDiff]:
        """Return all diffs (change records) for a memory."""
        return self._store.list_diffs(memory_id)

    def get_contradictions(self, memory_id: str, min_confidence: float = 0.4) -> list[MemoryDiff]:
        """Return only diffs with contradiction confidence >= threshold."""
        return [
            d for d in self._store.list_diffs(memory_id)
            if d.contradiction_confidence >= min_confidence
        ]

    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Return the current state of a memory."""
        return self._store.get(memory_id)

    def get_all_memories(self, user_id: Optional[str] = None) -> list[MemoryItem]:
        """Return all current memories, optionally filtered by user."""
        return self._store.get_all(user_id=user_id)

"""
Memory Version History Store.

Wraps the base MemoryStore to add immutable snapshot tracking.
Every ADD or UPDATE operation records a MemorySnapshot and a MemoryDiff.
Supports rollback to any historical version.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from .store import MemoryStore
from .schemas import MemoryItem, MemoryCategory
from .versioning_schemas import (
    MemorySnapshot, MemoryDiff, VersionedMemoryHistory,
    VersionTrigger, ContradictionSeverity
)


class VersionedMemoryStore(MemoryStore):
    """
    Extends MemoryStore with immutable snapshot history tracking.

    For every add() and update() call, a MemorySnapshot is recorded.
    MemoryDiffs are computed between consecutive snapshots.
    Supports full rollback to any prior version.
    """

    def __init__(self):
        super().__init__()
        self._histories: dict[str, VersionedMemoryHistory] = {}

    # ------------------------------------------------------------------
    # Override add() to record initial snapshot
    # ------------------------------------------------------------------

    def add(
        self,
        content: str,
        category: MemoryCategory,
        user_id: str = "default_user",
        source_agent: str = "personal_assistant",
        session_id: Optional[str] = None,
        topic_key: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> MemoryItem:
        item = super().add(
            content=content,
            category=category,
            user_id=user_id,
            source_agent=source_agent,
            session_id=session_id,
            topic_key=topic_key,
            metadata=metadata,
        )
        self._record_snapshot(item, VersionTrigger.INITIAL, source_agent)
        return item

    # ------------------------------------------------------------------
    # Override update() to record new snapshot + diff
    # ------------------------------------------------------------------

    def update(
        self,
        memory_id: str,
        content: str,
        category: Optional[MemoryCategory] = None,
        metadata: Optional[dict] = None,
        trigger: VersionTrigger = VersionTrigger.USER_UPDATE,
        triggered_by: str = "system",
        contradiction_confidence: float = 0.0,
        explanation: Optional[str] = None,
    ) -> Optional[MemoryItem]:
        item = super().update(memory_id, content, category, metadata)
        if item:
            self._record_snapshot(item, trigger, triggered_by, contradiction_confidence, explanation)
        return item

    # ------------------------------------------------------------------
    # Version History API
    # ------------------------------------------------------------------

    def get_history(self, memory_id: str) -> Optional[VersionedMemoryHistory]:
        """Return the full version history for a given memory ID."""
        return self._histories.get(memory_id)

    def list_snapshots(self, memory_id: str) -> list[MemorySnapshot]:
        """List all snapshots for a given memory, oldest first."""
        hist = self._histories.get(memory_id)
        return hist.snapshots if hist else []

    def list_diffs(self, memory_id: str) -> list[MemoryDiff]:
        """List all diffs for a given memory, oldest first."""
        hist = self._histories.get(memory_id)
        return hist.diffs if hist else []

    def rollback(
        self,
        memory_id: str,
        to_version: int,
        triggered_by: str = "user"
    ) -> Optional[MemoryItem]:
        """
        Roll back a memory to a specific historical version.
        Creates a new snapshot recording the rollback event.
        Returns the updated MemoryItem or None if version/memory not found.
        """
        hist = self._histories.get(memory_id)
        if not hist:
            return None
        target_snap = hist.get_snapshot(to_version)
        if not target_snap:
            return None

        return self.update(
            memory_id=memory_id,
            content=target_snap.content,
            trigger=VersionTrigger.ROLLBACK,
            triggered_by=triggered_by,
            contradiction_confidence=0.0,
            explanation=f"Rolled back to v{to_version}: '{target_snap.content[:60]}...'"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_snapshot(
        self,
        item: MemoryItem,
        trigger: VersionTrigger,
        triggered_by: str,
        contradiction_confidence: float = 0.0,
        explanation: Optional[str] = None,
    ) -> None:
        """Append a new snapshot to this memory's history and compute diff if needed."""
        hist = self._histories.setdefault(
            item.id, VersionedMemoryHistory(memory_id=item.id)
        )
        new_version = len(hist.snapshots) + 1
        snap = MemorySnapshot(
            memory_id=item.id,
            version=new_version,
            content=item.content,
            trigger=trigger,
            triggered_by=triggered_by,
            metadata=dict(item.metadata),
        )
        hist.snapshots.append(snap)

        # Compute diff from the previous snapshot
        if len(hist.snapshots) >= 2:
            prev_snap = hist.snapshots[-2]
            diff = MemoryDiff.from_snapshots(
                from_snap=prev_snap,
                to_snap=snap,
                contradiction_confidence=contradiction_confidence,
                explanation=explanation,
            )
            hist.diffs.append(diff)

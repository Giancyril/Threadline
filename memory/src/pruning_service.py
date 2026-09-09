"""
Background Memory Pruning & Archival Service.

Periodically scans the MemoryStore for:
1. EPHEMERAL memories past their expires_at timestamp -> archives them.
2. PROJECT_BOUND memories past their expires_at -> moves to archive with a summary note.
3. PERMANENT memories -> never pruned.

Can be run manually (prune_now()) or as a scheduled background thread.
"""
from __future__ import annotations
import threading
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from .store import MemoryStore
from .schemas import MemoryItem
from .temporal_schemas import LongevityTier

logger = logging.getLogger(__name__)


class MemoryPruningService:
    """
    Background archival and pruning service for temporal memory management.

    Usage:
        pruner = MemoryPruningService(store)
        pruner.start(interval_seconds=3600)   # run every hour
        # ... later ...
        pruner.stop()

    Or run once manually:
        results = pruner.prune_now()
    """

    def __init__(self, store: MemoryStore):
        self._store = store
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._archived_log: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def prune_now(self) -> dict:
        """
        Run a single pruning cycle synchronously.
        Returns a summary dict with counts of archived/pruned memories.
        """
        now = datetime.now(timezone.utc)
        all_memories = self._store.get_all()

        archived_ephemeral: list[str] = []
        archived_project: list[str] = []
        skipped_permanent: int = 0

        for mem in all_memories:
            tier = mem.metadata.get("longevity_tier", LongevityTier.PERMANENT.value)
            expires_at_str = mem.metadata.get("expires_at", None)

            if tier == LongevityTier.PERMANENT.value:
                skipped_permanent += 1
                continue

            if not expires_at_str:
                continue

            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            if now > expires_at:
                # Archive: mark as is_archived in metadata (soft delete)
                self._store.update(
                    memory_id=mem.id,
                    content=mem.content,
                    metadata={
                        **mem.metadata,
                        "is_archived": True,
                        "archived_at": now.isoformat(),
                        "archive_reason": f"Expired {tier} memory"
                    }
                )
                self._archived_log.append({
                    "id": mem.id,
                    "tier": tier,
                    "content": mem.content[:80],
                    "archived_at": now.isoformat(),
                })

                if tier == LongevityTier.EPHEMERAL.value:
                    archived_ephemeral.append(mem.id)
                else:
                    archived_project.append(mem.id)

                logger.info(f"[Pruner] Archived {tier} memory: {mem.id} ('{mem.content[:40]}...')")

        summary = {
            "pruned_at": now.isoformat(),
            "archived_ephemeral": len(archived_ephemeral),
            "archived_project_bound": len(archived_project),
            "skipped_permanent": skipped_permanent,
            "total_archived": len(archived_ephemeral) + len(archived_project),
        }
        logger.info(f"[Pruner] Cycle complete: {summary}")
        return summary

    def get_archived_log(self) -> list[dict]:
        """Return the log of all archived memories from this session."""
        return list(self._archived_log)

    def get_active_memories(self) -> list[MemoryItem]:
        """Return only non-archived memories from the store."""
        return [
            m for m in self._store.get_all()
            if not m.metadata.get("is_archived", False)
        ]

    # ------------------------------------------------------------------
    # Background thread lifecycle
    # ------------------------------------------------------------------

    def start(self, interval_seconds: float = 3600.0) -> None:
        """Start the background pruning thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("[Pruner] Already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(interval_seconds,),
            daemon=True,
            name="MemoryPruner"
        )
        self._thread.start()
        logger.info(f"[Pruner] Started background pruning every {interval_seconds}s")

    def stop(self) -> None:
        """Stop the background pruning thread gracefully."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[Pruner] Stopped.")

    def _run_loop(self, interval_seconds: float) -> None:
        while not self._stop_event.is_set():
            try:
                self.prune_now()
            except Exception as exc:
                logger.error(f"[Pruner] Error in pruning cycle: {exc}")
            self._stop_event.wait(timeout=interval_seconds)

"""
Tests for Memory Versioning & Contradiction system:
- MemorySnapshot creation and version ordering
- MemoryDiff contradiction scoring
- VersionedMemoryStore immutable history
- ContradictionScorer heuristics
- MemoryRollbackService full workflow
"""
import pytest
from memory.src.versioning_schemas import (
    MemorySnapshot, MemoryDiff, VersionedMemoryHistory,
    VersionTrigger, ContradictionSeverity
)
from memory.src.versioned_store import VersionedMemoryStore
from memory.src.contradiction_scorer import ContradictionScorer
from memory.src.rollback_service import MemoryRollbackService
from memory.src.schemas import MemoryCategory


# -----------------------------------------------------------------------
# 1. MemorySnapshot & MemoryDiff schemas
# -----------------------------------------------------------------------

class TestVersioningSchemas:
    def test_snapshot_auto_id(self):
        snap = MemorySnapshot(memory_id="mem_abc", version=1, content="User lives in Tokyo")
        assert snap.snapshot_id.startswith("snap_")
        assert snap.version == 1

    def test_diff_severity_high(self):
        s1 = MemorySnapshot(memory_id="m1", version=1, content="User lives in Tokyo")
        s2 = MemorySnapshot(memory_id="m1", version=2, content="User moved to Zurich")
        diff = MemoryDiff.from_snapshots(s1, s2, contradiction_confidence=0.9)
        assert diff.contradiction_severity == ContradictionSeverity.HIGH

    def test_diff_severity_medium(self):
        s1 = MemorySnapshot(memory_id="m1", version=1, content="User prefers Python")
        s2 = MemorySnapshot(memory_id="m1", version=2, content="User switched to Rust")
        diff = MemoryDiff.from_snapshots(s1, s2, contradiction_confidence=0.6)
        assert diff.contradiction_severity == ContradictionSeverity.MEDIUM

    def test_diff_severity_none(self):
        s1 = MemorySnapshot(memory_id="m1", version=1, content="User prefers Python")
        s2 = MemorySnapshot(memory_id="m1", version=2, content="User prefers Python 3.14")
        diff = MemoryDiff.from_snapshots(s1, s2, contradiction_confidence=0.0)
        assert diff.contradiction_severity == ContradictionSeverity.NONE

    def test_history_current_version(self):
        hist = VersionedMemoryHistory(memory_id="m1")
        hist.snapshots.append(MemorySnapshot(memory_id="m1", version=1, content="v1"))
        hist.snapshots.append(MemorySnapshot(memory_id="m1", version=2, content="v2"))
        assert hist.current_version == 2
        assert hist.latest_content == "v2"


# -----------------------------------------------------------------------
# 2. ContradictionScorer
# -----------------------------------------------------------------------

class TestContradictionScorer:
    def setup_method(self):
        self.scorer = ContradictionScorer()

    def test_identical_content_is_zero(self):
        score, _ = self.scorer.score("User lives in Tokyo", "User lives in Tokyo", MemoryCategory.BIOGRAPHICAL)
        assert score == 0.0

    def test_location_change_is_high_confidence(self):
        score, explanation = self.scorer.score(
            "User lives in Tokyo", "User moved to Zurich",
            MemoryCategory.BIOGRAPHICAL, topic_key="location"
        )
        assert score >= 0.6
        assert "moved" in explanation.lower() or "Contradiction" in explanation

    def test_no_signal_but_different_content(self):
        score, _ = self.scorer.score(
            "User prefers dark mode", "User prefers light mode",
            MemoryCategory.PREFERENCES
        )
        assert 0.0 <= score <= 1.0

    def test_high_overlap_reduces_score(self):
        score, _ = self.scorer.score(
            "User is a Senior AI Engineer",
            "User is a Staff AI Engineer",
            MemoryCategory.BIOGRAPHICAL, topic_key="profession"
        )
        # High overlap between these two means lower contradiction than a drastic change
        assert score < 0.9

    def test_no_longer_signal_boosts_score(self):
        score, explanation = self.scorer.score(
            "User works at Google", "User no longer works at Google",
            MemoryCategory.BIOGRAPHICAL, topic_key="employer"
        )
        assert score >= 0.6
        assert "Change signal" in explanation or "no longer" in explanation.lower()


# -----------------------------------------------------------------------
# 3. VersionedMemoryStore
# -----------------------------------------------------------------------

class TestVersionedMemoryStore:
    def setup_method(self):
        self.store = VersionedMemoryStore()

    def test_add_records_initial_snapshot(self):
        mem = self.store.add("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL)
        snaps = self.store.list_snapshots(mem.id)
        assert len(snaps) == 1
        assert snaps[0].version == 1
        assert snaps[0].trigger == VersionTrigger.INITIAL

    def test_update_adds_new_snapshot(self):
        mem = self.store.add("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL)
        self.store.update(memory_id=mem.id, content="User lives in Zurich")
        snaps = self.store.list_snapshots(mem.id)
        assert len(snaps) == 2
        assert snaps[-1].content == "User lives in Zurich"

    def test_update_creates_diff(self):
        mem = self.store.add("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL)
        self.store.update(memory_id=mem.id, content="User lives in Zurich", contradiction_confidence=0.8)
        diffs = self.store.list_diffs(mem.id)
        assert len(diffs) == 1
        assert diffs[0].contradiction_confidence == 0.8

    def test_rollback_restores_content(self):
        mem = self.store.add("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL)
        self.store.update(memory_id=mem.id, content="User lives in Zurich")
        restored = self.store.rollback(mem.id, to_version=1)
        assert restored is not None
        assert restored.content == "User lives in Tokyo"

    def test_rollback_creates_new_snapshot(self):
        mem = self.store.add("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL)
        self.store.update(memory_id=mem.id, content="User lives in Zurich")
        self.store.rollback(mem.id, to_version=1)
        snaps = self.store.list_snapshots(mem.id)
        assert len(snaps) == 3  # Initial + update + rollback
        assert snaps[-1].trigger == VersionTrigger.ROLLBACK


# -----------------------------------------------------------------------
# 4. MemoryRollbackService full workflow
# -----------------------------------------------------------------------

class TestMemoryRollbackService:
    def setup_method(self):
        self.svc = MemoryRollbackService()

    def test_full_lifecycle(self):
        mem = self.svc.add_memory("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL, topic_key="location")
        self.svc.update_memory(mem.id, "User moved to Zurich", topic_key="location")
        history = self.svc.get_history(mem.id)
        assert history.current_version == 2
        contradictions = self.svc.get_contradictions(mem.id)
        assert len(contradictions) >= 1

    def test_rollback_service(self):
        mem = self.svc.add_memory("User works at Google", MemoryCategory.BIOGRAPHICAL, topic_key="employer")
        self.svc.update_memory(mem.id, "User now works at OpenAI", topic_key="employer")
        restored = self.svc.rollback(mem.id, to_version=1)
        assert restored.content == "User works at Google"

    def test_get_snapshots(self):
        mem = self.svc.add_memory("User prefers Python", MemoryCategory.PREFERENCES)
        self.svc.update_memory(mem.id, "User prefers Rust")
        snaps = self.svc.get_snapshots(mem.id)
        assert len(snaps) == 2
        assert snaps[0].content == "User prefers Python"
        assert snaps[1].content == "User prefers Rust"

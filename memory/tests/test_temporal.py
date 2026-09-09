"""
Tests for temporal memory dynamics:
- Longevity heuristic classifier accuracy
- Non-linear decay curve correctness (ephemeral vs permanent)
- MemoryPruningService archival logic
"""
import pytest
from datetime import datetime, timezone, timedelta

from memory.src.temporal_schemas import LongevityTier, TemporalMetadata, DecayCurveEngine
from memory.src.extractor import MemoryExtractor, LongevityClassifier
from memory.src.schemas import MemoryCategory, MemoryItem
from memory.src.store import MemoryStore
from memory.src.pruning_service import MemoryPruningService


# -----------------------------------------------------------------------
# 1. LongevityClassifier tests
# -----------------------------------------------------------------------

class TestLongevityClassifier:
    def setup_method(self):
        self.clf = LongevityClassifier()

    def test_biographical_is_permanent(self):
        tier = self.clf.classify("User lives in Tokyo", MemoryCategory.BIOGRAPHICAL)
        assert tier == LongevityTier.PERMANENT

    def test_ephemeral_overrides_biographical(self):
        tier = self.clf.classify("User is eating lunch today", MemoryCategory.BIOGRAPHICAL)
        assert tier == LongevityTier.EPHEMERAL

    def test_project_content_is_project_bound(self):
        tier = self.clf.classify("User is working on a sprint", MemoryCategory.PROJECTS)
        assert tier == LongevityTier.PROJECT_BOUND

    def test_preference_is_permanent_by_default(self):
        tier = self.clf.classify("User prefers dark mode", MemoryCategory.PREFERENCES)
        assert tier == LongevityTier.PERMANENT

    def test_comm_style_is_permanent(self):
        tier = self.clf.classify("User communication preference: be concise", MemoryCategory.COMMUNICATION_STYLE)
        assert tier == LongevityTier.PERMANENT

    def test_right_now_is_ephemeral(self):
        tier = self.clf.classify("User is right now in a meeting", MemoryCategory.PROJECTS)
        assert tier == LongevityTier.EPHEMERAL

    def test_branch_signals_project_bound(self):
        tier = self.clf.classify("User is working on branch feature/auth", MemoryCategory.PROJECTS)
        assert tier == LongevityTier.PROJECT_BOUND


# -----------------------------------------------------------------------
# 2. DecayCurveEngine tests
# -----------------------------------------------------------------------

class TestDecayCurveEngine:
    def test_ephemeral_at_zero_hours_is_one(self):
        score = DecayCurveEngine.compute_decay_score(LongevityTier.EPHEMERAL, age_hours=0)
        assert abs(score - 1.0) < 0.001

    def test_ephemeral_at_24h_is_half(self):
        score = DecayCurveEngine.compute_decay_score(LongevityTier.EPHEMERAL, age_hours=24)
        assert abs(score - 0.5) < 0.01

    def test_ephemeral_at_96h_is_near_zero(self):
        score = DecayCurveEngine.compute_decay_score(LongevityTier.EPHEMERAL, age_hours=96)
        assert score < 0.07

    def test_permanent_at_one_year_is_near_full(self):
        score = DecayCurveEngine.compute_decay_score(LongevityTier.PERMANENT, age_hours=8760)
        assert score > 0.85  # Should be ~0.86 at 1 year (half-life ~5 years)

    def test_permanent_at_zero_is_one(self):
        score = DecayCurveEngine.compute_decay_score(LongevityTier.PERMANENT, age_hours=0)
        assert abs(score - 1.0) < 0.001

    def test_project_at_21_days_is_half(self):
        # Sigmoid inflection at 21 days
        score = DecayCurveEngine.compute_decay_score(LongevityTier.PROJECT_BOUND, age_hours=21 * 24)
        assert 0.45 < score < 0.55

    def test_project_at_60_days_is_low(self):
        score = DecayCurveEngine.compute_decay_score(LongevityTier.PROJECT_BOUND, age_hours=60 * 24)
        assert score < 0.15

    def test_recency_boosted_score_is_higher_when_fresh(self):
        base = 0.7
        score_fresh = DecayCurveEngine.recency_boosted_score(base, LongevityTier.EPHEMERAL, age_hours=0)
        score_old = DecayCurveEngine.recency_boosted_score(base, LongevityTier.EPHEMERAL, age_hours=96)
        assert score_fresh > score_old


# -----------------------------------------------------------------------
# 3. TemporalMetadata defaults
# -----------------------------------------------------------------------

class TestTemporalMetadata:
    def test_ephemeral_expires_in_1_day(self):
        meta = TemporalMetadata.calculate_defaults(LongevityTier.EPHEMERAL)
        expires = datetime.fromisoformat(meta.expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        delta = expires - datetime.now(timezone.utc)
        assert 0 < delta.total_seconds() < 86400 * 1.1

    def test_project_bound_expires_in_45_days(self):
        meta = TemporalMetadata.calculate_defaults(LongevityTier.PROJECT_BOUND)
        expires = datetime.fromisoformat(meta.expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        delta = expires - datetime.now(timezone.utc)
        assert 0 < delta.days <= 46

    def test_permanent_has_no_expiry(self):
        meta = TemporalMetadata.calculate_defaults(LongevityTier.PERMANENT)
        assert meta.expires_at is None


# -----------------------------------------------------------------------
# 4. MemoryPruningService tests
# -----------------------------------------------------------------------

class TestMemoryPruningService:
    def _make_expired_memory(self, store: MemoryStore, tier: str) -> MemoryItem:
        """Add a memory that is already past its expiry time."""
        past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        item = store.add(
            content=f"Test {tier} memory (expired)",
            category=MemoryCategory.PREFERENCES,
            metadata={"longevity_tier": tier, "expires_at": past},
        )
        return item

    def test_prune_archives_expired_ephemeral(self):
        store = MemoryStore()
        mem = self._make_expired_memory(store, LongevityTier.EPHEMERAL.value)
        pruner = MemoryPruningService(store)
        result = pruner.prune_now()
        assert result["archived_ephemeral"] == 1
        archived = store.get(mem.id)
        assert archived.metadata.get("is_archived") is True

    def test_prune_skips_permanent_memories(self):
        store = MemoryStore()
        store.add(
            content="User lives in Tokyo",
            category=MemoryCategory.BIOGRAPHICAL,
            metadata={"longevity_tier": LongevityTier.PERMANENT.value},
        )
        pruner = MemoryPruningService(store)
        result = pruner.prune_now()
        assert result["archived_ephemeral"] == 0
        assert result["skipped_permanent"] == 1

    def test_get_active_memories_excludes_archived(self):
        store = MemoryStore()
        self._make_expired_memory(store, LongevityTier.EPHEMERAL.value)
        store.add(content="User prefers Python", category=MemoryCategory.PREFERENCES,
                  metadata={"longevity_tier": LongevityTier.PERMANENT.value})
        pruner = MemoryPruningService(store)
        pruner.prune_now()
        active = pruner.get_active_memories()
        assert len(active) == 1
        assert "Python" in active[0].content

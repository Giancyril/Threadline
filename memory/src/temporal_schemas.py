"""
Temporal Memory Dynamics & Longevity calibration schemas.
Includes non-linear decay curve engine tailored to each LongevityTier.
"""
from enum import Enum
from typing import Optional
from datetime import datetime, timezone, timedelta
import math
from pydantic import BaseModel, Field


class LongevityTier(str, Enum):
    EPHEMERAL = "ephemeral"          # Half-life: 24 hours (e.g. today's lunch, temporary mood)
    PROJECT_BOUND = "project_bound"  # Half-life: 30 days (e.g. current sprint task, active branch)
    PERMANENT = "permanent"          # Half-life: Infinite (e.g. core identity, primary tech stack)


class TemporalMetadata(BaseModel):
    longevity_tier: LongevityTier = Field(default=LongevityTier.PERMANENT)
    decay_half_life_days: float = Field(default=90.0)
    expires_at: Optional[str] = None
    is_archived: bool = False
    access_count: int = 0
    last_accessed_at: Optional[str] = None

    @classmethod
    def calculate_defaults(cls, tier: LongevityTier) -> "TemporalMetadata":
        now = datetime.now(timezone.utc)
        if tier == LongevityTier.EPHEMERAL:
            expiry = (now + timedelta(days=1)).isoformat()
            return cls(longevity_tier=tier, decay_half_life_days=1.0, expires_at=expiry)
        elif tier == LongevityTier.PROJECT_BOUND:
            expiry = (now + timedelta(days=45)).isoformat()
            return cls(longevity_tier=tier, decay_half_life_days=30.0, expires_at=expiry)
        else:
            return cls(longevity_tier=tier, decay_half_life_days=9999.0, expires_at=None)


class DecayCurveEngine:
    """
    Non-linear memory decay scoring engine.

    Each LongevityTier uses a different decay model:
    - EPHEMERAL: Steep exponential decay (rapid drop over hours, near-zero by day 2)
    - PROJECT_BOUND: Sigmoid decay curve (gradual slope, steep drop around 30 days)
    - PERMANENT: Near-flat decay (memory stays highly relevant, tiny time penalty)

    All return a float in [0.0, 1.0] where 1.0 = perfectly fresh.
    """

    @staticmethod
    def compute_decay_score(tier: LongevityTier, age_hours: float) -> float:
        """
        Returns a decay multiplier [0.0, 1.0] for a memory of given age.

        Args:
            tier: The LongevityTier assigned to the memory.
            age_hours: How many hours old the memory is.

        Returns:
            float: Decay score between 0.0 (fully stale) and 1.0 (fully fresh).
        """
        if tier == LongevityTier.PERMANENT:
            return DecayCurveEngine._permanent_decay(age_hours)
        elif tier == LongevityTier.EPHEMERAL:
            return DecayCurveEngine._ephemeral_decay(age_hours)
        else:
            return DecayCurveEngine._project_bound_decay(age_hours)

    @staticmethod
    def _ephemeral_decay(age_hours: float) -> float:
        """
        Steep exponential decay.
        Half-life = 24 hours. Score ~0.5 at 24h, ~0.05 at 96h.
        """
        half_life_hours = 24.0
        return math.exp(-0.693 * age_hours / half_life_hours)

    @staticmethod
    def _project_bound_decay(age_hours: float) -> float:
        """
        Sigmoid-shaped decay.
        Memory stays mostly relevant for ~21 days, then drops off fast by day 45.
        Uses: 1 / (1 + exp((age_days - 21) / 7))
        """
        age_days = age_hours / 24.0
        inflection_days = 21.0
        steepness = 7.0
        return 1.0 / (1.0 + math.exp((age_days - inflection_days) / steepness))

    @staticmethod
    def _permanent_decay(age_hours: float) -> float:
        """
        Near-flat decay: minimal drop over years.
        Half-life effectively 5 years (43,800 hours).
        Score is ~0.99 at 1 year.
        """
        half_life_hours = 43_800.0  # ~5 years
        return math.exp(-0.693 * age_hours / half_life_hours)

    @staticmethod
    def recency_boosted_score(
        base_score: float,
        tier: LongevityTier,
        age_hours: float,
        recency_weight: float = 0.15,
    ) -> float:
        """
        Applies decay-aware recency boost on top of a cosine similarity base_score.
        Final score = base_score * (1 + recency_weight * decay)
        """
        decay = DecayCurveEngine.compute_decay_score(tier, age_hours)
        return base_score * (1.0 + recency_weight * decay)

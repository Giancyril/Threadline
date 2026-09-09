"""
Temporal Memory Dynamics & Longevity calibration schemas.
"""
from enum import Enum
from typing import Optional
from datetime import datetime, timezone, timedelta
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

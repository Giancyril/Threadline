"""
Semantic Drift & Topic Clustering Schemas.

Models for tracking temporal topic shifts, cluster centroids,
drift velocities, and preference divergence alerts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TopicCluster(BaseModel):
    """Represents a coherent cluster of memories grouped by semantic topic."""
    cluster_id: str
    name: str
    keywords: List[str] = Field(default_factory=list)
    memory_ids: List[str] = Field(default_factory=list)
    centroid: Optional[List[float]] = None
    cohesion_score: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriftPoint(BaseModel):
    """A timestamped measurement of semantic center distance and movement."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    window_label: str
    drift_distance: float = Field(default=0.0, ge=0.0)
    drift_velocity: float = Field(default=0.0)  # Rate of change per hour/day
    active_cluster_count: int = 0
    divergence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dominant_topic: Optional[str] = None


class DivergenceAlert(BaseModel):
    """Alert triggered when user's preferences or project scope deviates significantly."""
    alert_id: str
    topic: str
    previous_preference: str
    current_preference: str
    divergence_score: float = Field(ge=0.0, le=1.0)
    severity: str = "medium"  # low, medium, high
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recommendation: str = ""
    acknowledged: bool = False


class DriftAnalysisSummary(BaseModel):
    """Aggregate analysis across all memories."""
    total_memories: int = 0
    clusters: List[TopicCluster] = Field(default_factory=list)
    drift_points: List[DriftPoint] = Field(default_factory=list)
    divergence_alerts: List[DivergenceAlert] = Field(default_factory=list)
    overall_drift_status: str = "stable"  # stable, drifting, volatile
    mean_velocity: float = 0.0

"""
Sliding-Window Centroid Drift Calculator.

Computes semantic centroid trajectories across temporal windows,
measuring drift distance, velocity, and divergence in user context over time.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Sequence
from memory.src.drift_schemas import DriftPoint


def cosine_distance(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Calculates cosine distance 1 - cos(theta) in range [0.0, 2.0]."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    
    cos_sim = dot / (norm_a * norm_b)
    # Clamp to [-1.0, 1.0] for numerical stability
    cos_sim = max(-1.0, min(1.0, cos_sim))
    return float(1.0 - cos_sim)


def compute_centroid(vectors: Sequence[Sequence[float]]) -> List[float]:
    """Computes arithmetic mean vector across a collection of vectors."""
    if not vectors or not vectors[0]:
        return []
    
    dim = len(vectors[0])
    count = len(vectors)
    sums = [0.0] * dim
    
    for vec in vectors:
        if len(vec) == dim:
            for i in range(dim):
                sums[i] += vec[i]
                
    return [s / count for s in sums]


class DriftCalculator:
    """
    Analyzes sequences of embedded memories partitioned into temporal windows
    to compute centroid migration and drift velocity.
    """
    def __init__(self, velocity_threshold: float = 0.35):
        self.velocity_threshold = velocity_threshold

    def calculate_window_drifts(
        self,
        windows: List[Dict[str, Any]]
    ) -> List[DriftPoint]:
        """
        windows: list of dicts with keys:
          - 'label': str (e.g. 'Window 1', 'Day 1')
          - 'timestamp': datetime
          - 'embeddings': List[List[float]]
          - 'cluster_count': Optional[int]
          - 'dominant_topic': Optional[str]
        """
        if not windows:
            return []

        drift_points: List[DriftPoint] = []
        prev_centroid: Optional[List[float]] = None
        prev_time: Optional[datetime] = None

        for idx, win in enumerate(windows):
            ts = win.get("timestamp") or datetime.now(timezone.utc)
            label = win.get("label", f"Window {idx + 1}")
            embeddings = win.get("embeddings", [])
            clusters = win.get("cluster_count", 1)
            topic = win.get("dominant_topic", "General")

            if not embeddings:
                drift_points.append(
                    DriftPoint(
                        timestamp=ts,
                        window_label=label,
                        drift_distance=0.0,
                        drift_velocity=0.0,
                        active_cluster_count=clusters,
                        divergence_score=0.0,
                        dominant_topic=topic
                    )
                )
                continue

            current_centroid = compute_centroid(embeddings)

            if prev_centroid is None:
                # Baseline window
                drift_dist = 0.0
                velocity = 0.0
                divergence = 0.0
            else:
                drift_dist = cosine_distance(prev_centroid, current_centroid)
                hours_diff = 1.0
                if prev_time:
                    delta_seconds = abs((ts - prev_time).total_seconds())
                    hours_diff = max(0.1, delta_seconds / 3600.0)
                
                # Velocity normalized per 24 hours
                velocity = float(drift_dist / (hours_diff / 24.0)) if hours_diff > 0 else 0.0
                # Divergence score normalized to [0, 1]
                divergence = min(1.0, drift_dist * 1.5)

            drift_points.append(
                DriftPoint(
                    timestamp=ts,
                    window_label=label,
                    drift_distance=round(drift_dist, 4),
                    drift_velocity=round(velocity, 4),
                    active_cluster_count=clusters,
                    divergence_score=round(divergence, 4),
                    dominant_topic=topic
                )
            )

            prev_centroid = current_centroid
            prev_time = ts

        return drift_points

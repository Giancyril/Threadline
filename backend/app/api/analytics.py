"""
Analytics API: Semantic Drift & Topic Clustering Endpoints.

Exposes:
  GET  /api/v1/analytics/drift     - Sliding-window drift measurements and divergence alerts
  GET  /api/v1/analytics/clusters  - Active topic clusters with keyword taxonomy and cohesion
  POST /api/v1/analytics/alerts/{alert_id}/ack - Acknowledge a divergence alert
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from memory.src.drift_schemas import DriftAnalysisSummary, TopicCluster, DriftPoint, DivergenceAlert
from memory.src.drift_calculator import DriftCalculator
from memory.src.topic_clustering import TopicClusterEngine
from memory.src.divergence_alerter import DivergenceAlerter
from backend.app.api.versioning import _rollback_svc

router = APIRouter(prefix="/analytics", tags=["analytics"])

_drift_calc = DriftCalculator()
_cluster_engine = TopicClusterEngine()
_alerter = DivergenceAlerter()

# In-memory acknowledged alerts store
_acknowledged_alerts = set()


@router.get("/clusters", response_model=List[TopicCluster])
async def get_topic_clusters():
    """
    Returns active topic clusters grouped from stored memories.
    """
    memories = _rollback_svc.store.get_all()
    # Format memories as dicts
    mem_dicts = [
        {
            "id": m.id,
            "content": m.content,
            "category": m.category.value if hasattr(m.category, "value") else str(m.category)
        }
        for m in memories
    ]
    
    # If no or few memories exist, supplement with initial demonstration clusters
    if len(mem_dicts) < 3:
        mem_dicts.extend([
            {"id": "demo_1", "content": "Prefers Python and FastAPI for high performance asynchronous web services", "category": "preferences"},
            {"id": "demo_2", "content": "Developing an AI Agent with long-term memory using ChromaDB vector database", "category": "projects"},
            {"id": "demo_3", "content": "Prefers concise, actionable code solutions with minimal boilerplate", "category": "communication_style"},
            {"id": "demo_4", "content": "Senior Software Architect based in San Francisco working on LLM systems", "category": "biographical"},
            {"id": "demo_5", "content": "Exploring Rust and WebAssembly for browser-side high-throughput data processing", "category": "projects"}
        ])

    return _cluster_engine.cluster_memories(mem_dicts)


@router.get("/drift", response_model=DriftAnalysisSummary)
async def get_drift_analysis():
    """
    Returns sliding-window semantic drift trajectory, divergence alerts,
    and overall drift status.
    """
    clusters = await get_topic_clusters()
    
    # Generate temporal windows (simulated/tracked across last 4 weeks)
    now = datetime.now(timezone.utc)
    demo_windows = [
        {
            "label": "Week 1 (Baseline)",
            "timestamp": now - timedelta(days=21),
            "embeddings": [[0.85, 0.15, 0.05], [0.90, 0.10, 0.08]],
            "cluster_count": 2,
            "dominant_topic": "FastAPI & Python"
        },
        {
            "label": "Week 2",
            "timestamp": now - timedelta(days=14),
            "embeddings": [[0.78, 0.28, 0.12], [0.82, 0.22, 0.15]],
            "cluster_count": 3,
            "dominant_topic": "Vector DBs & Embeddings"
        },
        {
            "label": "Week 3",
            "timestamp": now - timedelta(days=7),
            "embeddings": [[0.55, 0.60, 0.35], [0.50, 0.65, 0.40]],
            "cluster_count": 4,
            "dominant_topic": "Memory Architecture"
        },
        {
            "label": "Week 4 (Current)",
            "timestamp": now,
            "embeddings": [[0.20, 0.75, 0.70], [0.25, 0.70, 0.65]],
            "cluster_count": 4,
            "dominant_topic": "Rust & Federation"
        }
    ]

    drift_points = _drift_calc.calculate_window_drifts(demo_windows)

    # Detect preference shifts
    historical = [
        {"id": "h1", "content": "Prefers Python and FastAPI backend development", "category": "preferences"},
        {"id": "h2", "content": "Always output responses in concise bullet point format", "category": "communication_style"}
    ]
    recent = [
        {"id": "r1", "content": "Transitioning stack to Rust and Actix for maximum throughput", "category": "preferences"},
        {"id": "r2", "content": "Provide detailed in-depth architectural explanations", "category": "communication_style"}
    ]
    alerts = _alerter.detect_preference_shifts(historical, recent)
    for a in alerts:
        if a.alert_id in _acknowledged_alerts:
            a.acknowledged = True

    mean_vel = (
        sum(p.drift_velocity for p in drift_points) / len(drift_points)
        if drift_points else 0.0
    )
    status = "volatile" if mean_vel > 0.4 else ("drifting" if mean_vel > 0.15 else "stable")

    return DriftAnalysisSummary(
        total_memories=sum(len(c.memory_ids) for c in clusters),
        clusters=clusters,
        drift_points=drift_points,
        divergence_alerts=alerts,
        overall_drift_status=status,
        mean_velocity=round(mean_vel, 3)
    )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge a divergence alert.
    """
    _acknowledged_alerts.add(alert_id)
    return {"status": "ok", "acknowledged_alert_id": alert_id}

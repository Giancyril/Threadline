"""
Unit tests for Semantic Drift & Topic Clustering components:
- Cosine distance and centroid math
- Sliding-window drift calculator
- Topic cluster engine and keyword extraction
- Divergence alerter and preference shifts
"""
import pytest
from datetime import datetime, timezone, timedelta
from memory.src.drift_schemas import TopicCluster, DriftPoint, DivergenceAlert
from memory.src.drift_calculator import cosine_distance, compute_centroid, DriftCalculator
from memory.src.topic_clustering import extract_keywords, text_jaccard_similarity, TopicClusterEngine
from memory.src.divergence_alerter import DivergenceAlerter


def test_cosine_distance():
    # Identical vectors -> distance 0
    assert cosine_distance([1.0, 0.0], [1.0, 0.0]) == pytest.approx(0.0, abs=1e-5)
    # Orthogonal vectors -> distance 1.0
    assert cosine_distance([1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0, abs=1e-5)
    # Opposite vectors -> distance 2.0
    assert cosine_distance([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(2.0, abs=1e-5)
    # Empty / zero vector
    assert cosine_distance([], []) == 0.0
    assert cosine_distance([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_compute_centroid():
    vectors = [
        [1.0, 2.0, 3.0],
        [3.0, 2.0, 1.0],
    ]
    centroid = compute_centroid(vectors)
    assert centroid == [2.0, 2.0, 2.0]
    assert compute_centroid([]) == []


def test_drift_calculator_sliding_windows():
    calc = DriftCalculator()
    now = datetime.now(timezone.utc)
    
    windows = [
        {
            "label": "Week 1",
            "timestamp": now - timedelta(days=7),
            "embeddings": [[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]],
            "cluster_count": 1,
            "dominant_topic": "Frontend"
        },
        {
            "label": "Week 2",
            "timestamp": now,
            "embeddings": [[0.0, 1.0, 0.0], [0.1, 0.9, 0.0]],
            "cluster_count": 2,
            "dominant_topic": "Backend"
        }
    ]
    
    points = calc.calculate_window_drifts(windows)
    assert len(points) == 2
    assert points[0].drift_distance == 0.0  # Baseline
    assert points[1].drift_distance > 0.5   # Significant shift from frontend to backend
    assert points[1].active_cluster_count == 2
    assert points[1].dominant_topic == "Backend"


def test_topic_clustering_engine():
    engine = TopicClusterEngine(similarity_threshold=0.2)
    memories = [
        {"id": "m1", "content": "User prefers Python for data science and AI", "category": "preferences"},
        {"id": "m2", "content": "User builds machine learning models using Python and PyTorch", "category": "preferences"},
        {"id": "m3", "content": "Lives in Seattle and loves hiking in national parks", "category": "biographical"},
        {"id": "m4", "content": "Enjoys outdoor hiking and nature trails in Washington", "category": "biographical"},
    ]
    
    clusters = engine.cluster_memories(memories)
    assert len(clusters) >= 2
    
    # Check that m1 and m2 share cluster or are grouped
    cluster_for_m1 = next((c for c in clusters if "m1" in c.memory_ids), None)
    assert cluster_for_m1 is not None
    assert cluster_for_m1.cohesion_score > 0.0
    assert len(cluster_for_m1.keywords) > 0


def test_extract_keywords():
    text = "FastAPI backend services with PostgreSQL database and async SQLAlchemy"
    kw = extract_keywords(text, max_words=3)
    assert len(kw) <= 3
    assert any("fastapi" in k.lower() or "postgresql" in k.lower() for k in kw)


def test_divergence_alerter():
    alerter = DivergenceAlerter()
    
    historical = [
        {"id": "h1", "content": "User prefers concise responses with bullet points", "category": "communication_style"},
        {"id": "h2", "content": "Core tech stack is Python and FastAPI", "category": "preferences"}
    ]
    
    recent = [
        {"id": "r1", "content": "User now wants elaborate detailed explanations rather than bullet points", "category": "communication_style"},
        {"id": "r2", "content": "Transitioning all microservices from python to rust", "category": "preferences"}
    ]
    
    alerts = alerter.detect_preference_shifts(historical, recent)
    assert len(alerts) >= 1
    
    topics = [a.topic for a in alerts]
    assert "Programming Language" in topics or "Tone & Style" in topics
    
    for a in alerts:
        assert a.divergence_score >= 0.7
        assert a.recommendation != ""

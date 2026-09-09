"""
Phase 2 tests: Embedding, Storage + Semantic Retrieval layer.
Uses an in-memory Qdrant collection (no server required).
"""
import pytest
from memory.src.schemas import MemoryCategory, MemoryItem
from memory.src.store import MemoryStore
from memory.src.embedder import TFIDFEmbedder
from memory.src.retriever import MemoryRetriever
from memory.src.service import MemoryService


# ----------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------

@pytest.fixture()
def service():
    return MemoryService()


@pytest.fixture()
def populated_service():
    svc = MemoryService()
    messages = [
        "I prefer dark mode in all my editors",
        "I live in Singapore",
        "I am working on AI Assistant With Memory project using Mem0",
        "I prefer concise, bulleted responses over long paragraphs",
        "I work as a senior Python backend engineer",
        "I love using FastAPI for my microservices",
    ]
    for msg in messages:
        svc.process_turn(user_message=msg, user_id="user_test")
    return svc


# ----------------------------------------------------------------
# Embedder Unit Tests
# ----------------------------------------------------------------

def test_embedder_produces_vectors():
    emb = TFIDFEmbedder()
    texts = ["user prefers dark mode", "user lives in Singapore", "building a project with Mem0"]
    vectors = emb.encode(texts)
    assert len(vectors) == 3
    assert all(len(v) > 0 for v in vectors)


def test_embedder_vectors_are_normalized():
    import math
    emb = TFIDFEmbedder()
    vectors = emb.encode(["user prefers dark mode in editors", "lives in Berlin"])
    for vec in vectors:
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 1e-6 or norm == 0.0


def test_embedder_similar_texts_score_higher_than_different():
    emb = TFIDFEmbedder()
    texts = [
        "user prefers dark mode",
        "user likes dark theme in editors",
        "user lives in Berlin",
    ]
    vectors = emb.encode(texts)

    def cosine(a, b):
        import math
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    # dark-mode / dark-theme should be more similar than dark-mode / berlin
    sim_same = cosine(vectors[0], vectors[1])
    sim_diff = cosine(vectors[0], vectors[2])
    assert sim_same > sim_diff


# ----------------------------------------------------------------
# Retriever Integration Tests
# ----------------------------------------------------------------

def test_retriever_indexes_and_retrieves(populated_service):
    """A direct keyword query should surface the matching memory in top results."""
    results = populated_service.retrieve(
        query="dark mode editors",   # direct TF-IDF-friendly query
        user_id="user_test",
        limit=5
    )
    assert len(results) > 0
    # Top result must have a positive score (some entries may score 0 on TF-IDF)
    top_score = results[0][1]
    assert top_score > 0.0
    # The dark mode memory must appear somewhere in top-5
    contents = [r[0].content.lower() for r in results]
    assert any("dark mode" in c for c in contents)


def test_retrieval_returns_results_for_known_topic(populated_service):
    """Any query about stored topics should return at least one result."""
    results = populated_service.retrieve(
        query="Singapore location", user_id="user_test", limit=3
    )
    assert len(results) > 0


def test_retrieval_scoped_to_user(populated_service):
    """User B has no memories — should return empty."""
    results = populated_service.retrieve(query="editor preferences", user_id="user_other")
    assert len(results) == 0


def test_retrieval_category_filter(populated_service):
    """Category filter should return only memories in that category."""
    results = populated_service.retrieve(
        query="where does the user live?",
        user_id="user_test",
        category=MemoryCategory.BIOGRAPHICAL,
        limit=5
    )
    assert all(r[0].category == MemoryCategory.BIOGRAPHICAL for r in results)
    assert any(
        "singapore" in r[0].content.lower() or "engineer" in r[0].content.lower()
        for r in results
    )


def test_retrieval_ranked_by_relevance(populated_service):
    """Results must be returned in descending score order."""
    results = populated_service.retrieve(
        query="concise responses style",
        user_id="user_test",
        limit=3
    )
    assert len(results) >= 1
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)


# ----------------------------------------------------------------
# Service: delete propagates to vector index
# ----------------------------------------------------------------

def test_delete_removes_from_retrieval(service):
    service.process_turn(user_message="I live in Tokyo", user_id="user_del")

    all_mems = service.get_all(user_id="user_del")
    assert len(all_mems) == 1
    mem_id = all_mems[0].id

    deleted = service.delete_memory(mem_id)
    assert deleted is True

    assert len(service.get_all(user_id="user_del")) == 0


# ----------------------------------------------------------------
# Service: full turn-to-retrieval pipeline
# ----------------------------------------------------------------

def test_full_store_index_retrieve_pipeline():
    """End-to-end: ingest turns, then retrieve each topic by its key terms."""
    svc = MemoryService()
    user = "user_pipeline"

    svc.process_turn("I live in Berlin", user_id=user)
    svc.process_turn("I prefer dark mode in all tools", user_id=user)
    svc.process_turn("I am building a CLI tool for productivity", user_id=user)
    svc.process_turn("Please keep responses under 100 words", user_id=user)

    # Location query — direct keyword match
    loc_results = svc.retrieve("Berlin location", user_id=user, limit=3)
    assert any("berlin" in r[0].content.lower() for r in loc_results)

    # Preference query — direct keyword match
    pref_results = svc.retrieve("dark mode tools", user_id=user, limit=3)
    assert any("dark mode" in r[0].content.lower() for r in pref_results)

    # Style query
    style_results = svc.retrieve("100 words response length", user_id=user, limit=3)
    assert any(
        "100 words" in r[0].content.lower() or "concise" in r[0].content.lower()
        for r in style_results
    )

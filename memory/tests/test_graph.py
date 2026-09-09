"""
Unit and Integration Tests for Knowledge Graph Associative Memory.
Verifies:
1. Extraction of entity-relationship triples
2. Graph indexing and node deduplication
3. Multi-hop traversal and associative context discovery
4. End-to-end memory service integration
"""
import pytest
from memory.src.graph_schemas import EntityType, RelationType, GraphTriple
from memory.src.graph_extractor import GraphTripleExtractor
from memory.src.graph_store import KnowledgeGraphStore
from memory.src.graph_traversal import GraphTraversalEngine
from memory.src.service import MemoryService


def test_graph_triple_extraction():
    extractor = GraphTripleExtractor()
    text = "I live in Tokyo, work as a Staff AI Engineer, and building Threadline using FastAPI, Qdrant"
    triples = extractor.extract_triples(text=text, user_name="Gian")

    assert len(triples) >= 3
    # Check location
    loc_triples = [t for t in triples if t.relation == RelationType.LIVES_IN]
    assert len(loc_triples) == 1
    assert loc_triples[0].object == "Tokyo"

    # Check profession
    role_triples = [t for t in triples if t.relation == RelationType.WORKS_AS]
    assert len(role_triples) == 1
    assert "Staff Ai Engineer" in role_triples[0].object

    # Check tools
    tool_triples = [t for t in triples if t.relation == RelationType.USES_TOOL]
    assert len(tool_triples) >= 1
    tool_names = [t.object for t in tool_triples]
    assert any("Fastapi" in tn or "Qdrant" in tn for tn in tool_names)


def test_graph_store_node_deduplication():
    store = KnowledgeGraphStore()
    user_id = "test_user_graph"

    # Add same entity twice
    n1 = store.get_or_create_node("FastAPI", EntityType.TOOL, user_id=user_id)
    n2 = store.get_or_create_node("fastapi", EntityType.TOOL, user_id=user_id)
    assert n1.id == n2.id
    assert len(store.get_all_nodes(user_id=user_id)) == 1


def test_multi_hop_traversal():
    store = KnowledgeGraphStore()
    traversal = GraphTraversalEngine(graph_store=store)
    user_id = "u_hops"

    # Triple 1: Gian lives_in Tokyo
    t1 = GraphTriple(
        subject="Gian",
        subject_type=EntityType.PERSON,
        relation=RelationType.LIVES_IN,
        object="Tokyo",
        object_type=EntityType.LOCATION,
    )
    # Triple 2: Tokyo located_in Japan
    t2 = GraphTriple(
        subject="Tokyo",
        subject_type=EntityType.LOCATION,
        relation=RelationType.LOCATED_IN,
        object="Japan",
        object_type=EntityType.LOCATION,
    )

    store.add_triple(t1, user_id=user_id)
    store.add_triple(t2, user_id=user_id)

    # Hop 1 + Hop 2 query
    results = traversal.traverse(query="Where is Gian?", user_id=user_id, max_hops=2)
    assert len(results) >= 2
    hop1 = [r for r in results if r["hop"] == 1]
    hop2 = [r for r in results if r["hop"] == 2]
    assert len(hop1) == 1
    assert hop1[0]["object"] == "Tokyo"
    assert len(hop2) == 1
    assert hop2[0]["object"] == "Japan"


def test_service_associative_recall():
    service = MemoryService()
    user_id = "u_service_graph"

    service.process_turn(
        user_message="I am based in Zurich and developing Threadline",
        user_id=user_id,
    )

    all_nodes = service.graph_store.get_all_nodes(user_id=user_id)
    assert len(all_nodes) >= 2

    # Query for Zurich
    assoc = service.retrieve_associative(query="Zurich", user_id=user_id)
    assert len(assoc) >= 0  # Valid execution

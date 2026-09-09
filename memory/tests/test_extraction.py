import pytest
from memory.src.schemas import MemoryCategory, MemoryAction
from memory.src.extractor import MemoryExtractor
from memory.src.store import MemoryStore
from memory.src.service import MemoryService

@pytest.fixture
def extractor():
    return MemoryExtractor()

@pytest.fixture
def store():
    return MemoryStore()

@pytest.fixture
def service(store, extractor):
    return MemoryService(store=store, extractor=extractor)

def test_small_talk_filtered_out(extractor):
    small_talk_phrases = [
        "Hello!",
        "Hi there",
        "How are you doing today?",
        "Good morning",
        "Thanks so much!",
        "Cool",
        "Bye!"
    ]
    for phrase in small_talk_phrases:
        res = extractor.extract_from_turn(phrase)
        assert len(res.memories) == 0, f"Expected 0 memories for small talk: '{phrase}'"

def test_preference_extraction(extractor):
    text = "I prefer dark mode in my editors."
    res = extractor.extract_from_turn(text)
    assert len(res.memories) == 1
    mem = res.memories[0]
    assert mem.category == MemoryCategory.PREFERENCES
    assert "dark mode" in mem.content.lower()
    assert mem.action == MemoryAction.ADD

def test_biographical_fact_extraction(extractor):
    text = "I live in Tokyo and I work as a Senior DevOps Engineer."
    res = extractor.extract_from_turn(text)
    assert len(res.memories) == 2
    
    categories = [m.category for m in res.memories]
    assert categories.count(MemoryCategory.BIOGRAPHICAL) == 2
    
    contents = [m.content for m in res.memories]
    assert any("Tokyo" in c for c in contents)
    assert any("DevOps Engineer" in c for c in contents)

def test_project_extraction(extractor):
    text = "I am currently developing AI Assistant With Memory using Mem0."
    res = extractor.extract_from_turn(text)
    assert len(res.memories) >= 1
    proj_mem = next(m for m in res.memories if m.category == MemoryCategory.PROJECTS)
    assert "AI Assistant With Memory" in proj_mem.content

def test_communication_style_extraction(extractor):
    text = "Please keep responses concise and avoid fluff."
    res = extractor.extract_from_turn(text)
    assert len(res.memories) == 1
    mem = res.memories[0]
    assert mem.category == MemoryCategory.COMMUNICATION_STYLE
    assert "concise" in mem.content.lower()

def test_conflict_resolution_and_update(service, store):
    user_id = "user_123"

    # Turn 1: User lives in Austin
    items1, _ = service.process_turn(
        user_message="I live in Austin",
        user_id=user_id
    )
    assert len(items1) == 1
    assert items1[0].content == "User lives in Austin"
    austin_mem_id = items1[0].id

    # Verify store contains Austin memory
    all_mems = store.get_all(user_id=user_id)
    assert len(all_mems) == 1
    assert all_mems[0].content == "User lives in Austin"

    # Turn 2: User moved to Berlin (contradiction)
    items2, extract_res = service.process_turn(
        user_message="I moved to Berlin recently",
        user_id=user_id
    )
    
    assert len(items2) == 1
    assert items2[0].id == austin_mem_id  # Same memory item ID updated!
    assert items2[0].content == "User lives in Berlin"
    assert items2[0].metadata.get("previous_content") == "User lives in Austin"

    # Verify total count in store is still 1 (no duplicate stale fact!)
    updated_all = store.get_all(user_id=user_id)
    assert len(updated_all) == 1
    assert updated_all[0].content == "User lives in Berlin"

def test_store_crud_and_scoping(store):
    u1 = "user_alpha"
    u2 = "user_beta"

    m1 = store.add("Loves Python", MemoryCategory.PREFERENCES, user_id=u1)
    m2 = store.add("Building web app", MemoryCategory.PROJECTS, user_id=u1)
    m3 = store.add("Loves Rust", MemoryCategory.PREFERENCES, user_id=u2)

    # Scoping by user
    assert len(store.get_all(user_id=u1)) == 2
    assert len(store.get_all(user_id=u2)) == 1

    # Scoping by category
    prefs_u1 = store.get_all(user_id=u1, category=MemoryCategory.PREFERENCES)
    assert len(prefs_u1) == 1
    assert prefs_u1[0].content == "Loves Python"

    # Deletion
    assert store.delete(m1.id) is True
    assert store.get(m1.id) is None
    assert len(store.get_all(user_id=u1)) == 1

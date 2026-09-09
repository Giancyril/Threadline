"""
Phase 3 Tests: Context Injection Engine and Chat API.
Verifies:
1. ContextBuilder formats markdown blocks and system prompt cleanly
2. ChatEngine retrieves prior memory and enriches the response
3. Chat turn extracts new facts and persists them across sessions
4. POST /api/v1/chat endpoint completes full round-trip
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.chat_engine import ChatEngine
from memory.src.service import MemoryService
from memory.src.context_builder import ContextBuilder
from memory.src.schemas import MemoryItem, MemoryCategory


def test_context_builder_formatting():
    builder = ContextBuilder()
    memories = [
        MemoryItem(id="m1", user_id="u1", content="User prefers dark mode", category=MemoryCategory.PREFERENCES),
        MemoryItem(id="m2", user_id="u1", content="User lives in Singapore", category=MemoryCategory.BIOGRAPHICAL),
        MemoryItem(id="m3", user_id="u1", content="User prefers concise answers", category=MemoryCategory.COMMUNICATION_STYLE),
    ]

    block = builder.build_memory_context_block(memories)
    assert "User Communication Style & Instructions:" in block
    assert "User Preferences:" in block
    assert "Biographical Details & Profile:" in block
    assert "dark mode" in block
    assert "Singapore" in block

    system_prompt = builder.build_system_prompt(memories)
    assert builder.base_system_prompt in system_prompt
    assert "Long-Term Memory Context" in system_prompt


def test_chat_engine_memory_lifecycle():
    mem_service = MemoryService()
    engine = ChatEngine(memory_service=mem_service)
    user_id = "test_user_phase3"

    # Turn 1: Learn fact
    res1 = engine.process_chat(
        user_message="I live in Berlin and prefer dark mode",
        user_id=user_id,
        session_id="session_1",
    )
    assert len(res1.newly_learned_memories) >= 1
    assert any("Berlin" in m["content"] or "dark mode" in m["content"] for m in res1.newly_learned_memories)

    # Turn 2: New session, same user asking about memory
    res2 = engine.process_chat(
        user_message="What do you know about me?",
        user_id=user_id,
        session_id="session_2",
    )
    assert len(res2.injected_memories) >= 1
    assert "Berlin" in res2.reply or "dark mode" in res2.reply


@pytest.mark.asyncio
async def test_chat_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "user_id": "api_test_user",
            "session_id": "sess_101",
            "message": "I prefer using FastAPI for all backend development",
            "use_memory": True,
            "learn_memory": True,
        }
        response = await ac.post("/api/v1/chat/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert data["user_id"] == "api_test_user"
        assert len(data["newly_learned_memories"]) >= 1

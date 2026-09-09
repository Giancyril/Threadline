"""
Phase 4 Tests: Memory Management REST API & Governance Controls.
Verifies:
1. POST /api/v1/memories/ - manual memory creation
2. GET /api/v1/memories/ - list, filter by user/category/search
3. GET & PUT /api/v1/memories/{id} - read and update memory
4. DELETE /api/v1/memories/{id} - targeted memory deletion
5. Learning Pause/Resume toggle
6. DELETE /api/v1/memories/purge/all - full purge
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_memory_crud_api_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_id = "test_gov_user"

        # 1. Create manual memory
        create_resp = await ac.post("/api/v1/memories/", json={
            "content": "Prefers dark mode in VSCode",
            "category": "preferences",
            "user_id": user_id,
        })
        assert create_resp.status_code == 201
        created = create_resp.json()
        mem_id = created["id"]
        assert created["content"] == "Prefers dark mode in VSCode"
        assert created["category"] == "preferences"

        # 2. List memories
        list_resp = await ac.get(f"/api/v1/memories/?user_id={user_id}")
        assert list_resp.status_code == 200
        mem_list = list_resp.json()
        assert mem_list["total"] >= 1
        assert any(m["id"] == mem_id for m in mem_list["memories"])

        # 3. Search filter
        search_resp = await ac.get(f"/api/v1/memories/?user_id={user_id}&search=dark+mode")
        assert search_resp.status_code == 200
        assert search_resp.json()["total"] >= 1

        # 4. Update memory
        update_resp = await ac.put(f"/api/v1/memories/{mem_id}", json={
            "content": "Prefers Solarized Dark theme in VSCode",
            "category": "preferences",
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["content"] == "Prefers Solarized Dark theme in VSCode"

        # 5. Delete specific memory
        del_resp = await ac.delete(f"/api/v1/memories/{mem_id}")
        assert del_resp.status_code == 200

        # Verify not found
        get_resp = await ac.get(f"/api/v1/memories/{mem_id}")
        assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_memory_learning_pause_toggle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_id = "pause_test_user"

        # Initial status is enabled
        status_resp = await ac.get(f"/api/v1/memories/learning/status?user_id={user_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["learning_enabled"] is True

        # Pause learning
        pause_resp = await ac.post(f"/api/v1/memories/learning/status?user_id={user_id}", json={
            "learning_enabled": False
        })
        assert pause_resp.status_code == 200
        assert pause_resp.json()["learning_enabled"] is False

        # Chat turn while paused should not extract/learn new facts
        chat_resp = await ac.post("/api/v1/chat/", json={
            "user_id": user_id,
            "message": "I live in Melbourne and work at Google",
            "use_memory": True,
            "learn_memory": True,
        })
        assert chat_resp.status_code == 200
        assert len(chat_resp.json()["newly_learned_memories"]) == 0

        # Resume learning
        resume_resp = await ac.post(f"/api/v1/memories/learning/status?user_id={user_id}", json={
            "learning_enabled": True
        })
        assert resume_resp.status_code == 200
        assert resume_resp.json()["learning_enabled"] is True


@pytest.mark.asyncio
async def test_purge_all_memories():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_id = "purge_user"

        # Add 2 memories
        await ac.post("/api/v1/memories/", json={"content": "Fact 1", "category": "biographical", "user_id": user_id})
        await ac.post("/api/v1/memories/", json={"content": "Fact 2", "category": "projects", "user_id": user_id})

        purge_resp = await ac.delete(f"/api/v1/memories/purge/all?user_id={user_id}")
        assert purge_resp.status_code == 200
        assert purge_resp.json()["deleted_count"] >= 2

        # Check list is now empty for this user
        list_resp = await ac.get(f"/api/v1/memories/?user_id={user_id}")
        assert list_resp.json()["total"] == 0

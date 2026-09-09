"""
Phase 7 End-to-End Hardening & Integration Test Suite.
Verifies the complete real-world user lifecycle across multiple sessions:
1. User provides biographical & preference facts in Session 1
2. Background turn-extraction categorizes and indexes into Qdrant
3. User opens Session 2 (new session ID) and asks a natural question
4. Retrieval engine enriches system prompt with context from Session 1
5. User updates a preference -> conflict detection updates the fact
6. User checks memory management bank -> sees updated fact
7. User activates Privacy Pause -> verifies assistant stops learning new facts
8. User executes Right-to-be-Forgotten Purge -> verifies memory bank is completely empty
9. Collaborative multi-agent workflow verifies shared memory access via OpenMemory MCP
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from memory.src.mcp_server import OpenMemoryMCPServer
from backend.app.api.chat import _shared_memory_service
from agents.src.workflow import MultiAgentOrchestrator


@pytest.mark.asyncio
async def test_full_e2e_user_journey_across_sessions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_id = "e2e_journey_user"

        # --- Step 1: Session 1 - Introduction and facts extraction ---
        sess1_resp = await client.post("/api/v1/chat/", json={
            "user_id": user_id,
            "session_id": "session_alpha",
            "message": "Hi! I am a Staff AI Engineer based in Tokyo and I prefer concise responses.",
            "use_memory": True,
            "learn_memory": True,
        })
        assert sess1_resp.status_code == 200
        data1 = sess1_resp.json()
        assert len(data1["newly_learned_memories"]) >= 1

        # --- Step 2: Session 2 - Cross-session recall ---
        sess2_resp = await client.post("/api/v1/chat/", json={
            "user_id": user_id,
            "session_id": "session_beta",
            "message": "What do you know about me?",
            "use_memory": True,
            "learn_memory": False,
        })
        assert sess2_resp.status_code == 200
        data2 = sess2_resp.json()
        assert len(data2["injected_memories"]) >= 1
        assert "Tokyo" in data2["reply"] or "Staff AI Engineer" in data2["reply"] or "concise" in data2["reply"]

        # --- Step 3: Conflict Update (User moves from Tokyo to Zurich) ---
        conflict_turn = await client.post("/api/v1/chat/", json={
            "user_id": user_id,
            "session_id": "session_beta",
            "message": "Actually I moved, I now live in Zurich",
            "use_memory": True,
            "learn_memory": True,
        })
        assert conflict_turn.status_code == 200
        data_conflict = conflict_turn.json()
        assert any("Zurich" in m["content"] for m in data_conflict["newly_learned_memories"])

        # --- Step 4: Governance UI verification ---
        mem_list = await client.get(f"/api/v1/memories/?user_id={user_id}")
        assert mem_list.status_code == 200
        memories = mem_list.json()["memories"]
        assert any("Zurich" in m["content"] for m in memories)

        # --- Step 5: Privacy pause toggle ---
        await client.post(f"/api/v1/memories/learning/status?user_id={user_id}", json={
            "learning_enabled": False
        })

        unlearned_turn = await client.post("/api/v1/chat/", json={
            "user_id": user_id,
            "session_id": "session_gamma",
            "message": "I bought a Tesla Model S today",
            "use_memory": True,
            "learn_memory": True,
        })
        assert unlearned_turn.status_code == 200
        assert len(unlearned_turn.json()["newly_learned_memories"]) == 0

        # --- Step 6: Multi-Agent shared memory access ---
        orchestrator = MultiAgentOrchestrator(memory_service=_shared_memory_service)
        agent_result = orchestrator.run_collaborative_workflow(topic="Neural Memory Architecture", user_id=user_id)
        assert agent_result["status"] == "completed"
        assert len(agent_result["writer"]["retrieved_memories"]) >= 1

        # --- Step 7: Right to be Forgotten (Full Purge) ---
        purge_resp = await client.delete(f"/api/v1/memories/purge/all?user_id={user_id}")
        assert purge_resp.status_code == 200
        assert purge_resp.json()["deleted_count"] >= 1

        # Confirm 0 memories left
        empty_list = await client.get(f"/api/v1/memories/?user_id={user_id}")
        assert empty_list.json()["total"] == 0

"""
Phase 5 Tests: OpenMemory MCP Server & Multi-Agent Shared Memory Pipeline.
Verifies:
1. OpenMemoryMCPServer tools schema conforms to specification
2. MCP store, retrieve, list, and delete tool execution
3. Multi-agent collaboration: Researcher writes to memory -> Writer retrieves and incorporates it
4. Cross-agent provenance tracking (source_agent tag preservation)
"""
import pytest
from memory.src.service import MemoryService
from memory.src.schemas import MemoryCategory
from memory.src.mcp_server import OpenMemoryMCPServer
from agents.src.workflow import MultiAgentOrchestrator, ResearcherAgent, WriterAgent


@pytest.mark.asyncio
async def test_mcp_server_tool_lifecycle():
    service = MemoryService()
    mcp = OpenMemoryMCPServer(memory_service=service)
    user_id = "mcp_test_user"

    # 1. Manifest
    tools = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in tools]
    assert "retrieve_memories" in tool_names
    assert "store_memory" in tool_names
    assert "list_all_memories" in tool_names
    assert "delete_memory" in tool_names

    # 2. Store tool
    store_res = await mcp.execute_tool("store_memory", {
        "content": "User prefers FastAPI and TypeScript",
        "category": "preferences",
        "user_id": user_id,
        "source_agent": "mcp_client_test",
    })
    assert store_res["success"] is True
    mem_id = store_res["memory"]["id"]
    assert store_res["memory"]["source_agent"] == "mcp_client_test"

    # 3. Retrieve tool
    retrieve_res = await mcp.execute_tool("retrieve_memories", {
        "query": "FastAPI TypeScript preferences",
        "user_id": user_id,
    })
    assert retrieve_res["count"] >= 1
    assert any("FastAPI" in m["content"] for m in retrieve_res["memories"])

    # 4. List tool
    list_res = await mcp.execute_tool("list_all_memories", {"user_id": user_id})
    assert list_res["total"] >= 1

    # 5. Delete tool
    del_res = await mcp.execute_tool("delete_memory", {"memory_id": mem_id})
    assert del_res["success"] is True


def test_multi_agent_shared_memory_workflow():
    service = MemoryService()
    user_id = "crew_user"

    # Preset user preference in memory
    service.add_manual_memory(
        content="User prefers concise responses",
        category=MemoryCategory.COMMUNICATION_STYLE,
        user_id=user_id,
        source_agent="user_setup",
    )

    orchestrator = MultiAgentOrchestrator(memory_service=service)
    result = orchestrator.run_collaborative_workflow(topic="AI Assistant Architecture", user_id=user_id)

    assert result["status"] == "completed"
    assert result["research"]["findings_count"] == 3

    # Verify Writer agent retrieved memories written by Researcher
    writer_retrieved = result["writer"]["retrieved_memories"]
    assert len(writer_retrieved) >= 1
    assert any("FastAPI" in m or "Qdrant" in m or "vector" in m for m in writer_retrieved)

    # Verify memory provenance was tracked
    all_stored = service.get_all(user_id=user_id)
    researcher_entries = [m for m in all_stored if m.source_agent == "researcher_agent"]
    assert len(researcher_entries) == 3

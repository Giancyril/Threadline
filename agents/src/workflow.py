"""
Multi-Agent Workflow with Shared Memory:
Demonstrates cross-agent collaboration where:
1. Agent 1 (Researcher / Discovery Agent) gathers technical facts & stores findings in shared memory.
2. Agent 2 (Writer / Synthesis Agent) retrieves stored findings & user preferences to draft the final deliverable.
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
from memory.src.service import MemoryService
from memory.src.schemas import MemoryCategory
from memory.src.context_builder import ContextBuilder


class BaseCollaborativeAgent:
    def __init__(self, name: str, role: str, memory_service: MemoryService):
        self.name = name
        self.role = role
        self.memory_service = memory_service
        self.context_builder = ContextBuilder()

    def read_shared_memory(self, query: str, user_id: str = "default_user") -> List[str]:
        results = self.memory_service.retrieve(query=query, user_id=user_id, limit=5)
        if not results:
            all_m = self.memory_service.get_all(user_id=user_id)
            results = [(m, 1.0) for m in all_m[:5]]
        return [item.content for item, _ in results]

    def write_to_shared_memory(
        self,
        content: str,
        category: MemoryCategory,
        user_id: str = "default_user",
    ) -> str:
        item = self.memory_service.add_manual_memory(
            content=content,
            category=category,
            user_id=user_id,
            source_agent=self.name,
        )
        return item.id


class ResearcherAgent(BaseCollaborativeAgent):
    """Gathers facts and discovers architectural constraints, writing them into shared memory."""

    def __init__(self, memory_service: MemoryService):
        super().__init__(name="researcher_agent", role="Technical Researcher", memory_service=memory_service)

    def conduct_research(self, topic: str, user_id: str = "default_user") -> Dict[str, Any]:
        # Perform research discovery
        discovered_findings = [
            f"User is standardizing on FastAPI and Qdrant for project: {topic}",
            "Technical requirement: vector search must use in-memory cosine fallback when offline",
            "Performance target: semantic memory retrieval must execute under 50ms",
        ]
        written_ids = []
        for fact in discovered_findings:
            mid = self.write_to_shared_memory(content=fact, category=MemoryCategory.PROJECTS, user_id=user_id)
            written_ids.append(mid)

        return {
            "agent": self.name,
            "topic": topic,
            "findings_count": len(discovered_findings),
            "stored_memory_ids": written_ids,
        }


class WriterAgent(BaseCollaborativeAgent):
    """Reads shared research memory and user preferences, producing tailored briefs."""

    def __init__(self, memory_service: MemoryService):
        super().__init__(name="writer_agent", role="Documentation & Synthesis Writer", memory_service=memory_service)

    def draft_report(self, topic: str, user_id: str = "default_user") -> Dict[str, Any]:
        # 1. Read shared memories stored by Researcher or user
        project_memories = self.read_shared_memory(query=topic, user_id=user_id)
        pref_memories = self.read_shared_memory(query="preferences style", user_id=user_id)

        # 2. Synthesize brief with memory awareness
        summary_lines = [f"- {m}" for m in project_memories]
        is_concise = any("concise" in p.lower() for p in pref_memories)

        draft = f"# Project Brief: {topic.title()}\n\n"
        draft += "## Key Context (Retrieved from Shared Memory Bank):\n"
        draft += "\n".join(summary_lines) if summary_lines else "- No prior project memories found."
        draft += "\n\n## Synthesis:\n"
        if is_concise:
            draft += "Delivered in concise bullet format adhering to user communication style."
        else:
            draft += "Delivered comprehensive architectural overview for the project."

        return {
            "agent": self.name,
            "topic": topic,
            "retrieved_memories": project_memories,
            "draft": draft,
        }


class MultiAgentOrchestrator:
    """Coordinates multi-agent execution pipeline sharing a unified MemoryService."""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        self.memory_service = memory_service or MemoryService()
        self.researcher = ResearcherAgent(memory_service=self.memory_service)
        self.writer = WriterAgent(memory_service=self.memory_service)

    def run_collaborative_workflow(self, topic: str, user_id: str = "default_user") -> Dict[str, Any]:
        research_output = self.researcher.conduct_research(topic=topic, user_id=user_id)
        writer_output = self.writer.draft_report(topic=topic, user_id=user_id)

        return {
            "status": "completed",
            "topic": topic,
            "user_id": user_id,
            "research": research_output,
            "writer": writer_output,
        }

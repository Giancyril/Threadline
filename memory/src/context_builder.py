"""
Context Injection Engine:
Formats retrieved user memories, personal profile, and communication styles
into structured system instructions and prompt enrichment blocks.
"""
from __future__ import annotations
from typing import Optional, Sequence
from .schemas import MemoryItem, MemoryCategory


class ContextBuilder:
    """
    Constructs the prompt context from retrieved memories, separating
    critical profile items, communication styles, and topical facts.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are an intelligent, thoughtful personal AI assistant with long-term memory. "
        "You retain useful facts across conversations, adapt to the user's communication "
        "style and preferences, and provide personalized, accurate responses."
    )

    def __init__(self, base_system_prompt: Optional[str] = None):
        self.base_system_prompt = base_system_prompt or self.DEFAULT_SYSTEM_PROMPT

    def build_memory_context_block(
        self,
        retrieved_memories: Sequence[tuple[MemoryItem, float] | MemoryItem],
        max_tokens_budget: int = 1500,
    ) -> str:
        """
        Groups memories by category and creates a clean markdown block
        ready for injection into the system prompt.
        """
        if not retrieved_memories:
            return ""

        # Normalize items whether passed as (MemoryItem, score) or MemoryItem
        items: list[MemoryItem] = []
        for entry in retrieved_memories:
            if isinstance(entry, tuple):
                items.append(entry[0])
            else:
                items.append(entry)

        # Deduplicate while preserving order
        seen_ids = set()
        unique_items: list[MemoryItem] = []
        for item in items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_items.append(item)

        # Categorize
        preferences = []
        biographical = []
        projects = []
        comm_style = []

        for item in unique_items:
            content_line = f"- {item.content}"
            if item.category == MemoryCategory.PREFERENCES:
                preferences.append(content_line)
            elif item.category == MemoryCategory.BIOGRAPHICAL:
                biographical.append(content_line)
            elif item.category == MemoryCategory.PROJECTS:
                projects.append(content_line)
            elif item.category == MemoryCategory.COMMUNICATION_STYLE:
                comm_style.append(content_line)

        sections = []
        if comm_style:
            nl = chr(10)
            sections.append("### User Communication Style & Instructions:" + nl + nl.join(comm_style))
        if preferences:
            nl = chr(10)
            sections.append("### User Preferences:" + nl + nl.join(preferences))
        if biographical:
            nl = chr(10)
            sections.append("### Biographical Details & Profile:" + nl + nl.join(biographical))
        if projects:
            nl = chr(10)
            sections.append("### Active Projects & Work Context:" + nl + nl.join(projects))

        if not sections:
            return ""

        sep = chr(10) + chr(10)
        memory_block = (
            "## Long-Term Memory Context\n"
            "The following facts and preferences were remembered from previous interactions with this user. "
            "Use them seamlessly to personalize your responses without explicitly citing memory IDs unless requested."
            + sep
            + sep.join(sections)
        )
        return memory_block

    def build_system_prompt(
        self,
        retrieved_memories: Sequence[tuple[MemoryItem, float] | MemoryItem] = (),
    ) -> str:
        """
        Merges base system instructions with relevant retrieved long-term memories.
        """
        memory_block = self.build_memory_context_block(retrieved_memories)
        if not memory_block:
            return self.base_system_prompt

        return f"{self.base_system_prompt}\n\n{memory_block}"

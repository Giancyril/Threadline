from typing import Optional, Sequence
from datetime import datetime, timezone
from .schemas import MemoryItem, ExtractedMemory, ExtractionResult, MemoryAction, MemoryCategory

class MemoryStore:
    """
    In-memory and persistent storage abstraction for user memories.
    Manages scoping by user_id, session_id, and category with conflict resolution.
    """
    def __init__(self):
        self._memories: dict[str, MemoryItem] = {}

    def add(
        self,
        content: str,
        category: MemoryCategory,
        user_id: str = "default_user",
        source_agent: str = "personal_assistant",
        session_id: Optional[str] = None,
        topic_key: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> MemoryItem:
        item = MemoryItem(
            content=content,
            category=category,
            user_id=user_id,
            source_agent=source_agent,
            session_id=session_id,
            topic_key=topic_key,
            metadata=metadata or {}
        )
        self._memories[item.id] = item
        return item

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        return self._memories.get(memory_id)

    def update(
        self,
        memory_id: str,
        content: str,
        category: Optional[MemoryCategory] = None,
        metadata: Optional[dict] = None
    ) -> Optional[MemoryItem]:
        item = self._memories.get(memory_id)
        if not item:
            return None
        item.content = content
        if category:
            item.category = category
        item.updated_at = datetime.now(timezone.utc).isoformat()
        if metadata:
            item.metadata.update(metadata)
        return item

    def delete(self, memory_id: str) -> bool:
        if memory_id in self._memories:
            del self._memories[memory_id]
            return True
        return False

    def get_all(
        self,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        session_id: Optional[str] = None
    ) -> list[MemoryItem]:
        results = list(self._memories.values())
        if user_id:
            results = [m for m in results if m.user_id == user_id]
        if category:
            results = [m for m in results if m.category == category]
        if session_id:
            results = [m for m in results if m.session_id == session_id]
        return sorted(results, key=lambda m: m.created_at, reverse=True)

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 5
    ) -> list[MemoryItem]:
        q_lower = query.lower()
        candidates = self.get_all(user_id=user_id, category=category)
        
        # Simple token intersection search (Phase 2 upgrades this to vector cosine similarity)
        scored = []
        q_tokens = set(q_lower.split())
        for c in candidates:
            c_tokens = set(c.content.lower().split())
            overlap = len(q_tokens.intersection(c_tokens))
            scored.append((overlap, c))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def apply_extraction(
        self,
        result: ExtractionResult,
        user_id: str = "default_user",
        source_agent: str = "personal_assistant",
        session_id: Optional[str] = None
    ) -> list[MemoryItem]:
        """
        Applies an extraction result to the store:
        - Handles ADD: inserts new memory item.
        - Handles UPDATE: overwrites conflicting memory item while maintaining history.
        - Handles DELETE: removes conflicting or flagged memory.
        """
        affected_items: list[MemoryItem] = []
        
        for ext in result.memories:
            if ext.action == MemoryAction.UPDATE and ext.conflicts_with_id:
                existing = self.get(ext.conflicts_with_id)
                if existing:
                    updated = self.update(
                        memory_id=existing.id,
                        content=ext.content,
                        category=ext.category,
                        metadata={"previous_content": existing.content, "updated_by": source_agent}
                    )
                    if updated:
                        affected_items.append(updated)
                        continue

            elif ext.action == MemoryAction.DELETE and ext.conflicts_with_id:
                self.delete(ext.conflicts_with_id)
                continue

            # Default ADD
            item = self.add(
                content=ext.content,
                category=ext.category,
                user_id=user_id,
                source_agent=source_agent,
                session_id=session_id,
                topic_key=ext.topic_key
            )
            affected_items.append(item)

        return affected_items

    def clear_all(self, user_id: Optional[str] = None) -> int:
        if user_id:
            to_del = [k for k, v in self._memories.items() if v.user_id == user_id]
            for k in to_del:
                del self._memories[k]
            return len(to_del)
        else:
            count = len(self._memories)
            self._memories.clear()
            return count

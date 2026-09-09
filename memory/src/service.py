from typing import Optional
from .schemas import MemoryItem, ExtractionResult
from .extractor import MemoryExtractor
from .store import MemoryStore

class MemoryService:
    """
    High-level memory orchestrator coordinating extraction, categorization,
    conflict detection, and persistence.
    """
    def __init__(self, store: Optional[MemoryStore] = None, extractor: Optional[MemoryExtractor] = None):
        self.store = store or MemoryStore()
        self.extractor = extractor or MemoryExtractor()

    def process_turn(
        self,
        user_message: str,
        assistant_message: Optional[str] = None,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        source_agent: str = "personal_assistant"
    ) -> tuple[list[MemoryItem], ExtractionResult]:
        # 1. Fetch current active memories for context & conflict detection
        existing = self.store.get_all(user_id=user_id)

        # 2. Extract durable facts and identify updates/conflicts
        extraction_result = self.extractor.extract_from_turn(
            user_message=user_message,
            assistant_message=assistant_message,
            existing_memories=existing
        )

        # 3. Apply changes (ADD/UPDATE/DELETE) into store
        applied_items = self.store.apply_extraction(
            result=extraction_result,
            user_id=user_id,
            source_agent=source_agent,
            session_id=session_id
        )

        return applied_items, extraction_result

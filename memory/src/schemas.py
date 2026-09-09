from enum import Enum
from typing import Optional, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field

class MemoryCategory(str, Enum):
    PREFERENCES = "preferences"
    BIOGRAPHICAL = "biographical"
    PROJECTS = "projects"
    COMMUNICATION_STYLE = "communication_style"

class MemoryAction(str, Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    NOOP = "noop"

class ExtractedMemory(BaseModel):
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:10]}")
    content: str = Field(..., description="The concise, durable factual statement about the user")
    category: MemoryCategory = Field(..., description="Assigned memory category")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    action: MemoryAction = Field(default=MemoryAction.ADD)
    conflicts_with_id: Optional[str] = Field(default=None, description="ID of existing memory this contradicts")
    topic_key: Optional[str] = Field(default=None, description="Normalized entity/topic key for deduplication e.g. location, theme, role")
    reasoning: Optional[str] = None

class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:10]}")
    user_id: str = "default_user"
    content: str
    category: MemoryCategory
    source_agent: str = "personal_assistant"
    session_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    topic_key: Optional[str] = None

class ExtractionResult(BaseModel):
    memories: list[ExtractedMemory] = Field(default_factory=list)
    raw_turn: str
    turn_analyzed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

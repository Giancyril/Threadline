"""
Schemas for Memory Management REST API.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from memory.src.schemas import MemoryCategory


class MemoryCreateRequest(BaseModel):
    content: str = Field(..., min_length=2, description="Factual memory content")
    category: MemoryCategory = Field(default=MemoryCategory.PREFERENCES, description="Category for grouping")
    user_id: str = Field(default="default_user", description="User scope")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MemoryUpdateRequest(BaseModel):
    content: str = Field(..., min_length=2, description="Updated memory text")
    category: Optional[MemoryCategory] = Field(default=None, description="Updated category if changed")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class MemoryItemResponse(BaseModel):
    id: str
    user_id: str
    content: str
    category: MemoryCategory
    source_agent: str
    session_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryListResponse(BaseModel):
    total: int
    user_id: Optional[str] = None
    memories: List[MemoryItemResponse]


class LearningStatusResponse(BaseModel):
    user_id: str
    learning_enabled: bool


class LearningStatusUpdateRequest(BaseModel):
    learning_enabled: bool


class PurgeResponse(BaseModel):
    deleted_count: int
    message: str

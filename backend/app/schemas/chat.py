"""
Chat request and response schemas including memory provenance tracking.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    user_id: str = Field(default="default_user", description="Identifier of the user")
    session_id: Optional[str] = Field(default="default_session", description="Session identifier")
    message: str = Field(..., description="The user's latest input message")
    history: List[ChatMessage] = Field(default_factory=list, description="Prior conversational turns in this session")
    use_memory: bool = Field(default=True, description="Whether to retrieve and apply long-term memory")
    learn_memory: bool = Field(default=True, description="Whether to extract and store facts from this turn")


class MemoryCitation(BaseModel):
    id: str
    content: str
    category: str
    score: float


class ChatResponse(BaseModel):
    reply: str
    user_id: str
    session_id: Optional[str] = None
    injected_memories: List[MemoryCitation] = Field(default_factory=list)
    newly_learned_memories: List[Dict[str, Any]] = Field(default_factory=list)

"""
Chat endpoints exposing memory-injected conversational turns.
"""
from fastapi import APIRouter, Depends
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_engine import ChatEngine
from memory.src.service import MemoryService

router = APIRouter(prefix="/chat", tags=["Chat"])

# Singleton service shared across backend calls
_shared_memory_service = MemoryService()
_shared_chat_engine = ChatEngine(memory_service=_shared_memory_service)


def get_chat_engine() -> ChatEngine:
    return _shared_chat_engine


@router.post("/", response_model=ChatResponse)
async def chat_turn(
    request: ChatRequest,
    engine: ChatEngine = Depends(get_chat_engine),
):
    """
    Handle a user chat turn with automated memory retrieval, prompt enrichment,
    and background fact extraction.
    """
    return engine.process_chat(
        user_message=request.message,
        user_id=request.user_id,
        session_id=request.session_id,
        history=request.history,
        use_memory=request.use_memory,
        learn_memory=request.learn_memory,
    )

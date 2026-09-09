"""
REST API endpoints for viewing, searching, editing, deleting, and governing memories.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.memory import (
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryItemResponse,
    MemoryListResponse,
    LearningStatusResponse,
    LearningStatusUpdateRequest,
    PurgeResponse,
)
from memory.src.schemas import MemoryCategory
from backend.app.api.chat import _shared_memory_service

router = APIRouter(prefix="/memories", tags=["Memories"])


@router.get("/", response_model=MemoryListResponse)
async def list_memories(
    user_id: Optional[str] = Query(default=None, description="Filter by user"),
    category: Optional[MemoryCategory] = Query(default=None, description="Filter by category"),
    search: Optional[str] = Query(default=None, description="Keyword filter"),
):
    """Retrieve all stored memories with optional user, category, and keyword filters."""
    items = _shared_memory_service.get_all(user_id=user_id, category=category, search_query=search)
    return MemoryListResponse(
        total=len(items),
        user_id=user_id,
        memories=[
            MemoryItemResponse(
                id=m.id,
                user_id=m.user_id,
                content=m.content,
                category=m.category,
                source_agent=m.source_agent,
                session_id=m.session_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                metadata=m.metadata,
            )
            for m in items
        ],
    )


@router.post("/", response_model=MemoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(request: MemoryCreateRequest):
    """Manually add a memory item into the user's memory bank."""
    item = _shared_memory_service.add_manual_memory(
        content=request.content,
        category=request.category,
        user_id=request.user_id,
        source_agent="user_direct",
        metadata=request.metadata,
    )
    return MemoryItemResponse(
        id=item.id,
        user_id=item.user_id,
        content=item.content,
        category=item.category,
        source_agent=item.source_agent,
        session_id=item.session_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
        metadata=item.metadata,
    )


@router.get("/{memory_id}", response_model=MemoryItemResponse)
async def get_memory(memory_id: str):
    """Get a single memory item by ID."""
    item = _shared_memory_service.get_memory(memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryItemResponse(
        id=item.id,
        user_id=item.user_id,
        content=item.content,
        category=item.category,
        source_agent=item.source_agent,
        session_id=item.session_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
        metadata=item.metadata,
    )


@router.put("/{memory_id}", response_model=MemoryItemResponse)
async def update_memory(memory_id: str, request: MemoryUpdateRequest):
    """Edit or correct an existing memory."""
    updated = _shared_memory_service.update_memory(
        memory_id=memory_id,
        content=request.content,
        category=request.category,
        metadata=request.metadata,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryItemResponse(
        id=updated.id,
        user_id=updated.user_id,
        content=updated.content,
        category=updated.category,
        source_agent=updated.source_agent,
        session_id=updated.session_id,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        metadata=updated.metadata,
    )


@router.delete("/{memory_id}", status_code=status.HTTP_200_OK)
async def delete_memory(memory_id: str):
    """Delete a specific memory item."""
    success = _shared_memory_service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted successfully", "id": memory_id}


@router.delete("/purge/all", response_model=PurgeResponse)
async def purge_memories(
    user_id: Optional[str] = Query(default=None, description="Clear memories only for this user"),
):
    """Clear all memories (privacy right to be forgotten)."""
    count = _shared_memory_service.clear_all(user_id=user_id)
    return PurgeResponse(
        deleted_count=count,
        message=f"Successfully purged {count} memory items.",
    )


# ------------------------------------------------------------------
# Privacy: Learning Pause / Resume
# ------------------------------------------------------------------

@router.get("/learning/status", response_model=LearningStatusResponse)
async def get_learning_status(user_id: str = Query(default="default_user")):
    """Check if memory extraction/learning is currently active for a user."""
    enabled = _shared_memory_service.is_learning_enabled(user_id)
    return LearningStatusResponse(user_id=user_id, learning_enabled=enabled)


@router.post("/learning/status", response_model=LearningStatusResponse)
async def update_learning_status(
    request: LearningStatusUpdateRequest,
    user_id: str = Query(default="default_user"),
):
    """Pause or resume automatic memory learning for a user."""
    enabled = _shared_memory_service.set_learning_enabled(user_id, request.learning_enabled)
    return LearningStatusResponse(user_id=user_id, learning_enabled=enabled)

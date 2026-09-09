"""
Memory Versioning API Endpoints.

Exposes:
  GET  /api/v1/versioning/{memory_id}/history    - Full version history with snapshots and diffs
  GET  /api/v1/versioning/{memory_id}/snapshots  - List all snapshots for a memory
  GET  /api/v1/versioning/{memory_id}/diffs      - List all diffs / change records
  POST /api/v1/versioning/{memory_id}/rollback   - Restore a memory to a specific version
  POST /api/v1/versioning/{memory_id}/update     - Update memory with contradiction scoring
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional

from memory.src.rollback_service import MemoryRollbackService
from memory.src.schemas import MemoryCategory

router = APIRouter(prefix="/versioning", tags=["versioning"])

# Shared rollback service (DI-compatible singleton for this demo)
_rollback_svc = MemoryRollbackService()


class UpdateMemoryRequest(BaseModel):
    new_content: str
    topic_key: Optional[str] = ""
    triggered_by: Optional[str] = "user"


class RollbackRequest(BaseModel):
    to_version: int
    triggered_by: Optional[str] = "user"


@router.get("/{memory_id}/history")
async def get_memory_history(memory_id: str):
    """
    Returns the complete version history for a memory:
    all snapshots (immutable records) and diffs (change records with contradiction scores).
    """
    history = _rollback_svc.get_history(memory_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"No history found for memory '{memory_id}'")

    return {
        "memory_id": memory_id,
        "current_version": history.current_version,
        "latest_content": history.latest_content,
        "snapshots": [s.model_dump() for s in history.snapshots],
        "diffs": [d.model_dump() for d in history.diffs],
    }


@router.get("/{memory_id}/snapshots")
async def get_memory_snapshots(memory_id: str):
    """Returns ordered list of all version snapshots for a memory."""
    snaps = _rollback_svc.get_snapshots(memory_id)
    if not snaps:
        raise HTTPException(status_code=404, detail=f"No snapshots found for '{memory_id}'")
    return {"memory_id": memory_id, "count": len(snaps), "snapshots": [s.model_dump() for s in snaps]}


@router.get("/{memory_id}/diffs")
async def get_memory_diffs(memory_id: str):
    """Returns all contradiction diffs recorded for this memory."""
    diffs = _rollback_svc.get_diffs(memory_id)
    return {
        "memory_id": memory_id,
        "count": len(diffs),
        "diffs": [d.model_dump() for d in diffs],
    }


@router.post("/{memory_id}/rollback")
async def rollback_memory(memory_id: str, body: RollbackRequest):
    """
    Roll back a memory to a specific historical version.
    Creates a new snapshot recording the rollback event.
    """
    restored = _rollback_svc.rollback(memory_id, body.to_version, body.triggered_by or "user")
    if not restored:
        raise HTTPException(
            status_code=404,
            detail=f"Memory '{memory_id}' not found or version {body.to_version} does not exist"
        )
    return {
        "memory_id": memory_id,
        "restored_version": body.to_version,
        "current_content": restored.content,
        "status": "rolled_back"
    }


@router.post("/{memory_id}/update")
async def update_memory_with_scoring(memory_id: str, body: UpdateMemoryRequest):
    """
    Update a memory's content with automatic contradiction confidence scoring.
    Returns the updated memory and the contradiction score computed.
    """
    existing = _rollback_svc.get_memory(memory_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    updated = _rollback_svc.update_memory(
        memory_id=memory_id,
        new_content=body.new_content,
        topic_key=body.topic_key or "",
        triggered_by=body.triggered_by or "user",
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")

    diffs = _rollback_svc.get_diffs(memory_id)
    latest_diff = diffs[-1] if diffs else None

    return {
        "memory_id": memory_id,
        "previous_content": existing.content,
        "new_content": updated.content,
        "contradiction_confidence": latest_diff.contradiction_confidence if latest_diff else 0.0,
        "contradiction_severity": latest_diff.contradiction_severity if latest_diff else "none",
        "explanation": latest_diff.explanation if latest_diff else None,
    }

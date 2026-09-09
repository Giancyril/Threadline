"""
Temporal Memory API Endpoints.

Exposes:
  GET  /api/v1/temporal/tiers         - List all LongevityTier definitions and half-lives
  GET  /api/v1/temporal/status        - Get temporal health: active vs archived counts
  POST /api/v1/temporal/prune         - Manually trigger a pruning/archival cycle
  POST /api/v1/temporal/expire/{id}   - Manually force-expire a specific memory
  GET  /api/v1/temporal/archived      - List all archived memories for auditing
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

from memory.src.temporal_schemas import LongevityTier, TemporalMetadata
from memory.src.store import MemoryStore
from memory.src.pruning_service import MemoryPruningService

router = APIRouter(prefix="/temporal", tags=["temporal"])

# Shared store instance (in production this would be dependency-injected)
_store = MemoryStore()
_pruner = MemoryPruningService(_store)


class TierInfo(BaseModel):
    tier: str
    description: str
    half_life_days: float
    example: str


class TemporalStatusResponse(BaseModel):
    total_memories: int
    active_memories: int
    archived_memories: int
    by_tier: dict


class PruneResponse(BaseModel):
    pruned_at: str
    archived_ephemeral: int
    archived_project_bound: int
    skipped_permanent: int
    total_archived: int


@router.get("/tiers", response_model=list[TierInfo])
async def list_longevity_tiers():
    """Return all LongevityTier definitions with descriptions and half-lives."""
    return [
        TierInfo(
            tier=LongevityTier.EPHEMERAL.value,
            description="Short-lived facts anchored to a specific moment or day.",
            half_life_days=1.0,
            example="User is eating lunch at a ramen shop today"
        ),
        TierInfo(
            tier=LongevityTier.PROJECT_BOUND.value,
            description="Project-specific context that fades after 30-45 days.",
            half_life_days=30.0,
            example="User is working on feature/auth branch for the current sprint"
        ),
        TierInfo(
            tier=LongevityTier.PERMANENT.value,
            description="Core identity facts that never expire.",
            half_life_days=9999.0,
            example="User is a Staff AI Engineer based in Tokyo"
        ),
    ]


@router.get("/status", response_model=TemporalStatusResponse)
async def get_temporal_status():
    """Return temporal health metrics: how many memories are active vs archived by tier."""
    all_memories = _store.get_all()
    active = _pruner.get_active_memories()
    archived = [m for m in all_memories if m.metadata.get("is_archived", False)]

    by_tier: dict = {}
    for m in all_memories:
        tier = m.metadata.get("longevity_tier", LongevityTier.PERMANENT.value)
        by_tier[tier] = by_tier.get(tier, 0) + 1

    return TemporalStatusResponse(
        total_memories=len(all_memories),
        active_memories=len(active),
        archived_memories=len(archived),
        by_tier=by_tier,
    )


@router.post("/prune", response_model=PruneResponse)
async def trigger_pruning():
    """Manually trigger a full pruning cycle to archive all expired memories."""
    result = _pruner.prune_now()
    return PruneResponse(**result)


@router.post("/expire/{memory_id}")
async def force_expire_memory(memory_id: str):
    """Force-expire a specific memory by ID, marking it as archived immediately."""
    mem = _store.get(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    now = datetime.now(timezone.utc).isoformat()
    _store.update(
        memory_id=memory_id,
        content=mem.content,
        metadata={
            **mem.metadata,
            "is_archived": True,
            "archived_at": now,
            "archive_reason": "Manually force-expired via API",
            "expires_at": now,
        }
    )
    return {"memory_id": memory_id, "archived_at": now, "status": "force-expired"}


@router.get("/archived")
async def list_archived_memories():
    """Return all soft-archived memories for audit purposes."""
    all_memories = _store.get_all()
    archived = [m for m in all_memories if m.metadata.get("is_archived", False)]
    return {
        "count": len(archived),
        "archived_memories": [
            {
                "id": m.id,
                "content": m.content,
                "category": m.category.value,
                "longevity_tier": m.metadata.get("longevity_tier"),
                "archived_at": m.metadata.get("archived_at"),
                "archive_reason": m.metadata.get("archive_reason"),
            }
            for m in archived
        ],
    }

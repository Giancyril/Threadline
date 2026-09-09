"""
Memory Federation API Endpoints.

Exposes:
  GET  /api/v1/federation/manifest - Returns this agent's federation manifest
  POST /api/v1/federation/export   - Generates cryptographically signed TMEF bundle with PII scrubbing
  POST /api/v1/federation/import   - Ingests and reconciles remote TMEF bundle with conflict resolution
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

from memory.src.federation_schemas import TMEFBundle, AgentManifest, ExportedMemoryItem, FederationImportResult
from memory.src.federation_crypto import FederationCryptoSigner, DEFAULT_FEDERATION_SECRET
from memory.src.privacy_scrubber import PrivacyScrubber
from memory.src.federation_merger import FederationMergeResolver
from backend.app.api.versioning import _rollback_svc

router = APIRouter(prefix="/federation", tags=["federation"])

_crypto_signer = FederationCryptoSigner()
_scrubber = PrivacyScrubber()
_merger = FederationMergeResolver()

LOCAL_AGENT = AgentManifest(
    agent_id="agent_threadline_host",
    agent_name="Threadline Local Host",
    agent_version="1.2.0",
    framework="threadline",
    capabilities=["semantic_memory", "knowledge_graph", "longevity_decay", "versioning", "tmef_v1"]
)


class ExportRequest(BaseModel):
    categories: Optional[List[str]] = None
    redact_pii: bool = True
    custom_secret: Optional[str] = None


class ImportRequest(BaseModel):
    bundle: TMEFBundle
    strategy: str = "auto"  # auto, local_wins, remote_wins
    custom_secret: Optional[str] = None
    verify_signature: bool = True


@router.get("/manifest", response_model=AgentManifest)
async def get_agent_manifest():
    """Returns local agent's federation metadata and supported capabilities."""
    return LOCAL_AGENT


@router.post("/export", response_model=TMEFBundle)
async def export_tmef_bundle(req: ExportRequest = Body(default_factory=ExportRequest)):
    """
    Exports memories in standardized TMEF v1.0 format with optional PII redaction
    and cryptographic HMAC-SHA256 signature seal.
    """
    memories = _rollback_svc.store.get_all()
    
    # Filter by category if requested
    if req.categories:
        memories = [m for m in memories if (m.category.value if hasattr(m.category, "value") else str(m.category)) in req.categories]

    mem_dicts = [
        {
            "id": m.id,
            "content": m.content,
            "category": m.category.value if hasattr(m.category, "value") else str(m.category),
            "created_at": getattr(m, "created_at", datetime.now(timezone.utc).isoformat()),
            "metadata": getattr(m, "metadata", {}) or {}
        }
        for m in memories
    ]

    redaction_summary = None
    if req.redact_pii:
        mem_dicts, redaction_summary = _scrubber.scrub_memory_items(mem_dicts)

    bundle_items = [
        ExportedMemoryItem(
            memory_id=m["id"],
            content=m["content"],
            category=m["category"],
            longevity_tier=m.get("metadata", {}).get("longevity_tier", "permanent"),
            created_at=str(m["created_at"]),
            metadata=m.get("metadata", {})
        )
        for m in mem_dicts
    ]

    bundle_id = f"tmef_{uuid.uuid4().hex[:12]}"
    exported_at = datetime.now(timezone.utc)

    # Prepare bundle without signature first
    bundle = TMEFBundle(
        format_version="1.0",
        bundle_id=bundle_id,
        exported_at=exported_at,
        source_agent=LOCAL_AGENT,
        memory_count=len(bundle_items),
        memories=bundle_items,
        is_redacted=req.redact_pii,
        redaction_summary=redaction_summary
    )

    signer = FederationCryptoSigner(req.custom_secret) if req.custom_secret else _crypto_signer
    bundle.signature = signer.sign_bundle(bundle.model_dump())

    return bundle


@router.post("/import", response_model=FederationImportResult)
async def import_tmef_bundle(req: ImportRequest):
    """
    Validates cryptographic seal, applies 3-way conflict reconciliation,
    and ingests memories into local store.
    """
    signer = FederationCryptoSigner(req.custom_secret) if req.custom_secret else _crypto_signer
    
    if req.verify_signature:
        is_valid = signer.verify_bundle(req.bundle.model_dump(), req.bundle.signature)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid bundle signature: payload may be tampered or secret mismatch.")

    # Current local memories
    current_memories = _rollback_svc.store.get_all()
    local_dicts = [
        {
            "id": m.id,
            "content": m.content,
            "category": m.category.value if hasattr(m.category, "value") else str(m.category),
            "created_at": getattr(m, "created_at", datetime.now(timezone.utc).isoformat()),
            "metadata": getattr(m, "metadata", {}) or {}
        }
        for m in current_memories
    ]

    merged_dicts, result = _merger.reconcile_bundle(req.bundle, local_dicts, strategy=req.strategy)

    # Commit merged memories to store
    for item in merged_dicts:
        if not any(m.id == item["id"] for m in current_memories):
            _rollback_svc.record_add(
                item["id"],
                item["content"],
                item["category"],
                triggered_by=f"federation:{req.bundle.source_agent.agent_id}"
            )

    return result

"""
Threadline Memory Exchange Format (TMEF) v1 Specification.

Standardized interoperability protocol for federating, exporting,
and cryptographically exchanging agent memories across distributed AI systems.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentManifest(BaseModel):
    """Metadata describing the originating or destination agent."""
    agent_id: str
    agent_name: str
    agent_version: str = "1.0.0"
    framework: str = "threadline"
    capabilities: List[str] = Field(default_factory=lambda: ["semantic_memory", "knowledge_graph"])


class ExportedMemoryItem(BaseModel):
    """Individual memory payload within an exchange bundle."""
    memory_id: str
    content: str
    category: str
    longevity_tier: str = "permanent"
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    topic_tags: List[str] = Field(default_factory=list)


class TMEFBundle(BaseModel):
    """
    Threadline Memory Exchange Format (TMEF) v1.0 Bundle.
    Complete portable memory payload with cryptographic seal and audit manifest.
    """
    format_version: str = "1.0"
    bundle_id: str
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_agent: AgentManifest
    memory_count: int
    memories: List[ExportedMemoryItem]
    signature: str = ""  # SHA-256 HMAC seal
    is_redacted: bool = False
    redaction_summary: Optional[Dict[str, int]] = None


class FederationImportResult(BaseModel):
    """Result of importing a TMEF memory bundle into local memory store."""
    bundle_id: str
    total_received: int
    imported_count: int
    skipped_duplicates: int
    contradictions_flagged: int
    signature_valid: bool
    imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)

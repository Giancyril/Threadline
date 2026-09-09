"""
Memory Versioning & Contradiction Audit Trail schemas.

Provides immutable snapshot history for each memory, tracking every
content evolution with diffs, contradiction scores, and rollback pointers.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class VersionTrigger(str, Enum):
    USER_UPDATE = "user_update"          # User explicitly changed a fact
    AUTO_CONTRADICTION = "auto_contradiction"  # System detected a conflicting new statement
    MANUAL_EDIT = "manual_edit"          # User edited via UI
    ROLLBACK = "rollback"                # Restored from a previous version
    INITIAL = "initial"                  # First-ever version of this memory


class ContradictionSeverity(str, Enum):
    NONE = "none"           # No contradiction detected
    LOW = "low"             # Possible misinterpretation (conf < 0.4)
    MEDIUM = "medium"       # Probable update (conf 0.4 - 0.8)
    HIGH = "high"           # Clear factual conflict (conf > 0.8)


class MemorySnapshot(BaseModel):
    """
    An immutable point-in-time snapshot of a memory's content.
    Each update creates a new snapshot; history is append-only.
    """
    snapshot_id: str = Field(default_factory=lambda: f"snap_{uuid.uuid4().hex[:10]}")
    memory_id: str = Field(..., description="The parent memory's stable ID")
    version: int = Field(..., description="Monotonic version number, starting at 1")
    content: str = Field(..., description="Verbatim memory content at this version")
    trigger: VersionTrigger = Field(default=VersionTrigger.INITIAL)
    triggered_by: str = Field(default="system", description="Agent or user that caused this version")
    snapshot_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = Field(default_factory=dict)


class MemoryDiff(BaseModel):
    """
    Records the diff between two consecutive memory snapshots,
    with optional contradiction confidence scoring.
    """
    diff_id: str = Field(default_factory=lambda: f"diff_{uuid.uuid4().hex[:10]}")
    memory_id: str
    from_version: int
    to_version: int
    previous_content: str
    new_content: str
    contradiction_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="0.0 = same meaning, 1.0 = direct factual contradiction"
    )
    contradiction_severity: ContradictionSeverity = ContradictionSeverity.NONE
    explanation: Optional[str] = Field(
        default=None,
        description="Human-readable note explaining the nature of the update"
    )
    diff_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_snapshots(
        cls,
        from_snap: MemorySnapshot,
        to_snap: MemorySnapshot,
        contradiction_confidence: float = 0.0,
        explanation: Optional[str] = None
    ) -> "MemoryDiff":
        """Convenience constructor from two consecutive snapshots."""
        if contradiction_confidence >= 0.8:
            severity = ContradictionSeverity.HIGH
        elif contradiction_confidence >= 0.4:
            severity = ContradictionSeverity.MEDIUM
        elif contradiction_confidence > 0.0:
            severity = ContradictionSeverity.LOW
        else:
            severity = ContradictionSeverity.NONE

        auto_explanation = explanation
        if not auto_explanation:
            auto_explanation = (
                f"Memory updated from v{from_snap.version} to v{to_snap.version} "
                f"(trigger: {to_snap.trigger.value})"
            )

        return cls(
            memory_id=from_snap.memory_id,
            from_version=from_snap.version,
            to_version=to_snap.version,
            previous_content=from_snap.content,
            new_content=to_snap.content,
            contradiction_confidence=contradiction_confidence,
            contradiction_severity=severity,
            explanation=auto_explanation,
        )


class VersionedMemoryHistory(BaseModel):
    """
    Complete version history for a single memory item.
    Snapshots are ordered oldest-first. Current version is snapshots[-1].
    """
    memory_id: str
    snapshots: list[MemorySnapshot] = Field(default_factory=list)
    diffs: list[MemoryDiff] = Field(default_factory=list)

    @property
    def current_version(self) -> int:
        return len(self.snapshots)

    @property
    def latest_content(self) -> Optional[str]:
        return self.snapshots[-1].content if self.snapshots else None

    def get_snapshot(self, version: int) -> Optional[MemorySnapshot]:
        """Retrieve a specific version snapshot (1-indexed)."""
        for snap in self.snapshots:
            if snap.version == version:
                return snap
        return None

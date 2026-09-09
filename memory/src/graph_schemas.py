"""
Knowledge Graph Triple and Node schemas for associative semantic memory.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PERSON = "person"
    LOCATION = "location"
    ROLE = "role"
    PROJECT = "project"
    TOOL = "tool"
    PREFERENCE = "preference"
    CONCEPT = "concept"


class RelationType(str, Enum):
    LIVES_IN = "lives_in"
    WORKS_AS = "works_as"
    WORKS_ON = "works_on"
    PREFERS = "prefers"
    USES_TOOL = "uses_tool"
    COMMUNICATES_VIA = "communicates_via"
    LOCATED_IN = "located_in"
    RELATES_TO = "relates_to"


class KnowledgeNode(BaseModel):
    id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., description="Canonical entity name e.g. 'Tokyo', 'FastAPI', 'Gian'")
    entity_type: EntityType = Field(default=EntityType.CONCEPT)
    user_id: str = "default_user"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeEdge(BaseModel):
    id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}")
    source_node_id: str
    target_node_id: str
    relation: RelationType
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    source_memory_id: Optional[str] = None
    user_id: str = "default_user"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GraphTriple(BaseModel):
    subject: str
    subject_type: EntityType
    relation: RelationType
    object: str
    object_type: EntityType
    confidence: float = 0.95
    source_memory_id: Optional[str] = None

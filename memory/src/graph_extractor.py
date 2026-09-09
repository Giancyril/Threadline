"""
Entity & Relationship Triple Extractor:
Parses raw turns or existing memories into structured (Subject, Relation, Object) triples.
"""
from __future__ import annotations
import re
from typing import List, Optional
from .graph_schemas import GraphTriple, EntityType, RelationType


class GraphTripleExtractor:
    """
    Extracts structured knowledge triples from text turns and memories.
    """

    def extract_triples(
        self,
        text: str,
        user_name: str = "User",
        source_memory_id: Optional[str] = None
    ) -> List[GraphTriple]:
        triples: List[GraphTriple] = []
        clean = text.strip()

        # 1. Location: User lives_in <City>
        loc = re.search(r"(?:i live in|lives in|based in|moved to|residing in)\s+([A-Za-z\s]+?)(?:\.|$|,| and )", clean, re.IGNORECASE)
        if loc:
            city = loc.group(1).strip().title()
            if city:
                triples.append(GraphTriple(
                    subject=user_name,
                    subject_type=EntityType.PERSON,
                    relation=RelationType.LIVES_IN,
                    object=city,
                    object_type=EntityType.LOCATION,
                    source_memory_id=source_memory_id,
                ))

        # 2. Profession: User works_as <Role>
        role = re.search(r"(?:i am a|works as a|work as a|is a|i work as a)\s+([A-Za-z0-9\s]+?)(?:\.|\$|,| with | at | and )", clean, re.IGNORECASE)
        if role:
            role_name = role.group(1).strip().title()
            if role_name and not any(w in role_name.lower() for w in ["bit", "fan", "good"]):
                triples.append(GraphTriple(
                    subject=user_name,
                    subject_type=EntityType.PERSON,
                    relation=RelationType.WORKS_AS,
                    object=role_name,
                    object_type=EntityType.ROLE,
                    source_memory_id=source_memory_id,
                ))

        # 3. Project: User works_on <Project>
        proj = re.search(r"(?:working on|building|developing|project is)\s+([A-Za-z0-9\s\-_]+?)(?:\.|$|,| using | with )", clean, re.IGNORECASE)
        if proj:
            project_name = proj.group(1).strip().title()
            if project_name:
                triples.append(GraphTriple(
                    subject=user_name,
                    subject_type=EntityType.PERSON,
                    relation=RelationType.WORKS_ON,
                    object=project_name,
                    object_type=EntityType.PROJECT,
                    source_memory_id=source_memory_id,
                ))

        # 4. Tool / Tech Stack: <Project> uses_tool <Tool>
        tech = re.search(r"(?:using|uses|built with|stack is)\s+([A-Za-z0-9\s,]+?)(?:\.|$)", clean, re.IGNORECASE)
        if tech:
            tools = [t.strip().title() for t in tech.group(1).split(",") if len(t.strip()) > 1]
            for t in tools:
                triples.append(GraphTriple(
                    subject=user_name,
                    subject_type=EntityType.PERSON,
                    relation=RelationType.USES_TOOL,
                    object=t,
                    object_type=EntityType.TOOL,
                    source_memory_id=source_memory_id,
                ))

        # 5. Preference: User prefers <Preference>
        pref = re.search(r"(?:prefers|likes|preference is)\s+([A-Za-z0-9\s\-_]+?)(?:\.|$|,| over )", clean, re.IGNORECASE)
        if pref:
            pref_name = pref.group(1).strip().title()
            if pref_name and len(pref_name) > 3:
                triples.append(GraphTriple(
                    subject=user_name,
                    subject_type=EntityType.PERSON,
                    relation=RelationType.PREFERS,
                    object=pref_name,
                    object_type=EntityType.PREFERENCE,
                    source_memory_id=source_memory_id,
                ))

        return triples

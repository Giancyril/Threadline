import re
from typing import Optional, Sequence, Any
from .schemas import MemoryCategory, MemoryAction, ExtractedMemory, ExtractionResult, MemoryItem

class MemoryExtractor:
    """
    Analyzes conversation turns to extract durable facts and categorize them.
    Features heuristic pattern matching for deterministic offline execution + LLM hooks.
    """
    
    SMALL_TALK_PATTERNS = [
        r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|howdy|sup)[\s!\.,]*$",
        r"^(how\s+are\s+you|how's\s+it\s+going|what's\s+up)[\s\?!]*$",
        r"^(thanks|thank\s+you|ok|okay|cool|great|got\s+it|nice)[\s!\.,]*$",
        r"^(bye|goodbye|see\s+ya|catch\s+you\s+later)[\s!\.,]*$"
    ]

    TEMPORAL_NOISE = ["recently", "now", "lately", "currently", "today", "this month", "this year", "a while ago"]

    def is_small_talk(self, text: str) -> bool:
        clean = text.strip().lower()
        if len(clean) < 3:
            return True
        for pat in self.SMALL_TALK_PATTERNS:
            if re.match(pat, clean):
                return True
        return False

    def extract_from_turn(
        self,
        user_message: str,
        assistant_message: Optional[str] = None,
        existing_memories: Optional[Sequence[MemoryItem]] = None,
        llm_client: Any = None
    ) -> ExtractionResult:
        turn_text = f"User: {user_message}"
        if assistant_message:
            turn_text += f"\nAssistant: {assistant_message}"

        if self.is_small_talk(user_message):
            return ExtractionResult(memories=[], raw_turn=turn_text)

        memories = self._heuristic_extract(user_message, existing_memories or [])
        return ExtractionResult(memories=memories, raw_turn=turn_text)

    def _clean_entity(self, text: str) -> str:
        res = text.strip()
        for noise in self.TEMPORAL_NOISE:
            res = re.sub(rf"\b{noise}\b", "", res, flags=re.IGNORECASE).strip()
        return res.strip(" ,.-")

    def _heuristic_extract(
        self,
        text: str,
        existing_memories: Sequence[MemoryItem]
    ) -> list[ExtractedMemory]:
        results: list[ExtractedMemory] = []

        # 1. Location extraction (Biographical)
        loc_match = re.search(r"(?:i live in|i moved to|i'm based in|based in|living in)\s+([A-Za-z\s]+?)(?:\.|$|,|and)", text, re.IGNORECASE)
        if loc_match:
            city_raw = loc_match.group(1).strip()
            city = self._clean_entity(city_raw).title()
            if city:
                conflict_id = None
                action = MemoryAction.ADD
                for ex in existing_memories:
                    if ex.category == MemoryCategory.BIOGRAPHICAL and ("lives in" in ex.content.lower() or "based in" in ex.content.lower()):
                        conflict_id = ex.id
                        action = MemoryAction.UPDATE
                        break
                
                results.append(ExtractedMemory(
                    content=f"User lives in {city}",
                    category=MemoryCategory.BIOGRAPHICAL,
                    action=action,
                    conflicts_with_id=conflict_id,
                    topic_key="location",
                    reasoning="Identified user residence/location"
                ))

        # 2. Profession / Role extraction (Biographical)
        role_match = re.search(r"(?:i am a|i'm a|i work as a)\s+([A-Za-z0-9\s]+?)(?:\.|$|,|and|with)", text, re.IGNORECASE)
        if role_match:
            role_raw = role_match.group(1).strip()
            role = self._clean_entity(role_raw)
            if role and not any(f in role.lower() for f in ["bit", "little", "fan of", "good", "bad"]):
                conflict_id = None
                action = MemoryAction.ADD
                for ex in existing_memories:
                    if ex.category == MemoryCategory.BIOGRAPHICAL and ("works as" in ex.content.lower() or "is a" in ex.content.lower()):
                        conflict_id = ex.id
                        action = MemoryAction.UPDATE
                        break

                results.append(ExtractedMemory(
                    content=f"User works as a {role}",
                    category=MemoryCategory.BIOGRAPHICAL,
                    action=action,
                    conflicts_with_id=conflict_id,
                    topic_key="profession",
                    reasoning="Identified user professional role"
                ))

        # 3. Project extraction (Projects)
        proj_match = re.search(r"(?:building|working on|developing|created a project called|project is)\s+([A-Za-z0-9\s\-_]+?)(?:\.|$|,|\s+using\s+)", text, re.IGNORECASE)
        if proj_match:
            project_name = self._clean_entity(proj_match.group(1)).strip()
            if project_name:
                results.append(ExtractedMemory(
                    content=f"User is working on project: {project_name}",
                    category=MemoryCategory.PROJECTS,
                    action=MemoryAction.ADD,
                    topic_key=f"project_{project_name.lower()}",
                    reasoning="Identified ongoing project or codebase"
                ))

        # 4. Preferences extraction (Preferences)
        pref_match = re.search(r"(?:i prefer|i like|i love|my preference is)\s+([A-Za-z0-9\s\-_]+?)(?:\.|$|,|over)", text, re.IGNORECASE)
        if pref_match:
            pref = self._clean_entity(pref_match.group(1))
            if len(pref) > 3 and pref.lower() not in ["this", "that", "it"]:
                results.append(ExtractedMemory(
                    content=f"User prefers {pref}",
                    category=MemoryCategory.PREFERENCES,
                    action=MemoryAction.ADD,
                    topic_key=f"pref_{pref[:15].lower()}",
                    reasoning="Identified explicit preference"
                ))

        # 5. Communication Style extraction (Communication Style)
        style_match = re.search(r"(?:keep answers|keep responses|please be|prefer responses that are|never use emojis|concise bulleted|always include code|be concise|avoid fluff)(.*?)(?:\.|$)", text, re.IGNORECASE)
        if style_match:
            full_stmt = style_match.group(0).strip()
            results.append(ExtractedMemory(
                content=f"User communication preference: {full_stmt}",
                category=MemoryCategory.COMMUNICATION_STYLE,
                action=MemoryAction.ADD,
                topic_key="comm_style",
                reasoning="Identified communication style directive"
            ))

        return results

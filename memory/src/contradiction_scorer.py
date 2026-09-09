"""
Contradiction Confidence Scorer.

Heuristically computes a confidence score [0.0, 1.0] indicating
how strongly a new memory statement contradicts an existing one.

Scoring strategy:
  - Lexical overlap penalty (high overlap = low contradiction)
  - Topic/keyword signals (e.g. location changes, role changes)
  - Negation detection (e.g. "no longer", "moved from", "quit")
  - Direct antonym pairs for core biographical facts

Used by the VersionedMemoryStore when recording updates.
"""
from __future__ import annotations
import re
from .schemas import MemoryCategory


class ContradictionScorer:
    """
    Heuristic contradiction confidence scorer.

    Returns:
        float in [0.0, 1.0] where:
          0.0 = same meaning / no contradiction
          0.4 = possible update (user refined or clarified)
          0.8+ = direct factual contradiction
    """

    # Signals that strongly imply a change from a previous state
    CHANGE_SIGNALS = [
        r"\bno longer\b", r"\bnot anymore\b", r"\bmoved (from|to)\b",
        r"\bswitched (from|to)\b", r"\bchanged (from|to|my)\b",
        r"\bused to\b", r"\bformerly\b", r"\bpreviously\b",
        r"\bnow (live|work|use|am)\b", r"\bjust (quit|left|joined|started)\b",
        r"\bleaving\b", r"\bstarted at\b", r"\bjoined\b",
    ]

    # Topics where a new value always implies a contradiction with old
    EXCLUSIVE_TOPICS = ["location", "profession", "role", "employer", "city", "country"]

    def score(
        self,
        existing_content: str,
        new_content: str,
        category: MemoryCategory,
        topic_key: str = "",
    ) -> tuple[float, str]:
        """
        Compute contradiction confidence and return (score, explanation).

        Args:
            existing_content: The current memory text.
            new_content: The proposed new memory text.
            category: MemoryCategory of the memory.
            topic_key: Normalized topic key (e.g. 'location', 'profession').

        Returns:
            Tuple of (confidence: float, explanation: str).
        """
        if existing_content.strip().lower() == new_content.strip().lower():
            return 0.0, "Content is identical — no contradiction."

        score = 0.0
        reasons: list[str] = []

        # Check for explicit change-signaling language in the new content
        new_lower = new_content.lower()
        change_detected = False
        for pat in self.CHANGE_SIGNALS:
            if re.search(pat, new_lower, re.IGNORECASE):
                score = max(score, 0.75)
                reasons.append(f"Change signal detected: '{pat}'")
                change_detected = True
                break

        # If topic is exclusive (only one valid value at a time), boost score
        if topic_key and any(excl in topic_key.lower() for excl in self.EXCLUSIVE_TOPICS):
            if existing_content.strip().lower() != new_content.strip().lower():
                score = max(score, 0.65)
                reasons.append(f"Exclusive topic '{topic_key}' updated with different value")

        # Biographical updates are almost always contradictions
        if category == MemoryCategory.BIOGRAPHICAL and not change_detected:
            score = max(score, 0.55)
            reasons.append("Biographical fact replaced — probable contradiction")

        # Compute token overlap penalty (high overlap = low conflict)
        existing_tokens = set(existing_content.lower().split())
        new_tokens = set(new_content.lower().split())
        overlap = len(existing_tokens & new_tokens) / max(len(existing_tokens | new_tokens), 1)
        if overlap > 0.7:
            score = max(0.0, score - 0.3)  # Heavy overlap → probably a refinement
            reasons.append(f"High token overlap ({overlap:.0%}) — likely a clarification")
        elif overlap < 0.2:
            score = min(1.0, score + 0.15)  # Very different text → stronger conflict
            reasons.append(f"Low token overlap ({overlap:.0%}) — content diverged significantly")

        score = round(min(max(score, 0.0), 1.0), 3)
        explanation = (
            f"Contradiction score: {score:.2f}. "
            + ("; ".join(reasons) if reasons else "Heuristic baseline applied.")
        )
        if not reasons:
            explanation += " Content changed but no explicit contradiction signal found."

        return score, explanation

"""
Semantic Divergence Alerter.

Detects significant drifts and polarity switches in user preferences,
producing actionable notifications for proactive memory reconciliation.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from memory.src.drift_schemas import DivergenceAlert


SHIFT_PATTERNS = [
    # (topic, keyword_pairs)
    ("Programming Language", [("python", "rust"), ("python", "typescript"), ("javascript", "go"), ("c++", "rust")]),
    ("Backend Framework", [("fastapi", "django"), ("express", "fastapi"), ("flask", "fastapi"), ("spring", "nest")]),
    ("Database Choice", [("postgres", "mongodb"), ("mysql", "postgres"), ("redis", "sqlite")]),
    ("Tone & Style", [("concise", "detailed"), ("formal", "casual"), ("bullet points", "conversational")]),
    ("Operating System", [("windows", "linux"), ("macos", "linux"), ("windows", "macos")]),
    ("Theme Preference", [("dark", "light"), ("light", "dark")]),
]


class DivergenceAlerter:
    """
    Scans pairs of historical vs recent memories within the same category
    to identify behavioral and technical preference divergence.
    """
    def __init__(self, sensitivity: float = 0.70):
        self.sensitivity = sensitivity

    def detect_preference_shifts(
        self,
        historical_memories: List[Dict[str, Any]],
        recent_memories: List[Dict[str, Any]]
    ) -> List[DivergenceAlert]:
        """
        Compares earlier memories with recent ones to detect domain shifts.
        """
        alerts: List[DivergenceAlert] = []

        for recent in recent_memories:
            r_content = recent.get("content", "").lower()
            r_cat = recent.get("category", "")

            for old in historical_memories:
                o_content = old.get("content", "").lower()
                o_cat = old.get("category", "")

                # Must share category or be in preferences/projects
                if o_cat != r_cat and not ({o_cat, r_cat} & {"preferences", "projects", "communication_style"}):
                    continue

                for topic, pairs in SHIFT_PATTERNS:
                    for val_a, val_b in pairs:
                        # Check forward shift val_a -> val_b
                        has_a_in_old = bool(re.search(rf"\b{re.escape(val_a)}\b", o_content))
                        has_b_in_new = bool(re.search(rf"\b{re.escape(val_b)}\b", r_content))
                        has_b_in_old = bool(re.search(rf"\b{re.escape(val_b)}\b", o_content))

                        if has_a_in_old and has_b_in_new and not has_b_in_old:
                            # Detected shift
                            score = 0.85
                            severity = "high" if score >= 0.8 else "medium"
                            alert = DivergenceAlert(
                                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                                topic=topic,
                                previous_preference=old.get("content", ""),
                                current_preference=recent.get("content", ""),
                                divergence_score=score,
                                severity=severity,
                                detected_at=datetime.now(timezone.utc),
                                recommendation=(
                                    f"User has shifted {topic.lower()} preference from '{val_a}' to '{val_b}'. "
                                    f"Suggest updating or deprecating historical memory."
                                )
                            )
                            alerts.append(alert)

                        # Check reverse shift val_b -> val_a
                        has_b_in_old2 = bool(re.search(rf"\b{re.escape(val_b)}\b", o_content))
                        has_a_in_new2 = bool(re.search(rf"\b{re.escape(val_a)}\b", r_content))
                        has_a_in_old2 = bool(re.search(rf"\b{re.escape(val_a)}\b", o_content))

                        if has_b_in_old2 and has_a_in_new2 and not has_a_in_old2:
                            score = 0.85
                            severity = "high" if score >= 0.8 else "medium"
                            alert = DivergenceAlert(
                                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                                topic=topic,
                                previous_preference=old.get("content", ""),
                                current_preference=recent.get("content", ""),
                                divergence_score=score,
                                severity=severity,
                                detected_at=datetime.now(timezone.utc),
                                recommendation=(
                                    f"User has shifted {topic.lower()} preference from '{val_b}' to '{val_a}'. "
                                    f"Suggest updating or deprecating historical memory."
                                )
                            )
                            alerts.append(alert)

        # De-duplicate alerts with same topic and preferences
        unique_alerts: List[DivergenceAlert] = []
        seen = set()
        for a in alerts:
            key = (a.topic, a.previous_preference, a.current_preference)
            if key not in seen:
                seen.add(key)
                unique_alerts.append(a)

        return unique_alerts

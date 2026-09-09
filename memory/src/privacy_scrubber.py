"""
Privacy Scrubbing & Redaction Engine for Cross-Agent Memory Federation.

Strips personally identifiable information (PII), credential secrets, API keys,
and private identifiers before memory bundles leave local storage boundaries.
"""
from __future__ import annotations

import re
from typing import Tuple, Dict, Any, List


PII_PATTERNS = [
    ("api_key", re.compile(r"\b(sk-[a-zA-Z0-9_\-]{15,}|ghp_[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_\-\.]{20,}|AIza[0-9A-Za-z-_]{35})\b", re.IGNORECASE), "[REDACTED_API_KEY]"),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"), "[REDACTED_EMAIL]"),
    ("phone", re.compile(r"\b(\+?[0-9]{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    ("credit_card", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[REDACTED_CARD]"),
    ("ip_address", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[REDACTED_IP]"),
]


class PrivacyScrubber:
    """
    Sanitizes memory text according to privacy policies before federation export.
    """
    def __init__(
        self,
        redact_keys: bool = True,
        redact_emails: bool = True,
        redact_phones: bool = True,
        redact_cards: bool = True,
        redact_ips: bool = True
    ):
        self.enabled_rules = {
            "api_key": redact_keys,
            "email": redact_emails,
            "phone": redact_phones,
            "credit_card": redact_cards,
            "ip_address": redact_ips,
        }

    def scrub_text(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Applies redaction filters to input string.
        Returns: (scrubbed_text, counts_by_category)
        """
        scrubbed = text
        stats: Dict[str, int] = {}

        for category, pattern, placeholder in PII_PATTERNS:
            if not self.enabled_rules.get(category, True):
                continue
            matches = pattern.findall(scrubbed)
            if matches:
                stats[category] = len(matches)
                scrubbed = pattern.sub(placeholder, scrubbed)

        return scrubbed, stats

    def scrub_memory_items(
        self,
        memories: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Scrubs a list of memory dicts and tallies overall redactions.
        """
        overall_stats: Dict[str, int] = {}
        scrubbed_memories: List[Dict[str, Any]] = []

        for m in memories:
            item_copy = dict(m)
            original_content = item_copy.get("content", "")
            cleaned_content, counts = self.scrub_text(original_content)
            item_copy["content"] = cleaned_content

            for cat, cnt in counts.items():
                overall_stats[cat] = overall_stats.get(cat, 0) + cnt

            scrubbed_memories.append(item_copy)

        return scrubbed_memories, overall_stats

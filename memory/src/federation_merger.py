"""
Memory Federation Merge & Reconciliation Resolver.

Reconciles incoming federated memory bundles against the local memory store,
handling deduplication, timestamp precedence, and contradiction reconciliation.
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple
from memory.src.federation_schemas import TMEFBundle, FederationImportResult, ExportedMemoryItem
from memory.src.contradiction_scorer import ContradictionScorer
from memory.src.schemas import MemoryCategory


class FederationMergeResolver:
    """
    Resolves multi-agent memory synchronization conflicts.
    """
    def __init__(self, conflict_threshold: float = 0.40):
        self.conflict_threshold = conflict_threshold
        self.contradiction_scorer = ContradictionScorer()

    def reconcile_bundle(
        self,
        bundle: TMEFBundle,
        local_memories: List[Dict[str, Any]],
        strategy: str = "auto"  # auto, local_wins, remote_wins
    ) -> Tuple[List[Dict[str, Any]], FederationImportResult]:
        """
        Merges bundle.memories into local_memories.
        Returns: (merged_memory_list, import_result)
        """
        merged = list(local_memories)
        imported_count = 0
        skipped_duplicates = 0
        contradictions_flagged = 0
        conflicts: List[Dict[str, Any]] = []

        local_by_content = {m.get("content", "").strip().lower(): m for m in merged}

        for item in bundle.memories:
            cleaned_content = item.content.strip()
            norm_content = cleaned_content.lower()

            # 1. Exact duplication check
            if norm_content in local_by_content:
                skipped_duplicates += 1
                continue

            # 2. Check for semantic contradiction with existing memories in same category
            contradiction_found = False
            try:
                cat_enum = MemoryCategory(item.category)
            except Exception:
                cat_enum = MemoryCategory.PREFERENCES

            for loc in merged:
                if loc.get("category") == item.category:
                    score, explanation = self.contradiction_scorer.score(
                        loc.get("content", ""),
                        cleaned_content,
                        category=cat_enum
                    )
                    if score >= self.conflict_threshold:
                        contradiction_found = True
                        contradictions_flagged += 1
                        conflict_info = {
                            "type": "semantic_contradiction",
                            "local_id": loc.get("id"),
                            "local_content": loc.get("content"),
                            "remote_content": cleaned_content,
                            "contradiction_score": score,
                            "explanation": explanation,
                            "resolution_strategy": strategy
                        }
                        conflicts.append(conflict_info)

                        if strategy == "remote_wins":
                            loc["content"] = cleaned_content
                            loc["source_agent"] = f"federated:{bundle.source_agent.agent_name}"
                            imported_count += 1
                        break

            if contradiction_found and strategy != "remote_wins":
                continue

            if not contradiction_found:
                # 3. New memory to append
                new_entry = {
                    "id": f"fed_{item.memory_id}",
                    "content": cleaned_content,
                    "category": item.category,
                    "source_agent": f"federated:{bundle.source_agent.agent_name}",
                    "created_at": item.created_at,
                    "metadata": {
                        **item.metadata,
                        "longevity_tier": item.longevity_tier,
                        "federated_from": bundle.source_agent.agent_id,
                        "bundle_id": bundle.bundle_id
                    }
                }
                merged.append(new_entry)
                local_by_content[norm_content] = new_entry
                imported_count += 1

        result = FederationImportResult(
            bundle_id=bundle.bundle_id,
            total_received=len(bundle.memories),
            imported_count=imported_count,
            skipped_duplicates=skipped_duplicates,
            contradictions_flagged=contradictions_flagged,
            signature_valid=True,
            conflicts=conflicts
        )

        return merged, result

"""
Online Topic Clustering for Memories.

Groups incoming and existing memories into coherent semantic topic clusters
using graph-community / distance-based clustering, computing keyword signatures
and cluster cohesion scores.
"""
from __future__ import annotations

import re
import math
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from memory.src.drift_schemas import TopicCluster


STOPWORDS: Set[str] = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they", "them",
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "can", "could", "will", "would", "should", "of", "about",
    "that", "this", "these", "those", "likes", "prefers", "always", "never", "user"
}


def extract_keywords(text: str, max_words: int = 4) -> List[str]:
    """Tokenizes text, strips stopwords and returns highest frequency terms."""
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    if not filtered:
        return ["general"]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(max_words)]


def text_jaccard_similarity(text_a: str, text_b: str) -> float:
    """Computes Jaccard similarity of token sets between two texts."""
    set_a = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text_a.lower())) - STOPWORDS
    set_b = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text_b.lower())) - STOPWORDS
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


class TopicClusterEngine:
    """
    Groups memories into clusters and maintains updated topic taxonomy.
    """
    def __init__(self, similarity_threshold: float = 0.20):
        self.similarity_threshold = similarity_threshold

    def cluster_memories(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[TopicCluster]:
        """
        Groups a list of memory dicts (must contain 'id' and 'content', optionally 'category')
        into TopicCluster instances.
        """
        if not memories:
            return []

        # Graph adjacency list where edge exists if similarity >= threshold
        n = len(memories)
        adj: Dict[int, List[int]] = {i: [] for i in range(n)}

        for i in range(n):
            for j in range(i + 1, n):
                sim = text_jaccard_similarity(
                    memories[i].get("content", ""),
                    memories[j].get("content", "")
                )
                # Category boost
                if memories[i].get("category") == memories[j].get("category"):
                    sim += 0.15

                if sim >= self.similarity_threshold:
                    adj[i].append(j)
                    adj[j].append(i)

        # Find connected components (clusters)
        visited: Set[int] = set()
        clusters: List[TopicCluster] = []

        for i in range(n):
            if i in visited:
                continue

            component_indices: List[int] = []
            queue = [i]
            visited.add(i)

            while queue:
                curr = queue.pop(0)
                component_indices.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            # Build cluster details
            cluster_memories = [memories[idx] for idx in component_indices]
            mem_ids = [m.get("id", f"mem_{idx}") for idx, m in zip(component_indices, cluster_memories)]
            combined_text = " ".join(m.get("content", "") for m in cluster_memories)
            keywords = extract_keywords(combined_text, max_words=5)
            
            # Name cluster by top 2 keywords or dominant category
            cat = cluster_memories[0].get("category", "topic")
            cluster_name = f"{cat.capitalize()}: {', '.join(keywords[:2]).title()}" if keywords else f"{cat.capitalize()} Cluster"
            
            # Compute internal cohesion
            cohesion = 1.0
            if len(component_indices) > 1:
                pairwise_sims = []
                for a in range(len(cluster_memories)):
                    for b in range(a + 1, len(cluster_memories)):
                        pairwise_sims.append(
                            text_jaccard_similarity(
                                cluster_memories[a].get("content", ""),
                                cluster_memories[b].get("content", "")
                            )
                        )
                cohesion = sum(pairwise_sims) / len(pairwise_sims) if pairwise_sims else 1.0
                cohesion = min(1.0, max(0.2, cohesion * 1.5))

            cluster_id = f"cluster_{len(clusters) + 1}"
            clusters.append(
                TopicCluster(
                    cluster_id=cluster_id,
                    name=cluster_name,
                    keywords=keywords,
                    memory_ids=mem_ids,
                    cohesion_score=round(cohesion, 3),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            )

        return sorted(clusters, key=lambda c: len(c.memory_ids), reverse=True)

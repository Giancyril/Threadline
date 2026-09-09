"""
Embedding layer — deterministic TF-IDF embeddings for local/offline use.
Drop-in interface allows swapping to OpenAI/Gemini text embeddings when an
API key is available, without changing any calling code.
"""
from __future__ import annotations
from typing import Protocol, Sequence, runtime_checkable
import math


@runtime_checkable
class Embedder(Protocol):
    """Any object implementing encode() satisfies this protocol."""
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class TFIDFEmbedder:
    """
    Lightweight, zero-dependency TF-IDF embedder.
    Builds a vocabulary on the fly and returns normalized vectors.
    Good enough for semantic retrieval over a personal memory bank (dozens to
    low hundreds of entries). Phase 5+ can swap to dense embeddings.
    """

    def __init__(self, min_df: int = 1, max_features: int = 512):
        self._vocab: dict[str, int] = {}
        self._idf: dict[int, float] = {}
        self._min_df = min_df
        self._max_features = max_features
        self._fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, texts: list[str]) -> "TFIDFEmbedder":
        """Build vocabulary and IDF weights from a corpus."""
        from collections import Counter, defaultdict

        doc_freq: Counter[str] = Counter()
        tokenized = [self._tokenize(t) for t in texts]
        N = len(texts)

        for tokens in tokenized:
            for token in set(tokens):
                doc_freq[token] += 1

        # Keep the max_features most common tokens above min_df
        eligible = {
            t: df for t, df in doc_freq.items() if df >= self._min_df
        }
        top_tokens = sorted(
            eligible, key=lambda t: eligible[t], reverse=True
        )[: self._max_features]

        self._vocab = {token: idx for idx, token in enumerate(top_tokens)}
        self._idf = {
            idx: math.log((N + 1) / (doc_freq[token] + 1)) + 1.0
            for token, idx in self._vocab.items()
        }
        self._fitted = True
        return self

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode texts into normalized TF-IDF vectors.
        Fits on the input texts if not already fitted.
        """
        if not self._fitted:
            self.fit(texts)

        vectors = []
        for text in texts:
            vec = self._tfidf_vector(text)
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            vectors.append(vec)
        return vectors

    def encode_single(self, text: str) -> list[float]:
        return self.encode([text])[0]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> list[str]:
        import re
        return re.findall(r"[a-z0-9]+", text.lower())

    def _tfidf_vector(self, text: str) -> list[float]:
        from collections import Counter
        if not self._vocab:
            return []
        tokens = self._tokenize(text)
        tf: Counter[str] = Counter(tokens)
        total = max(len(tokens), 1)
        dim = len(self._vocab)
        vec = [0.0] * dim
        for token, count in tf.items():
            if token in self._vocab:
                idx = self._vocab[token]
                idf = self._idf.get(idx, 1.0)
                vec[idx] = (count / total) * idf
        return vec

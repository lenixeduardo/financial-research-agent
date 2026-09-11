import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass


_TOKEN_RE = re.compile(r"[\wÀ-ÿ]{3,}")


@dataclass(frozen=True)
class RetrievalCandidate:
    key: str
    text: str
    lexical_score: float
    semantic_score: float
    combined_score: float


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.casefold())


def _stable_hash(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big")


def _hashed_embedding(text: str, dimensions: int = 96) -> list[float]:
    """Dependency-free deterministic feature-hashed embedding for local/dev retrieval.

    This gives the repository a reproducible dense-retrieval path without requiring
    an external model during tests. A production embedding provider can replace this
    behind the same ranking contract.
    """
    vector = [0.0] * dimensions
    for token in tokenize(text):
        idx = _stable_hash(token) % dimensions
        sign = 1.0 if _stable_hash(f"sign:{token}") % 2 == 0 else -1.0
        vector[idx] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def _cosine(a: list[float], b: list[float]) -> float:
    return max(0.0, sum(x * y for x, y in zip(a, b, strict=True)))


def _bm25(query_tokens: list[str], document_tokens: list[str], average_length: float) -> float:
    if not query_tokens or not document_tokens:
        return 0.0
    counts = Counter(document_tokens)
    length = len(document_tokens)
    k1 = 1.5
    b = 0.75
    score = 0.0
    for term in set(query_tokens):
        frequency = counts[term]
        if not frequency:
            continue
        denominator = frequency + k1 * (1 - b + b * length / max(average_length, 1.0))
        score += (frequency * (k1 + 1)) / denominator
    return score


def hybrid_rank(
    query: str,
    documents: list[tuple[str, str]],
    *,
    top_k: int = 5,
    min_score: float = 0.05,
) -> list[RetrievalCandidate]:
    if not documents:
        return []
    query_tokens = tokenize(query)
    query_embedding = _hashed_embedding(query)
    tokenized_documents = [(key, text, tokenize(text)) for key, text in documents]
    average_length = sum(len(tokens) for _, _, tokens in tokenized_documents) / len(tokenized_documents)

    raw: list[tuple[str, str, float, float]] = []
    max_lexical = 0.0
    for key, text, tokens in tokenized_documents:
        lexical = _bm25(query_tokens, tokens, average_length)
        semantic = _cosine(query_embedding, _hashed_embedding(text))
        max_lexical = max(max_lexical, lexical)
        raw.append((key, text, lexical, semantic))

    ranked: list[RetrievalCandidate] = []
    for key, text, lexical, semantic in raw:
        normalized_lexical = lexical / max_lexical if max_lexical else 0.0
        combined = 0.65 * normalized_lexical + 0.35 * semantic
        if combined >= min_score:
            ranked.append(
                RetrievalCandidate(
                    key=key,
                    text=text,
                    lexical_score=round(normalized_lexical, 6),
                    semantic_score=round(semantic, 6),
                    combined_score=round(combined, 6),
                )
            )
    ranked.sort(key=lambda item: item.combined_score, reverse=True)
    return _diversify(ranked, top_k=top_k)


def _diversify(candidates: list[RetrievalCandidate], *, top_k: int) -> list[RetrievalCandidate]:
    """Lightweight MMR-like reranking to reduce near-duplicate chunks."""
    selected: list[RetrievalCandidate] = []
    remaining = list(candidates)
    while remaining and len(selected) < top_k:
        if not selected:
            selected.append(remaining.pop(0))
            continue
        best_index = 0
        best_score = float("-inf")
        for index, candidate in enumerate(remaining):
            candidate_embedding = _hashed_embedding(candidate.text)
            redundancy = max(
                _cosine(candidate_embedding, _hashed_embedding(item.text)) for item in selected
            )
            mmr = 0.8 * candidate.combined_score - 0.2 * redundancy
            if mmr > best_score:
                best_index = index
                best_score = mmr
        selected.append(remaining.pop(best_index))
    return selected

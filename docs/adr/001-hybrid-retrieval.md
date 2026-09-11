# ADR 001 — Hybrid retrieval before external vector infrastructure

## Status
Accepted

## Context
The case needs retrieval behavior that is testable, scored and reproducible without requiring an external embedding API during CI.

## Decision
Use a hybrid ranker that combines BM25-style lexical relevance with a deterministic feature-hashed dense representation, then applies an MMR-like diversification step. Expose citation scores and the retrieval method in the API.

## Consequences
- CI remains deterministic and offline.
- Retrieval quality can be benchmarked independently of an embedding vendor.
- The dense representation is intentionally a development baseline, not a claim of state-of-the-art semantic embeddings.
- A production embedding/vector provider can replace the dense scoring path behind the same contract.

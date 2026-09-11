# Architecture

## Goal

Financial Research Agent is designed as an auditable AI-engineering case rather than a thin model wrapper. Financial calculations stay deterministic; retrieval, routing, verification, observability and evaluation are explicit system layers.

## Request flow

```text
Client
  |
  v
FastAPI + Pydantic validation
  |
  +--> /documents --> parsing --> chunking --> structured extraction
  |                                      |
  |                                      v
  |                              Hybrid Retrieval
  |                         BM25 + hashed dense score
  |                                  + MMR
  |
  +--> /analyses
          |
          v
   Research Agent / Tool Call
          |
          v
   FinancialDataProvider
     mock | BRAPI
          |
          v
   Deterministic Metrics
          |
          v
      Model Router
          |
          v
   Financial Analysis Agent
          |
          v
       Verifier
          |
          v
 Structured AnalysisResult
          |
          +--> traces / latency / tools / model policy / cost
          +--> versioned evals / CI gate
```

## Design principles

1. **Evidence before narrative**: source provenance and citations are first-class data.
2. **Deterministic math**: ratios are calculated in Python, never delegated to an LLM.
3. **Explicit routing**: tasks choose a model policy through `ModelRouter`; provider-specific model calls can be added behind the policy without changing domain code.
4. **Independent verification**: the verifier has a separate routing policy and checks provenance, finite metrics, confidence consistency and risk evidence.
5. **Hybrid retrieval**: lexical relevance and a deterministic dense feature representation are combined, then diversified with MMR-like reranking.
6. **Failure is observable**: tool errors, insufficient data, latency and run status are captured in a trace.
7. **Quality is executable**: tests and versioned evals run in CI and can block regressions.
8. **Economics are measurable**: token usage and estimated cost are modeled per run even when local deterministic implementations report zero tokens.
9. **Guardrails are outside prompts**: upload limits and obvious prompt-injection patterns are enforced before retrieval.

## Production extension points

The repository intentionally keeps development storage in memory so it can run locally with no infrastructure. Production evolution should replace these interfaces, not rewrite the domain flow:

- document store -> PostgreSQL + pgvector or managed vector DB
- trace store -> OpenTelemetry/Langfuse-compatible backend
- deterministic dense retrieval -> hosted/local embedding provider
- synchronous request path -> queue + workers for long-running analyses
- in-process auth -> OIDC/RBAC gateway
- model policy -> real hosted/local model adapters

## What is intentionally not faked

The repository does not claim durable persistence, production authentication, real LLM token usage, or distributed workers when those components are not actually running. The case focuses on demonstrating the engineering contracts required to add them safely.

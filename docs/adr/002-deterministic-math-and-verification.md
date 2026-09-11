# ADR 002 — Deterministic financial math with independent verification

## Status
Accepted

## Context
Financial analysis is high-risk for silent numerical errors when arithmetic is delegated to probabilistic models.

## Decision
Calculate financial ratios in Python from typed inputs. Use AI/model layers for interpretation and workflow decisions, not arithmetic. Run a separate verification stage with its own routing policy before returning the final structured result.

## Consequences
- Numerical calculations are unit-testable and reproducible.
- Model changes do not change financial formulas.
- Verification can evolve independently from the analysis model.
- Provenance, confidence and unsupported claims remain inspectable in traces.

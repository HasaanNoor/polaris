# ADR 001: Project Principles

## Status

Accepted for Phase 0.

## Context

Polaris investigates societal questions where evidence can be incomplete, contested, or easily overinterpreted. The project needs enforceable principles before implementation begins.

## Decision

Polaris will prioritize evidence before explanation, reproducibility, provenance, uncertainty, explicit limitations, and cautious interpretation. It will distinguish descriptive, correlational, predictive, quasi-experimental, experimental, and synthesized evidence. It will not treat AI-generated explanation as evidence.

## Consequences

Reports must be artifact-backed. Quantitative claims must be traceable to deterministic analysis. The system must be able to stop with insufficient evidence, unsupported causal interpretation, non-robust results, or conflicting sources.

## Alternatives Considered

Start with a general-purpose AI research assistant: rejected because it would blur evidence, inference, and narrative generation.

Start with a dashboard-only tool: rejected because it would not encode research principles, provenance, or interpretation boundaries.

# ADR 003: Deterministic Analytical Core

## Status

Accepted for Phase 0.

## Context

Polaris must support reproducible empirical investigation. Data transformations, statistical calculations, diagnostics, estimates, and artifacts need to be auditable and repeatable.

## Decision

Polaris will keep data transformations, statistical calculations, causal estimates, diagnostics, and reproducible results deterministic. LLMs may assist selected language-heavy tasks later, but they must not calculate authoritative statistics, override analytical outputs, or independently assert causal conclusions.

## Consequences

Analytical services require explicit schemas, tests, and provenance records. This limits early flexibility but protects research integrity and reproducibility.

## Alternatives Considered

LLM-first analysis: rejected because it cannot provide the required auditability for quantitative results.

Manual-only analysis with report generation: rejected because it would not provide a structured, repeatable investigation artifact.

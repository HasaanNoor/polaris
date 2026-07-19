# ADR 002: Mandatory Multi-Agent Architecture

## Status

Accepted for Phase 0.

## Context

Societal research requires separable responsibilities across question interpretation, dataset selection, domain review, data quality, statistical analysis, causal-identification assessment, criticism, and synthesis.

## Decision

Polaris will use mandatory multi-agent orchestration. Agents must communicate through typed structured inputs and outputs. Initial agents will use deterministic strategies. Selected agents may later use evidence-grounded LLM strategies without changing their external contracts.

## Consequences

The architecture has more coordination overhead than a single-service design, but it makes responsibilities testable and failures easier to isolate. It also allows incremental implementation of target agent roles.

## Alternatives Considered

Single monolithic research service: rejected because it would make responsibilities, validation, and failure handling harder to audit.

Optional agents added later: rejected because orchestration is foundational to the research model rather than a user-interface enhancement.

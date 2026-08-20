# ADR-026: Real-World Causal Study Registry

## Status

Accepted.

## Context

Phase 22 added explicit Difference-in-Differences and event-study estimators, but its examples deliberately used synthetic treatment assignments because Polaris did not yet have reviewed intervention metadata. Running causal estimators before preserving treatment dates, treated entities, timing semantics, and source references would invite unsupported causal designs.

## Decision

Phase 23 adds a deterministic causal-study registry under `src/polaris/causal_studies` backed by tracked JSON metadata in `data/causal_studies`. A `CausalStudyDefinition` separates intervention metadata, treatment assignments, treatment sources, annual timing rules, proposed outcomes/covariates, comparison policy, design assumptions, and review status. `DesignReadinessAssessment` checks source references, entity compatibility, temporal coverage, pre/post periods, candidate controls, variable availability, and unsupported staggered treatment before a caller can convert reviewed metadata into a Phase 22 `CausalSpecification`.

Treatment metadata is separate from estimation. Phase 23 does not estimate effects, select controls, discover interventions, infer dates from outcomes, choose causal designs, or make causal claims. Announcement, adoption, effective, and implementation dates remain distinct, and the annual treatment-year mapping is explicit. Controls are diagnosed as candidates or accepted only when explicitly supplied; they are not automatically selected. Dataset compatibility is assessed before estimation, but design-ready means only that metadata and data structure are sufficient to attempt the specified design. It does not mean the design is causally valid or that identifying assumptions are true.

Interventions require source provenance because treatment dates and assignments must be reviewable. Source documentation establishes treatment metadata, not causal validity. Treatment sources remain distinct from literature evidence and empirical evidence. Registry metadata is Git-tracked because the treatment definition is part of the reproducible design identity; raw provider datasets and copyrighted source documents remain outside tracked code directories. Autonomous intervention discovery is deferred because it would need separate review, source archiving policy, and false-positive controls.

## Consequences

Polaris can now bridge reviewed treatment metadata to Phase 22 without weakening causal guardrails. MCP exposes read-only causal-study listing, inspection, and readiness assessment. Phase 13 requests may reference a causal-study ID, but that reference does not execute causal analysis without an explicit Phase 22 specification. Reports can render registry provenance when a causal result originated from registered metadata.

The first tracked definitions are templates, not real-world case studies. They remain draft or blocked until authoritative sources and reviewed assignments are supplied. A real case study should not proceed when treatment metadata, source review, explicit timing, compatible variables, control selection, or pre/post coverage is insufficient.

## Alternatives Considered

- Infer treatment events from outcome breaks or correlations: rejected because it violates causal-design provenance.
- Let LLMs propose treatment metadata: rejected because generated metadata is not a preserved source.
- Merge treatment sources into literature evidence: rejected because source documents for intervention timing are not empirical literature evidence.
- Automatically select comparison groups: rejected because control-group validity is a human design decision.
- Add new estimators such as synthetic control, IV, RDD, matching, or propensity scores: rejected because Phase 23 is metadata readiness, not estimation expansion.

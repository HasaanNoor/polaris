# ADR 027: Causal Robustness Analysis

## Status

Accepted for Phase 24.

## Context

Phase 22 introduced explicit Difference-in-Differences and event-study estimators. Phase 23
introduced reviewed causal-study metadata and deterministic conversion into a Phase 22
`CausalSpecification`. Phase 24 needs sensitivity analysis without turning robustness checks into
estimation logic or specification search.

## Decision

Polaris keeps robustness analysis in `polaris.analysis.robustness`, downstream of causal
estimation. A `RobustnessSpecification` contains exactly one baseline `CausalSpecification` and
explicit `RobustnessVariant` records. Each variant has a methodological rationale and records the
specific fields it changes.

Robustness variants call Phase 22 estimation rather than duplicating DiD or event-study logic.
Failed variants remain visible in `RobustnessAnalysisResult`.

## Rationale

Robustness follows causal estimation because it contextualizes an approved baseline result. It is
separate from the estimator so Phase 22 remains responsible for estimation and Phase 24 remains
responsible for sensitivity characterization.

Variants must be explicit because Polaris does not specification-mine. It does not automatically
search controls, windows, covariates, or placebo assignments, and it does not optimize p-values.

Polaris does not expose an overall robustness score. It reports dimensions such as estimate range,
sign consistency, significance changes, confidence-interval overlap, placebo findings,
leave-one-out sensitivity, failed variants, and pre-trend diagnostics.

Placebo tests are diagnostics, not automatic proof or disproof of a design. Leave-one-out analysis
is included because small treated or control groups can be dominated by a single entity. Failed
variants remain visible because hiding them would bias interpretation.

Robustness does not prove identifying assumptions. Reports retain conditional causal language:
estimates are stable only conditional on the design's identifying assumptions.

Real causal execution requires Phase 23 readiness. If a registered study is not reviewed,
metadata-valid, data-compatible, and design-ready, Polaris refuses real execution and may use
synthetic validation instead.

## Consequences

The workflow is opt-in. Ordinary Phase 4, Phase 21, Phase 22, Phase 23, Phase 13, Phase 18, and MCP
paths remain available without robustness configuration.

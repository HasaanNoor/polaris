# ADR-025: Causal Inference Foundations

## Status

Accepted for Phase 22.

## Context

Phase 21 added explicit longitudinal panel analysis, fixed effects, first differences, lags, and entity-clustered uncertainty. Those methods support within-entity longitudinal association, not causal identification by themselves. Polaris now needs a first causal-design layer that preserves the distinction between statistical association, longitudinal conditional association, and explicitly specified causal research design.

## Decision

Phase 22 adds an opt-in causal-analysis package under `polaris.analysis.causal` with frozen typed `CausalSpecification` and `CausalAnalysisResult` contracts. Difference-in-Differences is the first supported causal estimator because it naturally follows panel support while forcing treatment timing, treated/control groups, comparison structure, outcome, covariates, and estimand to be supplied explicitly.

Treatment timing must be supplied by the user or caller. Polaris does not discover interventions, infer treatment from outcomes, or construct causal designs from words such as "impact" or "effect." Parallel trends is represented as a structured assumption with diagnostics; non-significant pre-treatment coefficients are not treated as proof. Event-study output is included because it provides deterministic event-time construction, reference-period handling, and pre-treatment coefficient reporting.

Entity-clustered uncertainty reuses the Phase 21 panel covariance implementation. Phase 22 restricts treatment timing to common-start simple designs and rejects unsupported staggered adoption rather than reporting naive TWFE staggered-treatment coefficients as generally valid causal estimates.

Instrumental variables, regression discontinuity, synthetic control, propensity scores, inverse probability weighting, causal forests, double machine learning, mediation, VAR, Granger causality, dynamic panel GMM, Bayesian causal inference, and automatic treatment/policy discovery are deferred.

Evidence extraction now supports causal-design evidence and conditional causal claim candidates. Reasoning and reporting preserve conditional language: causal wording is allowed only under the supplied design and identifying assumptions. Mechanism reasoning remains separate and unproven unless mechanism evidence exists.

## Consequences

Polaris can now produce deterministic DiD and event-study causal-design artifacts, but only from explicit causal specifications that pass structural validation. Results surface treatment/control counts, clustered uncertainty, assumption records, pre-treatment diagnostics, limitations, and provenance. Real-world treatment metadata is not invented; examples use synthetic data unless reviewed intervention metadata exists locally.

## Alternatives considered

- Treat panel fixed effects as causal: rejected because fixed effects alone do not identify causal effects.
- Infer causal designs from natural language: rejected because treatment timing and comparison structure are methodological inputs, not text-mining outputs.
- Support staggered TWFE immediately: rejected because naive TWFE can be misleading under heterogeneous treatment effects.
- Add a broad causal inference package: rejected in favor of a narrow deterministic implementation aligned with Polaris contracts.

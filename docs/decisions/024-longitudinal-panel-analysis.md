# ADR-024: Longitudinal Panel Analysis

## Status

Accepted.

## Context

Polaris now has harmonized country-year data from WDI, WHO, WGI, and UNESCO. Phase 4 pooled OLS can estimate cross-sectional conditional associations, but it does not explicitly account for persistent country differences or common year shocks. Longitudinal country-year questions need a deterministic method that uses within-country change while preserving Phase 4 result compatibility.

## Decision

Polaris extends the Phase 4 analysis package with explicit panel procedures: `panel_entity_fe`, `panel_two_way_fe`, and `first_difference`. Panel analysis remains inside `src/polaris/analysis` and returns the existing `AnalysisResult` envelope with a compatible `PanelRegressionResult`.

Panel specifications must declare generic entity and time variables. The default country-year examples use `canonical_country_code` and `year`, but the analytical engine does not hard-code those names. Entity fixed effects are estimated with within-entity demeaning. Two-way fixed effects use deterministic double demeaning: value minus entity mean minus time mean plus the overall mean. Intercepts are not reported for transformed fixed-effects models because they are not substantively interpretable.

Entity-clustered standard errors are required for panel regression in Phase 21. The implementation uses a cluster-robust sandwich covariance estimator with finite-sample correction and records cluster count. Low cluster counts produce warnings rather than silent confidence. Unbalanced panels are supported and reported; Polaris does not fabricate missing entity-years.

Lags must be explicitly requested. Lagged variables are generated within entity after deterministic sorting by entity and time. Strict calendar-lag semantics are used: if a one-period lag is requested and the previous observed time is two periods earlier, the lag is missing and the row is excluded by complete-case rules. Lag operations record generated variable IDs, rows lost, and missing-lag reasons.

Fixed effects improve longitudinal association estimates but do not automatically identify causal effects. Difference-in-differences, IV, RDD, synthetic control, matching, causal forests, forecasting, VAR, Granger causality, dynamic panel GMM, random effects, Bayesian models, and machine-learning estimators are deferred.

## Consequences

Panel outputs include panel sample summaries, balanced/unbalanced status, entity and time coverage, within/between variation, transformed condition number, clustered uncertainty, model-fit metrics, lag provenance, and non-causal findings. Phase 5 evidence extraction, Phase 13 orchestration, Phase 18 reasoning, Phase 19 evaluation, and Phase 20 MCP tools consume panel results through existing contracts.

Country fixed effects account for stable country-specific differences. Year fixed effects account for common period shocks. Neither addresses every omitted time-varying confounder, measurement problem, serial-correlation issue, or cross-sectional dependence concern. Entity clustering helps uncertainty estimation for repeated observations but does not solve all time-series dependence.

## Alternatives Considered

Explicit dummy variables were considered for fixed effects. Demeaning was chosen because it avoids expanding result terms with many entity/year indicators and keeps reported coefficients focused on modeled predictors.

A separate `polaris.panel` application package was rejected because panel regression is an extension of Phase 4 analysis, not a separate research engine.

Automatic lag selection and automatic control selection were rejected to preserve explicit methodology and deterministic provenance.

Random-effects models and causal-inference designs were deferred because they require additional assumptions, diagnostics, and documentation beyond Phase 21.

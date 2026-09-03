# Causal Inference Methodology

Polaris distinguishes three evidence levels:

Correlation / OLS -> association.

Panel fixed effects / first differences -> within-entity longitudinal association.

Difference-in-Differences / event study -> conditional causal-design estimate under explicit identifying assumptions.

Phase 22 causal analysis is opt-in. A caller must supply `CausalSpecification` with treatment assignment, treatment timing, treated and comparison groups, outcome, windows, covariates, fixed effects, clustering, estimand, and event-study settings when applicable. Polaris does not infer causal mode from research-question wording and does not discover treatment events.

Supported methods are simple Difference-in-Differences component means, TWFE DiD for common-treatment-timing simple designs, and TWFE event-study estimates with explicit reference period and event window. Entity-clustered standard errors reuse Phase 21 covariance logic.

Parallel trends, no anticipation, stable treatment definition, comparison-group appropriateness, contamination/spillover, outcome measurement consistency, and compositional stability are recorded as structured assumptions. Diagnostics can flag concerns or insufficient data, but they do not prove identifying assumptions.

Staggered adoption is rejected in Phase 22 unless all treated entities share one treatment start. Post-treatment covariates produce a structured caution because bad controls can bias causal estimates.

Phase 23 adds reviewed treatment-metadata readiness before estimation. A causal-study definition may preserve intervention dates, treatment assignments, source references, annual timing rules, proposed outcome/covariate variable IDs, comparison policy, and review status. The workflow is:

Reviewed external intervention sources -> `CausalStudyRegistry` -> `DesignReadinessAssessment` -> human-approved `CausalSpecification` -> Phase 22 -> `CausalAnalysisResult`.

Design-ready does not mean causally valid. It means Polaris has enough explicit treatment metadata and compatible data structure to attempt the specified design. Treatment dates are never inferred from outcome changes, statistical breakpoints, correlations, LLM suggestions, vague descriptions, undocumented dates, or external facts without preserved sources. Announcement, adoption, effective, and implementation dates are distinct, and annual mappings such as `effective_date=2012-07-01` to `analysis_treatment_year=2013` must be explicit.

Phase 24 robustness analysis is opt-in and downstream of Phase 22 estimation. A
`RobustnessSpecification` must name one baseline causal analysis and explicit variants for
alternative windows, controls, covariates, leave-one-out checks, placebo timing or assignment, and
event-study windows. Polaris does not search all possible specifications, choose controls by
significance, rank variants, or compute a robustness score.

```text
Causal estimate
Robustness checks
Sensitivity characterization
!=
Proof of causality
```

Placebo and pre-trend diagnostics are warnings or supporting diagnostics, not automatic proof or
disproof. Stable estimates remain conditional on identifying assumptions.

## Phase 25 Causal Visualizations

Phase 25 can visualize existing Phase 22 and Phase 24 causal artifacts, including ATT estimates,
event-time coefficients, robustness variants, failed variants, leave-one-out diagnostics, and
placebo diagnostics. Event-study plots preserve the omitted reference period, event-time ordering,
zero-effect reference line, treatment-time reference line, missing event periods, and pre/post
labels. These figures do not prove parallel trends or causal validity; they make the existing
design and diagnostics easier to inspect.

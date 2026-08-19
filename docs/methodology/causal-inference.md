# Causal Inference Methodology

Polaris distinguishes three evidence levels:

Correlation / OLS -> association.

Panel fixed effects / first differences -> within-entity longitudinal association.

Difference-in-Differences / event study -> conditional causal-design estimate under explicit identifying assumptions.

Phase 22 causal analysis is opt-in. A caller must supply `CausalSpecification` with treatment assignment, treatment timing, treated and comparison groups, outcome, windows, covariates, fixed effects, clustering, estimand, and event-study settings when applicable. Polaris does not infer causal mode from research-question wording and does not discover treatment events.

Supported methods are simple Difference-in-Differences component means, TWFE DiD for common-treatment-timing simple designs, and TWFE event-study estimates with explicit reference period and event window. Entity-clustered standard errors reuse Phase 21 covariance logic.

Parallel trends, no anticipation, stable treatment definition, comparison-group appropriateness, contamination/spillover, outcome measurement consistency, and compositional stability are recorded as structured assumptions. Diagnostics can flag concerns or insufficient data, but they do not prove identifying assumptions.

Staggered adoption is rejected in Phase 22 unless all treated entities share one treatment start. Post-treatment covariates produce a structured caution because bad controls can bias causal estimates.

# ADR 007: Deterministic Statistical Engine

## Status

Accepted for Phase 4.

## Context

Phase 3 can determine whether a local CSV file can be safely interpreted according to a dataset manifest. Polaris now needs a deterministic statistical layer that consumes those validated normalized records and an explicit `StatisticalSpecification`.

This phase must preserve the boundary between statistical execution and interpretation. It must not select datasets, select methods with an LLM, infer causality, generate narrative conclusions, add agents, expose APIs, add databases, create a frontend, download external data, or silently impute missing values.

The Phase 1 specification already represents analysis type, model family, outcome variable, exposure variables, covariates, missing-data strategy, confidence level, and causal claim level. It did not explicitly distinguish Pearson from Spearman correlation, so Phase 4 adds one backward-compatible optional refinement field, `procedure`, using a small controlled enum.

## Decision

Polaris will add `src/polaris/analysis` as a deterministic statistical package. Its public entry point is `run_analysis(request=AnalysisRequest(...))`. The request embeds a successful `DatasetIngestionResult`, an explicit `StatisticalSpecification`, optional deterministic execution settings, optional significance threshold, optional confidence level, and a supported missing-data policy.

Supported Phase 4 procedures are:

- descriptive statistics;
- Pearson correlation;
- Spearman correlation;
- ordinary least squares regression.

Binary logistic regression is deferred. The existing schema can name a logistic model family, but correct implementation would require additional binary-class mapping contracts, convergence reporting, separation handling, and broader diagnostics. Deferring it keeps Phase 4 coherent and testable.

NumPy and SciPy are adopted. NumPy provides deterministic local arrays and linear algebra. SciPy provides correlation tests and distribution functions for p-values, confidence intervals, and diagnostics. Statsmodels remains deferred because it is not already available in the local environment and Phase 4's initial OLS scope can be implemented directly with NumPy/SciPy while preserving coefficients, standard errors, confidence intervals, fit statistics, and diagnostics. Pandas and scikit-learn are not adopted; Phase 3 already provides normalized records, and scikit-learn is not the right inferential regression dependency for standard errors and p-values.

Analyses use complete-case sample construction only. The sample builder preserves accepted-record order, included row numbers, source line numbers, excluded row numbers, and exclusion reasons. Missing values are not filled or inferred.

Regression diagnostics report facts without automatically changing models. Phase 4 includes condition number, VIF where eligible, residual normality testing where sample size supports it, Breusch-Pagan heteroskedasticity testing where meaningful, leverage summary, and Durbin-Watson over preserved row order. Undefined and not-applicable diagnostics are typed statuses rather than invalid JSON numbers.

Result identifiers are deterministic SHA-256 digests over source checksum, canonicalized statistical specification, procedure, and analysis schema version. Timestamps remain real execution metadata and are not part of the deterministic result-id guarantee.

## Consequences

Polaris can now produce typed analytical artifacts from validated local data without network access, databases, APIs, frontends, agents, or LLMs. Results preserve source checksum, specification, included and excluded row numbers, dependency versions, software version, execution settings, and analysis provenance.

The analysis layer rejects unsupported or incompatible specifications before low-level numerical routines run. It rejects unknown variables, non-numeric variables for numeric methods, duplicate predictors, dependent variables reused as predictors, unsupported grouping, weighting, fixed effects, transformations, standard-error options, unsupported methods, insufficient sample sizes, and non-analysis-ready ingestion results.

The system reports numerical evidence, assumptions, warnings, and limitations but does not produce research conclusions. Regression adjustment and statistical detectability are not treated as causal identification.

Future methods can be added by extending the `StatisticalProcedure` enum, compatibility validation, method-specific result models, diagnostics, examples, tests, and documentation while preserving existing result contracts.

## Alternatives considered

Statsmodels for OLS and logistic regression: deferred for Phase 4 because the dependency is not currently available locally and logistic regression requires a stronger method contract. It remains a good candidate for later inferential modeling expansion.

Pandas dataframes: rejected for Phase 4 because normalized Phase 3 records are already small, typed, ordered, and sufficient for deterministic sample construction.

scikit-learn regression: rejected because Phase 4 requires inferential outputs such as standard errors, confidence intervals, p-values, and diagnostics rather than prediction-oriented estimators.

LLM-based method selection or interpretation: rejected because the statistical specification is the source of truth and Phase 4 must not generate narrative or causal conclusions.

Automatic imputation: rejected because missing-data handling must be explicit, auditable, and deferred until stronger imputation contracts exist.

Databases, APIs, agents, and frontends: deferred because Phase 4 is a local deterministic analytical layer only.

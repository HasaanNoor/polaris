# Statistical Reporting

## Purpose

This policy defines minimum reporting requirements for quantitative outputs.

## Required Reporting Fields

Every statistical output must include:

- dataset and source version;
- unit of analysis;
- sample or observation count;
- inclusion and exclusion criteria;
- variable definitions;
- missing-data treatment;
- model or statistic specification;
- estimate or statistic;
- uncertainty measure where applicable;
- effect size where applicable;
- diagnostics;
- robustness or sensitivity checks where appropriate;
- limitations and practical significance.

## Phase 4 Deterministic Analysis Boundary

Phase 4 statistical results are machine-readable analytical artifacts, not narrative research conclusions. Supported procedures are descriptive statistics, Pearson correlation, Spearman correlation, and ordinary least squares regression. Each analysis must be requested through an explicit statistical specification and run only against a successful Phase 3 ingestion result.

Phase 4 uses complete-case analysis only. Rows excluded for missing required variables must be reported with source row numbers and variable identifiers. Missing values are not imputed, filled, interpolated, or treated as zero.

Correlation results report coefficients, p-values where supported, observation counts, missing-row exclusions, and warnings for undefined or constant-variable cases. They do not label relationships as substantively strong or weak and do not claim causation.

OLS results report coefficients, standard errors, test statistics, p-values, confidence intervals, threshold comparisons only when an explicit threshold is provided, fit statistics, residual and fitted-value summaries, diagnostics, and warnings. Diagnostics report calculated facts or not-applicable statuses; they do not automatically modify the requested model.

## Effect Sizes

Reports must distinguish statistical detectability from practical significance. Effect sizes should be expressed in interpretable units when possible. Standardized measures may be included when they aid comparison, but they must not replace substantive interpretation.

## Multiple Comparisons

When many outcomes, subgroups, countries, indicators, or model specifications are tested, the artifact must record the comparison family, whether adjustment was applied, and whether findings should be treated as exploratory.

## Robustness and Sensitivity

Robustness checks are required when reasonable alternative specifications, variable definitions, missing-data choices, weighting schemes, or source selections could change interpretation. Sensitivity analysis should be reported as evidence about stability, not as a cosmetic appendix.

## Survey Data

Survey-based claims must report sampling frame, collection mode, weighting, design effects when available, field dates, subgroup sample sizes, nonresponse risks, and wording limitations. Margins of error do not cover all survey error.

## Cross-Country Comparability

Cross-country statistics require checks for harmonized definitions, coverage, collection method, revision practice, denominators, and institutional context. Composite indicators require transparency about normalization, weighting, aggregation, and sensitivity to design choices.

## References

- OECD/European Union/EC-JRC, [Handbook on Constructing Composite Indicators: Methodology and User Guide](https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html).
- Pew Research Center, [U.S. Survey Methodology](https://www.pewresearch.org/u-s-survey-methodology/).
- What Works Clearinghouse, [Procedures and Standards Handbooks](https://ies.ed.gov/ncee/wwc/Handbooks).
- OECD, [Recommendation of the Council on Good Statistical Practice](https://legalinstruments.oecd.org/public/doc/331/body-text.en.html).

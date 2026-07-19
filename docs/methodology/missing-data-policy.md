# Missing Data Policy

## Purpose

Missing data can alter descriptive summaries, estimates, uncertainty, and interpretation. Polaris must make missingness visible and auditable.

## Core Rules

- Missing data must never be silently imputed.
- Missingness must be measured, reported, and linked to affected variables, geographies, periods, and populations.
- Imputed observations must remain identifiable.
- Transformed values derived from missing or imputed inputs must remain traceable.
- No single missing-data method is mandatory for every situation.

## Required Missingness Assessment

Investigations must record:

- missingness rates by variable and key subgroup;
- missingness patterns across geography and time;
- whether missingness appears structural, administrative, survey-related, or random;
- source-provided quality flags;
- affected analytical specifications;
- decision rationale for exclusion, imputation, modeling, or sensitivity checks.

## Allowed Responses

Complete-case analysis may be used when justified and limitations are reported.

Indicator exclusion may be used when missingness undermines interpretability.

Imputation may be used only when the method, assumptions, affected observations, and sensitivity checks are recorded.

Model-based handling may be used only when supported by the analytical method and documented assumptions.

Sensitivity analysis is required when missingness could materially change interpretation.

## Prohibited Responses

- replacing missing values without flags;
- hiding excluded observations;
- treating source gaps as zero;
- comparing countries or periods when coverage differences dominate interpretation;
- allowing an LLM to infer missing values as evidence.

## References

- World Bank DIME, [Reproducible Research](https://dimewiki.worldbank.org/Reproducible_Research).
- WHO, [Data Quality Assurance](https://www.who.int/data/data-collection-tools/health-service-data/data-quality-assurance-dqa).
- OECD/European Union/EC-JRC, [Handbook on Constructing Composite Indicators: Methodology and User Guide](https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html).

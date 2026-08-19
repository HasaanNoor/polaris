# Causal Language Policy

## Purpose

This policy governs when Polaris may use causal wording. The default is cautious, non-causal language unless an explicit identification assessment supports stronger interpretation.

## Evidence Categories and Language

Descriptive: use "level", "trend", "distribution", "gap", or "difference".

Correlational: use "associated with", "correlates with", or "relationship between".

Predictive: use "predicts in the evaluated model" or "forecast performance".

Quasi-experimental: use causal wording only with an explicit design, assumptions, diagnostics, and limitations.

Experimental: use causal wording only when randomization, implementation, attrition, compliance, and measurement issues are assessed.

Synthesized: use "evidence suggests" only when source quality and consistency support that wording.

## Causal Language Requires

- a clearly defined intervention, exposure, or treatment;
- a clearly defined outcome;
- a defensible comparison condition;
- temporal alignment;
- an explicit identification strategy;
- documented assumptions;
- threats to validity;
- robustness or sensitivity checks where appropriate;
- limitations and external-validity caveats.

## Insufficient Bases

Causal wording is not allowed based only on:

- temporal ordering;
- regression adjustment;
- fixed effects, first differences, lagged predictors, or clustered standard errors without a separate identification design;
- predictive accuracy;
- statistical significance;
- Phase 5 evidence extraction or claim-candidate generation;
- Phase 6 domain-agent relevance or concern codes;
- Phase 7 coordination, agreement, divergence, evidence-gap, or domain-gap records;
- Phase 8 synthesis artifacts, domain summaries, cross-domain findings, grounding findings, and fallback prose;
- an LLM-generated explanation.

## Panel Language

Pooled OLS may be described as a cross-row or cross-country conditional association. Entity fixed effects may be described as a within-entity longitudinal conditional association. Two-way fixed effects may be described as a within-entity longitudinal conditional association accounting for common time effects.

Allowed: "Higher government effectiveness is associated with higher life expectancy within countries over time under the specified fixed-effects model."

Disallowed: "Improving government effectiveness increases life expectancy" or "fixed effects prove that governance caused life expectancy changes."

## Required Stop Conditions

The Causal Identification Agent must mark causal interpretation unsupported when the question lacks a comparison strategy, data cannot identify the relationship, assumptions are not defensible, diagnostics fail, robustness checks are unstable, or sources conflict in ways that affect the claim.

## References

- What Works Clearinghouse, [Procedures and Standards Handbooks](https://ies.ed.gov/ncee/wwc/Handbooks).
- World Bank DIME, [DIME Research](https://www.worldbank.org/en/about/unit/unit-dec/impactevaluation/dime-research).
- World Bank DIME, [Experimental Methods](https://dimewiki.worldbank.org/Experimental_Methods).

## Phase 22 Causal-Design Language

Phase 22 permits causal wording only for explicit causal-design evidence produced from a validated `CausalSpecification`. Acceptable wording is conditional, such as: "Under the Difference-in-Differences design and its identifying assumptions, the estimated ATT is ...". Ordinary OLS, correlations, panel fixed effects, and first differences remain associational or longitudinal-associational evidence and must not be described as proving causality.

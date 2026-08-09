# Evidence Standards

## Purpose

This policy defines how Polaris assesses evidence quality. It does not rank sources by reputation alone. It evaluates whether the evidence is fit for the specific question.

## Evidence Types

Descriptive evidence: summarizes observed measures without estimating relationships.

Correlational evidence: estimates associations without claiming identification.

Predictive evidence: evaluates out-of-sample performance or forecasting quality.

Quasi-experimental evidence: uses a design intended to address confounding under explicit assumptions.

Experimental evidence: uses randomized assignment or a reviewed experimental design.

Synthesized evidence: integrates multiple studies, datasets, or reports using explicit inclusion criteria.

## Required Assessment Dimensions

- source credibility and institutional process;
- methodological transparency;
- measurement validity;
- data quality and missingness;
- statistical uncertainty;
- design risk of bias;
- causal-identification strength where relevant;
- external validity;
- practical significance;
- consistency or conflict across sources.

## Evidence-Quality Levels

High: transparent methods, strong measurement fit, reproducible data path, appropriate statistical analysis, and low risk of bias for the stated claim.

Moderate: usable evidence with limitations that do not dominate interpretation.

Limited: evidence is relevant but has substantial uncertainty, missingness, comparability issues, weak design, or incomplete provenance.

Insufficient: evidence cannot support the requested claim.

Conflicting: credible sources point in different directions or use incompatible definitions, populations, or periods.

## Rules

- Statistical significance alone is not sufficient evidence.
- Lack of statistical significance does not establish absence of an effect.
- Effect sizes and uncertainty must be reported when estimates are presented.
- Structured Phase 5 claim candidates must reference evidence records rather than duplicate them.
- Phase 5 claim candidates are bounded machine-readable propositions, not evidence-quality ratings or narrative conclusions.
- Phase 6 domain assessments must reference Phase 5 evidence and claim IDs rather than duplicate evidence payloads.
- Phase 6 domain agents may add deterministic domain concern codes, but they must not remove Phase 5 limitations or strengthen claim candidates into causal, policy, medical, or mechanism conclusions.
- Phase 7 coordinated assessments must reconcile Phase 6 structured records by reference. Agreement means shared structured evidence, claim, limitation, unsupported inference, or concern codes; it does not mean subjective consensus or final interpretation.
- Phase 7 divergence means a deterministic domain-specific difference such as uneven coverage or domain-specific relevance. It must not be described as contradiction unless a later typed contract represents contradictory structured states.
- Phase 7 must preserve limitations and unsupported-inference warnings so later synthesis layers know which claims they must not make.
- Phase 8 synthesis may produce natural-language explanation, but every substantive domain or cross-domain statement must remain traceable to supplied Phase 7 coordination and optional matching Phase 5 evidence details. Synthesis must preserve source limitations, unsupported-inference boundaries, missing-domain coverage, and evidence gaps; it must not introduce outside facts, fabricate identifiers, calculate new numerical evidence, convert associations into causal claims, or recommend policy or medical action.
- Phase 9 reports must preserve structured Phase 3-8 evidence, limitations, unsupported-inference boundaries, provenance, and internal Polaris references. Report generation is a deterministic presentation layer; it must not create evidence, create claims, rerun analysis, call an LLM, retrieve outside sources, or present internal references as external citations.
- Phase 12 harmonized datasets are derived artifacts. They must preserve source provider identity, value-level provenance, units, definitions, missingness reasons, aggregate exclusions, duplicate findings, and conflict findings so later analysis and reports do not mistake harmonized convenience for source equivalence.
- Phase 14 literature context is not empirical evidence. Retrieved chunks must come from a supplied local corpus, preserve citation metadata, remain linked to empirical claim IDs, and be reported separately from Polaris statistical findings. Lexical retrieval relevance must not be described as scientific agreement, causal validation, or a reason to change empirical results.
- Correlation and OLS claim candidates must remain non-causal unless a later causal-identification phase explicitly supports stronger claims.
- Multiple comparisons must be disclosed and, where appropriate, adjusted or treated as exploratory.
- Robustness and sensitivity analysis are required when model choices, missingness, variable definitions, or source selection materially affect interpretation.
- Survey evidence must report sampling frame, mode, weighting, design effects when available, nonresponse risks, and question-wording limitations.
- Cross-country comparisons must document indicator definitions, collection methods, revisions, and comparability limits.

## Institutional Differences

Institutions differ in evidence-rating systems. Education evidence frameworks may emphasize design standards and attrition; official-statistics frameworks emphasize institutional quality, methodology, accuracy, coherence, accessibility, and comparability; survey organizations emphasize total survey error and weighting. Polaris should record the applicable standard rather than forcing one universal rating.

## References

- What Works Clearinghouse, [Procedures and Standards Handbooks](https://ies.ed.gov/ncee/wwc/Handbooks).
- World Bank DIME, [Experimental Methods](https://dimewiki.worldbank.org/Experimental_Methods).
- OECD, [Recommendation of the Council on Good Statistical Practice](https://legalinstruments.oecd.org/public/doc/331/body-text.en.html).
- Pew Research Center, [U.S. Survey Methodology](https://www.pewresearch.org/u-s-survey-methodology/).
- WHO, [Data Quality Assurance](https://www.who.int/data/data-collection-tools/health-service-data/data-quality-assurance-dqa).

# Vision

## Mission

Polaris helps researchers and institutions investigate societal questions with reproducible data workflows, structured evidence assessment, and cautious interpretation.

## Problem Statement

Societal research often spans countries, time periods, data sources, and disciplines. Analysts must compare indicators, evaluate data quality, select models, handle missingness, document provenance, and explain uncertainty. These steps are commonly performed across disconnected tools, making evidence hard to audit and easy to overinterpret.

Polaris addresses this by coordinating specialized agents around a deterministic analytical core and by producing both machine-readable artifacts and human-readable reports.

## Target Users

- Researchers and graduate students.
- Policymakers and public-sector analysts.
- NGOs, think tanks, and international organizations.
- Journalists and evidence teams.
- Domain experts in governance, economics, education, health, social trust, demographics, environment, innovation, and conflict.

## Supported Use Cases

- Compare indicators across countries, regions, groups, or time.
- Assess whether available data can support a descriptive, correlational, predictive, quasi-experimental, experimental, or synthesized claim.
- Identify plausible datasets for a research question.
- Document provenance, transformations, missingness, model choices, diagnostics, and limitations.
- Generate reproducible research artifacts and cautious reports.
- Represent conflicting evidence without suppressing it.

## Scope

Polaris covers empirical investigation into relationships among societal conditions and outcomes. It may support descriptive statistics, exploratory analysis, correlational analysis, predictive modeling, causal-identification assessment, evidence synthesis, and report generation.

## Non-Goals

- Polaris is not an automatic truth engine.
- Polaris does not replace expert judgment, ethics review, statistical review, or domain review.
- Polaris does not treat LLM-generated explanations as evidence.
- Polaris does not select one universal method for every research question.
- Polaris does not approve dataset integrations in Phase 0.

## Ethical and Methodological Boundaries

Polaris must preserve uncertainty, provenance, limitations, and contradictory evidence. It must be able to conclude that evidence is insufficient, a relationship is not identifiable, results are not robust, sources conflict, or causal interpretation is unsupported.

The platform must avoid overstating evidence about countries, communities, protected groups, institutions, or conflict-affected populations. Sensitive data requires explicit provenance, licensing, privacy, and harm-review controls before use.

## Success Criteria

- Every investigation has a versioned research artifact and human-readable report.
- Quantitative claims are traceable to datasets, transformations, and deterministic analytical outputs.
- Agent outputs are typed and independently inspectable.
- Missing-data decisions are explicit and auditable.
- Causal language is allowed only when an identification assessment supports it.
- Reports clearly separate evidence, uncertainty, limitations, and interpretation.

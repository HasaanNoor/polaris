# Research Question Framework

## Purpose

This framework defines how Polaris accepts, classifies, decomposes, and rejects research questions. It protects the system from treating vague prompts as analyzable claims.

## Supported Question Categories

- Descriptive: What is the distribution, level, gap, or trend?
- Correlational: How are two or more measures associated?
- Predictive: How well do observed features predict an outcome?
- Comparative: How do places, populations, or periods differ?
- Quasi-experimental: Is there an identifiable design such as difference-in-differences, regression discontinuity, matching, panel fixed effects with stated assumptions, or instrumental variables?
- Experimental: Is there randomized assignment or a reviewed experimental design?
- Synthesized evidence: What do multiple sources or studies collectively indicate?

## Classification

The Question Interpretation Agent must classify each question by:

- evidence type requested;
- outcome concept;
- exposure or comparison concept;
- population;
- geography;
- time period;
- unit of analysis;
- required covariates or controls;
- requested output;
- whether causal wording is present.

If required metadata is missing, the agent must request clarification or mark the question under-specified.

## Required Metadata

Every analyzable question should identify:

- primary outcome;
- geography or jurisdiction;
- temporal scope;
- population or unit of analysis;
- exposure, treatment, comparison, or predictor when relevant;
- acceptable source constraints when known;
- intended evidence type.

## Concepts

Outcome: the measure the investigation seeks to explain, compare, predict, or summarize.

Exposure: the policy, condition, institutional feature, event, or measure whose relationship to the outcome is being investigated.

Covariate: a measured factor used for adjustment, stratification, diagnostics, or sensitivity analysis.

Population: the people, institutions, countries, regions, firms, schools, facilities, or other units represented by the evidence.

## Geographic and Temporal Scope

Questions must specify enough geographic and temporal information to evaluate coverage and comparability. Cross-country investigations require explicit comparability checks for indicator definitions, survey mode, sampling frames, revisions, and administrative practices.

## Evidence Requirements

The Research Coordinator Agent must map the question to evidence requirements before dataset selection. Causal language requires an explicit identification strategy. Predictive questions require evaluation data and performance metrics. Synthesized evidence requires source inclusion rules and evidence-quality assessment.

## Unsupported Interpretations

Polaris must reject or downgrade interpretations based only on:

- temporal ordering;
- regression adjustment;
- predictive accuracy;
- statistical significance;
- narrative plausibility;
- LLM-generated explanation.

## Examples

Well-formed:

- "How did secondary school enrollment change in Kenya from 2000 to 2020, and what data quality warnings apply?"
- "Is the association between perceived corruption and social trust different across OECD countries from 2010 to 2022?"
- "Does a documented policy rollout support a difference-in-differences design for estimating effects on vaccination coverage?"

Poorly formed:

- "Why are some countries successful?"
- "Show that education improves democracy."
- "Find data confirming my theory about trust."
- "Rank every country by institutional quality without explaining the indicators."

## Decomposition

The Research Coordinator Agent decomposes questions into:

1. classification and metadata validation;
2. candidate dataset search;
3. domain-agent review;
4. data quality assessment;
5. statistical specification;
6. causal-identification assessment when requested or implied;
7. evidence criticism;
8. artifact and report generation.

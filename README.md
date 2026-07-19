# Polaris

Agentic platform for societal intelligence and causal research.

## Status

Polaris is in **Phase 0: documentation and design specification**. The repository currently defines the project mission, research principles, architecture, methodology policies, candidate datasets, and initial roadmap. It does not yet contain application code, production infrastructure, or approved dataset integrations.

## Problem Statement

Researchers, policymakers, analysts, graduate students, NGOs, think tanks, journalists, and international organizations often need to investigate relationships among governance, economics, education, health, social trust, demographics, institutions, conflict, innovation, environment, and other societal outcomes. Existing workflows are fragmented across data portals, notebooks, statistical tools, reports, and informal interpretation.

Polaris is designed to coordinate that work while preserving methodological discipline. It supports empirical investigation, evidence review, and reproducible reporting, but it does not automatically establish causality.

## Core Principles

- Evidence before explanation.
- Correlation is not causation.
- AI assists research but does not replace statistical inference.
- Quantitative claims must be traceable to data and deterministic analysis.
- Descriptive, correlational, predictive, quasi-experimental, experimental, and synthesized evidence must be distinguished.
- Uncertainty, assumptions, limitations, provenance, effect sizes, and practical significance must be reported.
- Missing, imputed, and transformed observations must remain identifiable and traceable.
- Reproducibility is a first-class system requirement.
- Conflicting evidence must be represented rather than suppressed.

## Mandatory Multi-Agent Architecture

Polaris is inherently multi-agent. Multi-agent orchestration is mandatory, not an optional enhancement. The target architecture includes specialized agents for question interpretation, dataset selection, domain assessment, data quality, statistical analysis, causal identification, criticism, and synthesis.

Initial agent implementations will use deterministic strategies based on rules, structured parsing, metadata, dataset retrieval, statistical analysis, validation logic, evidence aggregation, and report templates. Selected agents may later use evidence-grounded LLM strategies when language reasoning materially improves interpretation, decomposition, hypothesis generation, criticism, contextualization, or synthesis.

LLMs must not invent evidence, silently introduce unsupported claims, calculate authoritative statistics instead of the analytical engine, override deterministic analytical outputs, independently assert causal conclusions, or conceal uncertainty and contradictory evidence.

## Research Workflow

1. A user submits a research question with geographic, temporal, population, outcome, exposure, and optional covariate context.
2. The Research Coordinator Agent classifies and decomposes the question.
3. Dataset and domain agents identify candidate sources and data limitations.
4. Data Quality, Statistical Analysis, and Causal Identification agents evaluate the available evidence.
5. The Evidence Critic Agent checks robustness, uncertainty, conflicts, and unsupported interpretation.
6. The Research Synthesis Agent generates a versioned machine-readable research artifact and a human-readable report.
7. The system may conclude that evidence is insufficient, a relationship is not identifiable, results are not robust, sources conflict, or causal interpretation is unsupported.

## Documentation Map

- [Vision](docs/vision.md)
- [Roadmap](docs/roadmap.md)
- [Research Question Framework](docs/research-question-framework.md)
- [System Overview](docs/architecture/system-overview.md)
- [Multi-Agent Design](docs/architecture/multi-agent-design.md)
- [Agent Strategy Model](docs/architecture/agent-strategy-model.md)
- [Research Artifact Schema](docs/architecture/research-artifact-schema.md)
- [Technology Decisions](docs/architecture/technology-decisions.md)
- [Methodology Charter](docs/methodology/charter.md)
- [Evidence Standards](docs/methodology/evidence-standards.md)
- [Dataset Source Selection](docs/datasets/source-selection.md)
- [Initial Dataset Catalog](docs/datasets/initial-catalog.md)
- [Architecture Decision Records](docs/decisions/001-project-principles.md)

## Roadmap Summary

Phase 0 completes the documentation baseline. Later phases will add schemas, deterministic analytical services, dataset ingestion, typed agent contracts, orchestration, tests, reproducible artifacts, reporting, frontend workflows, deployment, observability, and only then narrowly scoped evidence-grounded LLM enhancement where justified.

## Current Status and Next Phase

Current decision records establish Polaris as a research system with mandatory multi-agent orchestration and a deterministic analytical core. The next phase should convert the documented contracts into minimal schemas and validation tests without adding speculative application infrastructure.

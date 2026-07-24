# Polaris

Agentic platform for societal intelligence and causal research.

## Status

Polaris is in **Phase 5: structured evidence and deterministic claim extraction complete**. The repository includes typed Python schema contracts for research questions, dataset manifests, agent messages, provenance records, statistical specifications, and versioned research artifacts; a local in-memory registry for validated dataset manifests; deterministic local CSV ingestion with validation, normalization, checksums, provenance-compatible metadata, and structural data-quality profiles; deterministic statistical analysis for explicit specifications; and a deterministic evidence layer that converts statistical results into structured evidence records and bounded non-causal claim candidates. It does not yet contain application services, production infrastructure, orchestration runtime, LLM integration, dataset downloads, or approved dataset integrations.

## Package Overview

The Phase 1 package lives under `src/polaris/schemas` and uses Pydantic v2 for typed validation and JSON serialization. The schemas reject unknown fields by default, use timezone-aware UTC timestamps, and keep observed data, derived data, analytical outputs, provenance, and narrative interpretation distinct.

The Phase 2 registry package lives under `src/polaris/registry`. It loads local UTF-8 JSON manifests through the existing `DatasetManifest` schema, rejects duplicate dataset identifiers, preserves deterministic registration order, and supports structured metadata search with explainable match reasons. Registry search is metadata-only; it does not retrieve, download, transform, or analyze observations.

The Phase 3 ingestion package lives under `src/polaris/ingestion`. It resolves a registered manifest, reads a local CSV file, validates exact manifest-to-column mappings, normalizes supported scalar values, reports typed validation findings, computes SHA-256 checksums, and returns immutable ingestion results. Ingestion is local-only and does not download datasets or perform statistical analysis.

The Phase 4 analysis package lives under `src/polaris/analysis`. It consumes a successful `DatasetIngestionResult` and an explicit `StatisticalSpecification`, validates compatibility, builds a complete-case analysis sample, computes descriptive statistics, Pearson and Spearman correlations, OLS regression, diagnostics, typed findings, deterministic result identifiers, and analysis provenance. Analysis does not select datasets or methods, impute missing values, generate narrative conclusions, claim causality, or use LLMs.

The Phase 5 evidence package lives under `src/polaris/evidence`. It consumes a Phase 4 `AnalysisResult` and extracts immutable evidence records, deterministic claim candidates, claim-support links, propagated limitation codes, evidence provenance, and deterministic evidence and claim IDs. Evidence extraction does not generate narrative conclusions, infer causality, assign subjective strength labels, use LLMs, use agents, call APIs, or store data externally.

JSON schema examples are available in `examples/schemas`. Illustrative analysis specifications are available in `examples/analysis`, and illustrative evidence artifacts are available in `examples/evidence`. The illustrative metadata catalog is available in `catalog/datasets`. Small synthetic CSV examples are available in `data/examples`. Tests are available in `tests/schemas`, `tests/registry`, `tests/ingestion`, `tests/analysis`, and `tests/evidence`.

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
- [Architecture Decision Records](docs/decisions/001-project-principles.md), including [ADR-007](docs/decisions/007-deterministic-statistical-engine.md) and [ADR-008](docs/decisions/008-structured-evidence-and-claim-extraction.md)

## Roadmap Summary

Phase 0 completed the documentation baseline. Phase 1 added the minimal schema foundation. Phase 2 added deterministic local dataset-manifest loading, registration, coverage matching, warning surfacing, and structured metadata search. Phase 3 added deterministic local CSV ingestion and validation. Phase 4 added deterministic statistical analysis and diagnostics for explicit specifications. Phase 5 added structured evidence records and bounded non-causal claim candidates extracted from Phase 4 results. Later phases will add typed agent contracts, orchestration, reproducible artifact storage, reporting, frontend workflows, deployment, observability, and only then narrowly scoped evidence-grounded LLM enhancement where justified.

## Current Status and Next Phase

Current decision records establish Polaris as a research system with mandatory multi-agent orchestration, a deterministic analytical core, Pydantic-based schema contracts, an in-memory deterministic dataset registry, local CSV ingestion, and deterministic statistical execution. The next phase should continue building deterministic local capabilities without expanding into application frameworks or infrastructure.

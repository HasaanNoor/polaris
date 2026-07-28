# Polaris

Agentic platform for societal intelligence and causal research.

## Status

Polaris is in **Phase 9: structured research report generation complete**. The repository includes typed Python schema contracts for research questions, dataset manifests, agent messages, provenance records, statistical specifications, and versioned research artifacts; a local in-memory registry for validated dataset manifests; deterministic local CSV ingestion with validation, normalization, checksums, provenance-compatible metadata, and structural data-quality profiles; deterministic statistical analysis for explicit specifications; a deterministic evidence layer that converts statistical results into structured evidence records and bounded non-causal claim candidates; deterministic governance, economics, education, and public-health agents that produce structured `AgentAssessment` outputs from Phase 5 artifacts; deterministic coordination that produces structured `CoordinatedAssessment` outputs from Phase 6 assessments; a guardrailed synthesis layer that produces structured `SynthesisArtifact` outputs from Phase 7 coordination; and a deterministic reporting layer that packages Phase 3-8 artifacts into structured `ResearchReport` outputs with Markdown, HTML, and JSON rendering. It does not yet contain application services, production infrastructure, orchestration runtime, dataset downloads, approved dataset integrations, external retrieval, frontend workflows, PDF/DOCX export, or external bibliography generation.

## Package Overview

The Phase 1 package lives under `src/polaris/schemas` and uses Pydantic v2 for typed validation and JSON serialization. The schemas reject unknown fields by default, use timezone-aware UTC timestamps, and keep observed data, derived data, analytical outputs, provenance, and narrative interpretation distinct.

The Phase 2 registry package lives under `src/polaris/registry`. It loads local UTF-8 JSON manifests through the existing `DatasetManifest` schema, rejects duplicate dataset identifiers, preserves deterministic registration order, and supports structured metadata search with explainable match reasons. Registry search is metadata-only; it does not retrieve, download, transform, or analyze observations.

The Phase 3 ingestion package lives under `src/polaris/ingestion`. It resolves a registered manifest, reads a local CSV file, validates exact manifest-to-column mappings, normalizes supported scalar values, reports typed validation findings, computes SHA-256 checksums, and returns immutable ingestion results. Ingestion is local-only and does not download datasets or perform statistical analysis.

The Phase 4 analysis package lives under `src/polaris/analysis`. It consumes a successful `DatasetIngestionResult` and an explicit `StatisticalSpecification`, validates compatibility, builds a complete-case analysis sample, computes descriptive statistics, Pearson and Spearman correlations, OLS regression, diagnostics, typed findings, deterministic result identifiers, and analysis provenance. Analysis does not select datasets or methods, impute missing values, generate narrative conclusions, claim causality, or use LLMs.

The Phase 5 evidence package lives under `src/polaris/evidence`. It consumes a Phase 4 `AnalysisResult` and extracts immutable evidence records, deterministic claim candidates, claim-support links, propagated limitation codes, evidence provenance, and deterministic evidence and claim IDs. Evidence extraction does not generate narrative conclusions, infer causality, assign subjective strength labels, use LLMs, use agents, call APIs, or store data externally.

The Phase 6 agents package lives under `src/polaris/agents`. It consumes a Phase 5 `EvidenceArtifact` and returns immutable domain-specific `AgentAssessment` objects with relevance records, concern codes, inherited limitations, unsupported-inference codes, deterministic IDs, coverage summaries, and provenance. Agents are deterministic and rule-based; they do not retrieve outside context, synthesize across agents, generate narrative conclusions, infer causality, or recommend policy.

The Phase 7 coordination package lives under `src/polaris/coordination`. It consumes Phase 6 `AgentAssessment` objects and returns immutable `CoordinatedAssessment` objects with compatibility validation, domain coverage aggregation, evidence-domain mappings, claim-domain mappings, conservative agreement and divergence records, shared limitations, shared unsupported inferences, evidence gaps, domain gaps, deterministic IDs, and coordination provenance. Coordination is structural; it does not add evidence, modify claims, infer causality, rank domains, or generate report prose.

The Phase 8 synthesis package lives under `src/polaris/synthesis`. It consumes a Phase 7 `CoordinatedAssessment`, optionally with a matching Phase 5 `EvidenceArtifact` for richer claim/evidence grounding, and returns an immutable `SynthesisArtifact`. Deterministic synthesis works without credentials. LLM synthesis uses a small provider protocol, structured output validation, fabricated-reference checks, causal-language guards, policy/medical recommendation guards, limitation preservation, unsupported-inference preservation, fallback findings, and synthesis provenance. Synthesis does not inspect raw CSV files, calculate statistics, retrieve outside facts, modify coordinated assessments, infer causality, or recommend interventions.

The Phase 9 reporting package lives under `src/polaris/reporting`. It consumes explicit Phase 3-8 artifacts, validates shared lineage, builds an immutable structured `ResearchReport`, creates an internal Polaris reference index, preserves limitations and unsupported-inference boundaries, and renders deterministic JSON, Markdown, and standalone HTML. Reporting does not rerun analysis, create evidence or claims, retrieve outside facts, call an LLM, or generate external citations.

JSON schema examples are available in `examples/schemas`. Illustrative analysis specifications are available in `examples/analysis`, illustrative evidence artifacts are available in `examples/evidence`, illustrative domain assessments are available in `examples/agents`, an illustrative coordinated assessment is available in `examples/coordination`, an illustrative synthesis artifact is available in `examples/synthesis`, and illustrative reports are available in `examples/reporting`. The illustrative metadata catalog is available in `catalog/datasets`. Small synthetic CSV examples are available in `data/examples`. Tests are available in `tests/schemas`, `tests/registry`, `tests/ingestion`, `tests/analysis`, `tests/evidence`, `tests/agents`, `tests/coordination`, `tests/synthesis`, and `tests/reporting`.

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

Phase 0 completed the documentation baseline. Phase 1 added the minimal schema foundation. Phase 2 added deterministic local dataset-manifest loading, registration, coverage matching, warning surfacing, and structured metadata search. Phase 3 added deterministic local CSV ingestion and validation. Phase 4 added deterministic statistical analysis and diagnostics for explicit specifications. Phase 5 added structured evidence records and bounded non-causal claim candidates extracted from Phase 4 results. Phase 6 added deterministic domain agents that assess evidence relevance for governance, economics, education, and public health. Phase 7 added deterministic multi-agent coordination over domain assessments. Phase 8 added guardrailed interdisciplinary synthesis over coordinated assessments, with deterministic fallback and optional mockable LLM provider support. Phase 9 added deterministic structured research report generation with JSON, Markdown, and standalone HTML rendering. Later phases will add orchestration, reproducible artifact storage, frontend workflows, deployment, observability, retrieval-grounded context, and broader LLM enhancement where justified.

## Current Status and Next Phase

Current decision records establish Polaris as a research system with mandatory multi-agent orchestration, a deterministic analytical core, Pydantic-based schema contracts, an in-memory deterministic dataset registry, local CSV ingestion, deterministic statistical execution, structured evidence extraction, deterministic domain-agent assessment, deterministic coordination of structured domain outputs, and guardrailed synthesis from coordinated evidence. The next phase should continue building local capabilities without expanding into application frameworks or infrastructure.

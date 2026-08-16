# Polaris

Agentic platform for societal intelligence and causal research.

## Status

Polaris is in **Phase 19: reasoning evaluation and benchmarking complete locally**. The repository includes typed Python schema contracts for research questions, dataset manifests, agent messages, provenance records, statistical specifications, and versioned research artifacts; a local in-memory registry for validated dataset manifests; deterministic local CSV ingestion with validation, normalization, checksums, provenance-compatible metadata, and structural data-quality profiles; deterministic statistical analysis for explicit specifications; structured evidence extraction; deterministic governance, economics, education, and public-health agents; deterministic coordination; guardrailed synthesis; deterministic report generation; provider acquisition for immutable raw snapshots; real WDI validation through Phases 3-9; deterministic country-year harmonization; a lightweight in-process orchestration layer; local corpus-grounded literature retrieval; curated WHO GHO country-year panel integration; World Bank WGI governance panel integration; UNESCO UIS education panel integration; optional evidence-grounded reasoning; and deterministic reasoning evaluation. Phase 19 adds benchmark cases, expected reasoning behavior, benchmark suites, per-dimension evaluation results, deterministic/provider comparison summaries, adversarial fixtures, reproducibility checks, and JSON/Markdown benchmark reports. Polaris does not yet contain application services, production infrastructure, internet search, autonomous synchronization, frontend workflows, PDF/DOCX export, external bibliography generation, vector databases, online academic search APIs, causal estimators, autonomous policy recommendations, or an external workflow engine.

## Package Overview

The Phase 1 package lives under `src/polaris/schemas` and uses Pydantic v2 for typed validation and JSON serialization. The schemas reject unknown fields by default, use timezone-aware UTC timestamps, and keep observed data, derived data, analytical outputs, provenance, and narrative interpretation distinct.

The Phase 2 registry package lives under `src/polaris/registry`. It loads local UTF-8 JSON manifests through the existing `DatasetManifest` schema, rejects duplicate dataset identifiers, preserves deterministic registration order, and supports structured metadata search with explainable match reasons. Registry search is metadata-only; it does not retrieve, download, transform, or analyze observations.

The Phase 10 provider package lives under `src/polaris/providers`. It acquires official-provider files once, stores immutable raw snapshots under `data/raw/<provider>/`, writes checksum-bearing snapshot metadata, generates Phase 3-compatible manifests under `data/manifests/`, and exposes `download_dataset(provider="world_bank", dataset="WDI")`. Provider downloads are explicit; adapter availability does not imply that source files have already been acquired. After acquisition, registry, ingestion, analysis, evidence, coordination, synthesis, and reporting operate offline from local artifacts.

The Phase 3 ingestion package lives under `src/polaris/ingestion`. It resolves a registered manifest, reads a local CSV file, validates exact manifest-to-column mappings, normalizes supported scalar values, reports typed validation findings, computes SHA-256 checksums, and returns immutable ingestion results. Ingestion is local-only and does not download datasets or perform statistical analysis.

The Phase 4 analysis package lives under `src/polaris/analysis`. It consumes a successful `DatasetIngestionResult` and an explicit `StatisticalSpecification`, validates compatibility, builds a complete-case analysis sample, computes descriptive statistics, Pearson and Spearman correlations, OLS regression, diagnostics, typed findings, deterministic result identifiers, and analysis provenance. Analysis does not select datasets or methods, impute missing values, generate narrative conclusions, claim causality, or use LLMs.

The Phase 5 evidence package lives under `src/polaris/evidence`. It consumes a Phase 4 `AnalysisResult` and extracts immutable evidence records, deterministic claim candidates, claim-support links, propagated limitation codes, evidence provenance, and deterministic evidence and claim IDs. Evidence extraction does not generate narrative conclusions, infer causality, assign subjective strength labels, use LLMs, use agents, call APIs, or store data externally.

The Phase 6 agents package lives under `src/polaris/agents`. It consumes a Phase 5 `EvidenceArtifact` and returns immutable domain-specific `AgentAssessment` objects with relevance records, concern codes, inherited limitations, unsupported-inference codes, deterministic IDs, coverage summaries, and provenance. Agents are deterministic and rule-based; they do not retrieve outside context, synthesize across agents, generate narrative conclusions, infer causality, or recommend policy.

The Phase 7 coordination package lives under `src/polaris/coordination`. It consumes Phase 6 `AgentAssessment` objects and returns immutable `CoordinatedAssessment` objects with compatibility validation, domain coverage aggregation, evidence-domain mappings, claim-domain mappings, conservative agreement and divergence records, shared limitations, shared unsupported inferences, evidence gaps, domain gaps, deterministic IDs, and coordination provenance. Coordination is structural; it does not add evidence, modify claims, infer causality, rank domains, or generate report prose.

The Phase 8 synthesis package lives under `src/polaris/synthesis`. It consumes a Phase 7 `CoordinatedAssessment`, optionally with a matching Phase 5 `EvidenceArtifact` for richer claim/evidence grounding, and returns an immutable `SynthesisArtifact`. Deterministic synthesis works without credentials. LLM synthesis uses a small provider protocol, structured output validation, fabricated-reference checks, causal-language guards, policy/medical recommendation guards, limitation preservation, unsupported-inference preservation, fallback findings, and synthesis provenance. Synthesis does not inspect raw CSV files, calculate statistics, retrieve outside facts, modify coordinated assessments, infer causality, or recommend interventions.

The Phase 9 reporting package lives under `src/polaris/reporting`. It consumes explicit Phase 3-8 artifacts, validates shared lineage, builds an immutable structured `ResearchReport`, creates an internal Polaris reference index, preserves limitations and unsupported-inference boundaries, and renders deterministic JSON, Markdown, and standalone HTML. Reporting does not rerun analysis, create evidence or claims, retrieve outside facts, call an LLM, or generate external citations.

The Phase 12 harmonization package lives under `src/polaris/harmonization`. It consumes two or more `DatasetIngestionResult` objects, explicit dataset configs, reviewed variable mappings, and an explicit join type. It normalizes country identifiers and years, excludes aggregate entities by default, validates units and definitions, detects duplicate keys and cross-provider conflicts, records missingness reasons, preserves value-level provenance, and exports derived Phase 3-compatible CSV plus manifest artifacts.

The Phase 13 projects package lives under `src/polaris/projects`. It provides `ResearchProjectRequest`, `plan_research_project(...)`, and `run_research_project(...)` for a synchronous, single-entry workflow across dataset resolution, ingestion, optional harmonization, analysis, evidence extraction, selected domain agents, coordination, synthesis, and report generation. Project IDs are deterministic and exclude execution timestamps. Stage results preserve failure-stage metadata and completed upstream artifacts. Project-level provenance aggregates upstream artifact IDs and source checksums without replacing phase-specific provenance.

The Phase 14 literature package lives under `src/polaris/literature`. It ingests explicitly supplied local literature corpora, preserves document checksums and citation metadata, normalizes and chunks text deterministically, and retrieves relevant chunks with a local BM25-style lexical index. `LiteratureContextArtifact` records retrieved literature for existing empirical claim IDs while keeping literature claims separate from Polaris empirical evidence. Phase 8 synthesis and Phase 9 reporting can consume this optional artifact, and Phase 13 can add a `RETRIEVE_LITERATURE` stage only when a project-level literature configuration is supplied. No autonomous internet research or generated citations are supported.

The Phase 15 WHO package lives under `src/polaris/who`. It loads the local WHO GHO acquisition catalog, validates recorded SHA-256 checksums, profiles actual OData JSON snapshot schemas, applies reviewed indicator mappings and dimension filters, builds immutable `WHOHealthRecord` and `WHOHealthPanel` artifacts, records deferred indicators, and exports deterministic CSV/manifest/quality/provenance metadata. The current local catalog has 42 conceptual targets, 41 downloaded official WHO snapshots, 28 reviewed integrated indicators, and 14 deferred targets. Raw WHO files remain ignored and are not mutated.

The Phase 16 WGI package lives under `src/polaris/wgi`. It acquires official World Bank WGI source `3` API CSV ZIP snapshots under `data/raw/world_bank/wgi/`, validates checksums, profiles observed schema fields, maps the six WGI dimensions to separate canonical governance variables, preserves standard errors, source counts, absolute governance scores, and score confidence bounds as metadata, excludes aggregates and territories by default, and exports a Phase 3-compatible governance country-year panel. WGI examples are available in `examples/wgi`.

The Phase 17 UNESCO package lives under `src/polaris/unesco`. It reads only local UNESCO UIS files under `data/raw/unesco/`, profiles DEM, SDG, SCN-SDG, and SDG11 schemas, integrates reviewed SDG education indicators into immutable `UNESCOEducationRecord` and `UNESCOEducationPanel` artifacts, and writes a Phase 3-compatible education country-year CSV plus manifest, quality summary, integrated-variable catalog, deferred-indicator registry, and optional provenance. The default panel does not average sex categories, combine age cohorts, aggregate education levels, interpolate, impute, or create a custom education index. UNESCO examples are available in `examples/unesco`.

The Phase 18 reasoning package lives under `src/polaris/reasoning`. It interprets existing Phase 5 evidence, Phase 6 agent assessments, Phase 7 coordination, and optional Phase 14 literature context without rereading raw data or modifying evidence. It separates empirical interpretation from plausible mechanisms, alternative explanations, candidate confounders, contradictions, limitations, follow-up hypotheses, and follow-up research questions. Deterministic reasoning works offline; provider-backed reasoning uses structured output validation and the same grounding, causal, policy, medical, and citation guardrails. Reasoning is optional in Phase 13 and can be summarized by Phase 8 and rendered by Phase 9.

The Phase 19 evaluation package lives under `src/polaris/evaluation`. It evaluates Phase 18 reasoning artifacts for grounding, evidence fidelity, causal restraint, epistemic calibration, contradiction handling, limitation propagation, literature separation, structural validity, and reproducibility. It compares deterministic reasoning, optional provider-backed reasoning, and deliberately flawed fixtures by dimension instead of producing an opaque overall quality score. Benchmark examples are available in `examples/evaluation`.

The Phase 20 MCP package lives under `src/polaris/mcp`. It exposes selected Polaris capabilities to compatible local Model Context Protocol clients through a thin adapter layer over existing public APIs. Read-only resources cover dataset discovery, dataset manifests, variable catalogs for WDI/WHO/WGI/UNESCO, derived reports, projects, reasoning artifacts, evaluations, and provenance. Tools cover explicit dataset listing/inspection, statistical analysis, dataset harmonization, complete research-project execution, local literature retrieval, reasoning, reasoning evaluation, and report retrieval. MCP does not select datasets, variables, models, agents, mappings, or causal assumptions. Stdio is the default transport via `python -m polaris.mcp`; install the optional `mcp` extra to run the official MCP SDK server. Example configuration and request shapes are in `examples/mcp`.

JSON schema examples are available in `examples/schemas`. Provider acquisition examples are available in `examples/providers`. Harmonization examples are available in `examples/harmonization`. WHO panel examples are available in `examples/who`. WGI governance examples are available in `examples/wgi`. UNESCO education examples are available in `examples/unesco`. Reasoning examples are available in `examples/reasoning`. Evaluation benchmarks are available in `examples/evaluation`. MCP examples are available in `examples/mcp`. Project orchestration examples are available in `examples/projects`. Illustrative analysis specifications are available in `examples/analysis`, illustrative evidence artifacts are available in `examples/evidence`, illustrative domain assessments are available in `examples/agents`, an illustrative coordinated assessment is available in `examples/coordination`, an illustrative synthesis artifact is available in `examples/synthesis`, and illustrative reports are available in `examples/reporting`. The illustrative metadata catalog is available in `catalog/datasets`. Small synthetic CSV examples are available in `data/examples`. Tests are available in `tests/schemas`, `tests/registry`, `tests/ingestion`, `tests/providers`, `tests/analysis`, `tests/evidence`, `tests/agents`, `tests/coordination`, `tests/synthesis`, `tests/reporting`, `tests/harmonization`, `tests/projects`, `tests/who`, `tests/wgi`, `tests/unesco`, `tests/reasoning`, `tests/evaluation`, and `tests/mcp`.

## MCP Usage

Start a local MCP server with:

```bash
python -m polaris.mcp
```

The command uses stdio and requires the optional official MCP Python SDK dependency. Polaris normal imports, tests, and non-MCP workflows do not launch MCP. MCP clients can inspect `polaris://datasets`, `polaris://datasets/<dataset_id>/manifest`, `polaris://datasets/<dataset_id>/variables`, provider variable catalogs, derived project/report/reasoning/evaluation resources, and `polaris://provenance/<artifact_id>`. Execution tools require explicit typed inputs; they reject malformed requests and do not infer methodology from natural language.

The default safety boundary exposes catalog manifests, committed derived examples, configured project outputs, and configured local literature corpus roots. It does not expose raw provider files, arbitrary paths, shell execution, environment variables, secrets, web browsing, autonomous research planning, causal inference, or automatic recommendations.

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
- [Provider Selection Strategy](docs/data/provider-selection.md)
- [Planned Dataset Catalog](docs/data/dataset-catalog.md)
- [Variable Priority](docs/data/variable-priority.md)
- [Real-Data Integration Plan](docs/data/integration-plan.md)
- [Architecture Decision Records](docs/decisions/001-project-principles.md), including [ADR-014](docs/decisions/014-real-dataset-validation.md) and [ADR-015](docs/decisions/015-cross-dataset-country-year-harmonization.md)

## Roadmap Summary

Phase 0 completed the documentation baseline. Phase 1 added the minimal schema foundation. Phase 2 added deterministic local dataset-manifest loading, registration, coverage matching, warning surfacing, and structured metadata search. Phase 3 added deterministic local CSV ingestion and validation. Phase 4 added deterministic statistical analysis and diagnostics for explicit specifications. Phase 5 added structured evidence records and bounded non-causal claim candidates extracted from Phase 4 results. Phase 6 added deterministic domain agents. Phase 7 added deterministic multi-agent coordination. Phase 8 added guardrailed interdisciplinary synthesis. Phase 9 added deterministic structured research report generation. Phase 10 added real-provider acquisition infrastructure. Phase 11 validated official WDI data through Phases 3-9. Phase 12 added deterministic cross-dataset country-year harmonization and validated a WDI plus WHO life-expectancy example. Phase 13 added deterministic in-process research-project orchestration over the existing phases. Phase 14 added optional local literature context. Phase 15 added the curated WHO health panel. Phase 16 added the official World Bank WGI governance panel. Phase 17 added the curated UNESCO UIS education panel. Phase 18 added optional evidence-grounded reasoning over structured artifacts. Phase 19 added deterministic reasoning evaluation and benchmarking. Phase 20 added an optional local MCP research interface. Later phases will add broader artifact storage, frontend workflows, deployment, observability, and broader LLM enhancement where justified.

## Current Status and Next Phase

Current decision records establish Polaris as a research system with mandatory multi-agent orchestration, a deterministic analytical core, Pydantic-based schema contracts, an in-memory deterministic dataset registry, local CSV ingestion, deterministic statistical execution, structured evidence extraction, deterministic domain-agent assessment, deterministic coordination of structured domain outputs, guardrailed synthesis from coordinated evidence, structured reporting, immutable provider dataset acquisition, real WDI validation, cross-provider country-year harmonization, and a synchronous project orchestrator. The next major research task is to broaden reviewed provider-variable mappings while preserving explicit dataset selection, explicit variable mappings, explicit statistical specifications, explicit agent selection, deterministic project IDs, and traceable project provenance.

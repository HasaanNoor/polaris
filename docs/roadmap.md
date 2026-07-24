# Roadmap

This roadmap defines incremental phases. Candidate technologies are not implementation commitments until a phase records a decision.

## Phase 0: Documentation and Design Specification

Objective: establish mission, architecture, methodology policies, dataset criteria, and decision records.

Deliverables: README, contribution guide, vision, roadmap, research-question framework, architecture documents, methodology policies, dataset documents, and ADRs.

Verification: all required Markdown files are populated, internally linked, and free of unsupported methodology claims.

Non-goals: application code, dependencies, CI, Docker, frontend, backend, and approved dataset integrations.

## Phase 1: Core Schemas (complete)

Objective: convert Phase 0 concepts into minimal typed schemas.

Deliverables: research question, dataset manifest, agent message, provenance record, statistical specification, and research artifact schemas.

Verification: schema validation tests and examples. Implemented in `src/polaris/schemas`, `tests/schemas`, and `examples/schemas`.

## Phase 2: Dataset Registry and Metadata Search (complete)

Objective: implement a deterministic, in-memory registry for validated dataset manifests.

Deliverables: local JSON manifest loader, duplicate-safe registry, structured metadata search query, explainable search results, temporal and geographic coverage matching, warning and access-restriction surfacing, domain errors, illustrative catalog, tests, and ADR.

Verification: registry, loader, search, coverage, catalog, and Phase 1 schema tests pass with Ruff checks.

## Phase 3: Tabular Dataset Ingestion and Validation (complete)

Objective: implement deterministic local ingestion and validation for tabular source files associated with registered manifests.

Deliverables: typed ingestion configuration and request models, local CSV loader, manifest-to-column validation, value normalization, structural validation report, deterministic data-quality profile, immutable ingestion result, domain-specific errors, synthetic example CSV files, tests, documentation, and ADR-006.

Verification: schema, registry, and ingestion tests pass with Ruff lint, Ruff format check, and Git whitespace checks.

## Phase 4: Deterministic Statistical Analysis and Diagnostics (complete)

Objective: execute explicit statistical specifications against successful Phase 3 ingestion results.

Deliverables: typed analysis request and immutable result models, compatibility validation, complete-case sample construction, descriptive statistics, Pearson and Spearman correlations, OLS regression, diagnostics, typed analytical findings, provenance, deterministic result identifiers, examples, tests, documentation, and ADR-007.

Verification: analysis tests, schema/registry/ingestion regression tests, Ruff linting, Ruff format checks, and Git whitespace checks.

## Phase 5: Structured Evidence and Deterministic Claim Extraction (complete)

Objective: convert Phase 4 statistical results into structured machine-readable evidence records and bounded analytical claim candidates.

Deliverables: immutable evidence models, evidence taxonomy, extraction from descriptive statistics, correlations, OLS coefficients, model fit, diagnostics, sample quality, warning evidence, deterministic claim generation, limitation propagation, evidence and claim provenance, deterministic IDs, examples, tests, documentation, and ADR-008.

Verification: evidence tests, schema/registry/ingestion/analysis regression tests, Ruff linting, Ruff format checks, and Git whitespace checks.

## Phase 6: Dataset Metadata Review

Objective: review and harden candidate dataset metadata without ingesting observations.

Deliverables: source-review fields, licensing decisions, revision metadata checks, and warnings.

Verification: registry validation and candidate-source examples.

## Phase 7: Provenance and Artifact Store

Objective: persist versioned research artifacts and provenance records.

Deliverables: storage abstraction, artifact versioning, hash strategy, and retrieval tests.

Verification: artifact round-trip tests and immutable-version checks.

## Phase 8: Dataset Retrieval Prototype

Objective: retrieve a small reviewed public dataset through deterministic connectors.

Deliverables: connector interface, retrieval logs, source metadata capture, and access-failure handling.

Verification: reproducible retrieval test using pinned source metadata.

## Phase 9: Data Quality Service

Objective: assess missingness, coverage, comparability, revisions, and source warnings.

Deliverables: quality rules, dataset-quality report, and warning taxonomy.

Verification: tests using datasets with known quality issues.

## Phase 10: Transformation Pipeline

Objective: support traceable cleaning and derived-variable creation.

Deliverables: transformation records, observed-versus-derived separation, imputation flags, and audit logs.

Verification: lineage tests from raw values to transformed outputs.

## Phase 11: Descriptive Analytics

Objective: compute deterministic descriptive statistics and uncertainty summaries where applicable.

Deliverables: summary statistics, group comparisons, trend summaries, and reporting tables.

Verification: numerical tests against fixed fixtures.

## Phase 12: Statistical Modeling Service

Objective: add deterministic statistical model execution.

Deliverables: model specifications, diagnostics, effect estimates, uncertainty outputs, and multiple-comparison metadata.

Verification: tests against known analytical results.

## Phase 13: Initial Deterministic Agents

Objective: implement typed agents for coordination, question interpretation, dataset selection, data quality, and statistical analysis.

Deliverables: agent contracts, deterministic strategies, validation failures, and contribution records.

Verification: contract tests and end-to-end artifact generation.

## Phase 14: Orchestration Runtime

Objective: coordinate agents through explicit state transitions and failure handling.

Deliverables: orchestration graph, retry policy, stop conditions, and partial-result handling.

Verification: workflow tests for success, insufficient evidence, and conflicting-source outcomes.

## Phase 15: Evidence Critic and Synthesis

Objective: critique analytical outputs and generate cautious reports from artifacts.

Deliverables: evidence-quality assessment, limitation extraction, conflict representation, and report templates.

Verification: tests preventing unsupported causal or quantitative claims.

## Phase 16: Causal Identification Assessment

Objective: assess whether a question and dataset support explicit causal interpretation.

Deliverables: identification taxonomy, design checks, assumption records, and unsupported-causal-language diagnostics.

Verification: fixture tests for descriptive, regression-adjusted, quasi-experimental, and experimental cases.

## Phase 17: Robustness and Sensitivity

Objective: evaluate stability of findings under reasonable alternative specifications.

Deliverables: robustness-test registry, sensitivity outputs, and reporting rules.

Verification: reproducible robustness results on fixed fixtures.

## Phase 18: Domain Agent Expansion

Objective: introduce deterministic domain agents incrementally.

Deliverables: governance, economics, education, public health, society, demographics, environment, innovation, conflict, and historical-context agent stubs as needed.

Verification: typed outputs and domain-specific warning tests.

Non-goal: implementing every target agent at once.

## Phase 19: Human-Readable Report Renderer

Objective: generate readable reports from research artifacts.

Deliverables: report templates, citations, tables, figures, limitations, and reproducibility appendix.

Verification: snapshot tests and manual report review.

## Phase 20: Frontend Research Workspace

Objective: provide a usable interface for submitting questions and reviewing artifacts.

Deliverables: question form, investigation status, dataset views, evidence panels, diagnostics, and report view.

Verification: browser tests for primary workflows.

## Phase 21: Evidence-Grounded LLM Evaluation

Objective: evaluate whether selected agents benefit from LLM strategies.

Deliverables: candidate tasks, grounding constraints, evaluation set, refusal behavior, and comparison to deterministic baselines.

Verification: LLM outputs cannot alter deterministic analytical results or add unsupported claims.

## Phase 22: Controlled LLM Enhancement

Objective: add evidence-grounded LLM strategies only where Phase 19 justifies them.

Deliverables: strategy adapters, prompt/version records, grounding checks, and fallback behavior.

Verification: regression tests for unsupported evidence, uncertainty concealment, and contract stability.

## Phase 23: Deployment Baseline

Objective: package a minimal deployable system after core workflows exist.

Deliverables: deployment decision record, runtime configuration, persistence configuration, and operational documentation.

Verification: reproducible deployment in the selected environment.

## Phase 24: Observability and Governance

Objective: monitor investigations, failures, provenance, and methodological policy enforcement.

Deliverables: structured logs, metrics, audit views, and review queues.

Verification: traceability tests from report claims to artifacts and logs.

## Phase 25: Public Demo and Documentation Hardening

Objective: publish a constrained public demonstration using reviewed datasets and documented limitations.

Deliverables: demo investigation set, public documentation, limitation notices, and reproducibility packages.

Verification: public workflows reproduce expected artifacts and reports.

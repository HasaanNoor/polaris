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

## Phase 2: Repository Tooling

Objective: add minimal development tooling required to validate schemas and documentation.

Deliverables: formatter, linter, test runner, and local validation commands.

Verification: clean validation run from a fresh checkout.

## Phase 3: Deterministic Research Question Parser

Objective: classify supported research questions without LLMs.

Deliverables: parser rules, classification labels, required metadata checks, and invalid-question diagnostics.

Verification: unit tests for well-formed and poorly formed questions.

## Phase 4: Dataset Metadata Registry

Objective: represent candidate datasets without ingesting data.

Deliverables: registry schema, source-review fields, licensing fields, revision metadata, and warnings.

Verification: registry validation and candidate-source examples.

## Phase 5: Provenance and Artifact Store

Objective: persist versioned research artifacts and provenance records.

Deliverables: storage abstraction, artifact versioning, hash strategy, and retrieval tests.

Verification: artifact round-trip tests and immutable-version checks.

## Phase 6: Dataset Retrieval Prototype

Objective: retrieve a small reviewed public dataset through deterministic connectors.

Deliverables: connector interface, retrieval logs, source metadata capture, and access-failure handling.

Verification: reproducible retrieval test using pinned source metadata.

## Phase 7: Data Quality Service

Objective: assess missingness, coverage, comparability, revisions, and source warnings.

Deliverables: quality rules, dataset-quality report, and warning taxonomy.

Verification: tests using datasets with known quality issues.

## Phase 8: Transformation Pipeline

Objective: support traceable cleaning and derived-variable creation.

Deliverables: transformation records, observed-versus-derived separation, imputation flags, and audit logs.

Verification: lineage tests from raw values to transformed outputs.

## Phase 9: Descriptive Analytics

Objective: compute deterministic descriptive statistics and uncertainty summaries where applicable.

Deliverables: summary statistics, group comparisons, trend summaries, and reporting tables.

Verification: numerical tests against fixed fixtures.

## Phase 10: Statistical Modeling Service

Objective: add deterministic statistical model execution.

Deliverables: model specifications, diagnostics, effect estimates, uncertainty outputs, and multiple-comparison metadata.

Verification: tests against known analytical results.

## Phase 11: Initial Deterministic Agents

Objective: implement typed agents for coordination, question interpretation, dataset selection, data quality, and statistical analysis.

Deliverables: agent contracts, deterministic strategies, validation failures, and contribution records.

Verification: contract tests and end-to-end artifact generation.

## Phase 12: Orchestration Runtime

Objective: coordinate agents through explicit state transitions and failure handling.

Deliverables: orchestration graph, retry policy, stop conditions, and partial-result handling.

Verification: workflow tests for success, insufficient evidence, and conflicting-source outcomes.

## Phase 13: Evidence Critic and Synthesis

Objective: critique analytical outputs and generate cautious reports from artifacts.

Deliverables: evidence-quality assessment, limitation extraction, conflict representation, and report templates.

Verification: tests preventing unsupported causal or quantitative claims.

## Phase 14: Causal Identification Assessment

Objective: assess whether a question and dataset support explicit causal interpretation.

Deliverables: identification taxonomy, design checks, assumption records, and unsupported-causal-language diagnostics.

Verification: fixture tests for descriptive, regression-adjusted, quasi-experimental, and experimental cases.

## Phase 15: Robustness and Sensitivity

Objective: evaluate stability of findings under reasonable alternative specifications.

Deliverables: robustness-test registry, sensitivity outputs, and reporting rules.

Verification: reproducible robustness results on fixed fixtures.

## Phase 16: Domain Agent Expansion

Objective: introduce deterministic domain agents incrementally.

Deliverables: governance, economics, education, public health, society, demographics, environment, innovation, conflict, and historical-context agent stubs as needed.

Verification: typed outputs and domain-specific warning tests.

Non-goal: implementing every target agent at once.

## Phase 17: Human-Readable Report Renderer

Objective: generate readable reports from research artifacts.

Deliverables: report templates, citations, tables, figures, limitations, and reproducibility appendix.

Verification: snapshot tests and manual report review.

## Phase 18: Frontend Research Workspace

Objective: provide a usable interface for submitting questions and reviewing artifacts.

Deliverables: question form, investigation status, dataset views, evidence panels, diagnostics, and report view.

Verification: browser tests for primary workflows.

## Phase 19: Evidence-Grounded LLM Evaluation

Objective: evaluate whether selected agents benefit from LLM strategies.

Deliverables: candidate tasks, grounding constraints, evaluation set, refusal behavior, and comparison to deterministic baselines.

Verification: LLM outputs cannot alter deterministic analytical results or add unsupported claims.

## Phase 20: Controlled LLM Enhancement

Objective: add evidence-grounded LLM strategies only where Phase 19 justifies them.

Deliverables: strategy adapters, prompt/version records, grounding checks, and fallback behavior.

Verification: regression tests for unsupported evidence, uncertainty concealment, and contract stability.

## Phase 21: Deployment Baseline

Objective: package a minimal deployable system after core workflows exist.

Deliverables: deployment decision record, runtime configuration, persistence configuration, and operational documentation.

Verification: reproducible deployment in the selected environment.

## Phase 22: Observability and Governance

Objective: monitor investigations, failures, provenance, and methodological policy enforcement.

Deliverables: structured logs, metrics, audit views, and review queues.

Verification: traceability tests from report claims to artifacts and logs.

## Phase 23: Public Demo and Documentation Hardening

Objective: publish a constrained public demonstration using reviewed datasets and documented limitations.

Deliverables: demo investigation set, public documentation, limitation notices, and reproducibility packages.

Verification: public workflows reproduce expected artifacts and reports.

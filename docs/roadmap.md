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

## Phase 6: Deterministic Domain Agents (complete)

Objective: implement the first deterministic domain-agent layer over Phase 5 evidence artifacts.

Deliverables: typed domain taxonomy, immutable `AgentAssessment` models, deterministic relevance records, governance/economics/education/public-health agents, rule-based variable concept mapping, domain concern codes, unsupported-inference tracking, limitation propagation, deterministic assessment IDs, public execution API, examples, tests, and ADR-009.

Verification: agent tests, integration tests across Phases 3-6, schema/registry/ingestion/analysis/evidence regression tests, Ruff linting, Ruff format checks, and Git whitespace checks.

Non-goals: LLMs, retrieval, outside context, databases, policy recommendations, causal inference, coordinator synthesis, and final research-report generation.

## Phase 7: Deterministic Multi-Agent Coordination (complete)

Objective: coordinate deterministic Phase 6 domain assessments into one structured interdisciplinary state object.

Deliverables: frozen coordination request/result models, `CoordinatedAssessment`, assessment-set validation, domain coverage aggregation, evidence-domain mapping, claim-domain mapping, conservative agreement and divergence records, shared limitation aggregation, unsupported-inference aggregation, evidence and domain gaps, deterministic IDs, provenance, public API, examples, tests, documentation, and ADR-010.

Verification: coordination tests, integration tests across Phases 3-7, schema/registry/ingestion/analysis/evidence/agent regression tests, Ruff linting, Ruff format checks, and Git whitespace checks.

Non-goals: LLMs, retrieval, outside context, databases, embeddings, causal inference, policy recommendations, natural-language synthesis, statistical recalculation, probabilistic debate, and final report generation.

## Phase 8: Guardrailed LLM-Assisted Interdisciplinary Synthesis (complete)

Objective: produce structured interdisciplinary natural-language synthesis from a deterministic Phase 7 coordinated assessment without inventing evidence or violating upstream limitations.

Deliverables: frozen synthesis request/result models, `SynthesisArtifact`, deterministic fallback synthesis, prompt-grounding payload construction, strict prompt rules, small provider protocol, structured provider response validation, fabricated-reference checks, causal-language safeguards, policy/medical recommendation safeguards, limitation and unsupported-inference preservation, uncertainty codes, synthesis provenance, public API, illustrative example, tests, documentation, and ADR-011.

Verification: synthesis tests, integration tests across Phases 3-8, schema/registry/ingestion/analysis/evidence/agent/coordination regression tests, Ruff linting, Ruff format checks, and Git whitespace checks.

Non-goals: raw data inspection, statistical recalculation, dataset selection, outside retrieval, embeddings, databases, multi-provider framework, policy recommendations, medical recommendations, causal or mechanism claims, final report generation, frontend work, and application infrastructure.

## Phase 9: Structured Research Report Generation (complete)

Objective: convert validated Polaris artifacts into structured, reviewable, exportable research reports.

Deliverables: frozen report request/result models, lineage compatibility validation, deterministic section assembly, research-question, dataset, methodology, statistical-results, evidence, claim, domain-assessment, cross-domain, synthesis, limitations, gaps, unsupported-inferences, provenance, and reference-index sections, deterministic report IDs, JSON serialization, Markdown rendering, standalone HTML rendering, illustrative examples, tests, documentation, and ADR-012.

Verification: reporting tests, integration tests across Phases 3-9, schema/registry/ingestion/analysis/evidence/agent/coordination/synthesis regression tests, Ruff linting, Ruff format checks, and Git whitespace checks.

Non-goals: new statistical analysis, evidence creation, claim creation, agent reruns during reporting, LLM calls, external retrieval, external bibliography generation, causal interpretation, policy recommendations, medical recommendations, PDF, DOCX, LaTeX, frontend work, and application infrastructure.

## Phase 10: Real Dataset Acquisition and Provider Integration (complete)

Objective: transition from illustrative-only datasets to explicit acquisition of real-world public provider datasets while preserving deterministic offline research.

Deliverables: provider interface, built-in World Bank WDI, WHO GHO, and UNESCO UIS adapters, typed download and snapshot models, immutable raw snapshot storage, sidecar snapshot metadata, SHA-256 validation, duplicate checksum cache reuse, generated Phase 3-compatible manifests, provider registry, dataset-registry source classification, offline examples, tests, and ADR-013.

Verification: provider tests, registry and ingestion compatibility tests, full regression tests, Ruff linting, Ruff format checks, and Git whitespace checks.

Non-goals: literature retrieval, internet search, LLM reasoning, autonomous agents, streaming APIs, scheduled synchronization, raw-data mutation, and manual preprocessing.

Documentation follow-up: provider selection, planned dataset catalog, variable priorities, and staged integration workflow are documented in [Provider Selection Strategy](data/provider-selection.md), [Planned Dataset Catalog](data/dataset-catalog.md), [Variable Priority](data/variable-priority.md), and [Real-Data Integration Plan](data/integration-plan.md). Phase 10 adapter support currently covers World Bank WDI, WHO GHO, and UNESCO UIS; other selected datasets are planned but do not yet have provider adapters. Dataset selection does not imply that files have been downloaded, validated, or integrated end to end.

## Phase 11: Real Dataset Discovery and End-to-End Validation (complete)

Objective: discover local official provider files, profile schemas, prepare a reviewed WDI extract, and validate that one official real dataset can run through Phases 3-9.

Deliverables: real-data discovery and schema inspection, compatibility checks, WDI extract generation, manifest generation, validation summary, end-to-end runner, examples, tests, and ADR-014.

Verification: official World Bank WDI local data is ingested, analyzed, converted to evidence, assessed by deterministic agents, coordinated, synthesized, and reported through the existing pipeline.

## Phase 12: Cross-Dataset Country-Year Harmonization (complete)

Objective: combine explicitly selected variables from compatible validated provider datasets into a derived country-year analytical dataset without guessing identifiers, hiding missingness, or losing value-level provenance.

Deliverables: harmonization request, dataset, record, variable mapping, country/year normalization, compatibility validation, deterministic joins, duplicate/conflict/missingness handling, value-level provenance, quality summary, Phase 3-compatible export, WDI+WHO real-data example, tests, and ADR-015.

Verification: harmonization tests pass, and the local WDI plus WHO life-expectancy example exports a derived Phase 3-compatible dataset that runs through Phases 3-9.

## Phase 13: Research Project Orchestration (complete)

Objective: coordinate existing Polaris phases into one reproducible, explicit research-project workflow.

Deliverables: `ResearchProjectRequest`, `ResearchExecutionPlan`, `ResearchProjectResult`, explicit dataset-input models, dataset resolution, optional Phase 12 harmonization routing, Phase 4 statistical-specification routing, ordered execution stages, intermediate artifact tracking, failure-stage tracking, deterministic project IDs, project-level provenance aggregation, reproducibility summaries, output-directory writing, examples, tests, and ADR-016.

Verification: project tests cover models, planning, successful single-dataset execution, successful harmonized multi-provider execution, failure preservation, provenance, reproducibility, and optional real-data execution when local WDI and WHO files are present. The orchestrator reuses Phases 3-9 and 12 and does not choose datasets, infer mappings, invent statistical models, or add LLM behavior.

## Phase 14: Literature Context and Retrieval (complete)

Objective: add deterministic, provenance-preserving literature retrieval from a local or explicitly supplied corpus so Polaris can contextualize empirical claims after evidence extraction and coordination.

Deliverables: `LiteratureDocument`, `LiteratureChunk`, `CitationMetadata`, `LiteratureCorpus`, deterministic TXT/Markdown/JSON ingestion, text normalization, paragraph-aware chunking, BM25-style lexical retrieval, `RetrievalRequest`, `RetrievalResult`, claim-to-literature query construction, `LiteratureEvidence`, retrieval quality summaries, `LiteratureContextArtifact`, citation preservation, optional Phase 8 synthesis context, optional Phase 9 report section, optional Phase 13 `RETRIEVE_LITERATURE` stage, examples, tests, documentation, and ADR-017.

Verification: literature tests cover strict frozen models, checksums, deterministic chunk IDs, stable retrieval ranking, filters, unmatched claims, citation preservation, synthesis/report integration, and optional project orchestration. The default path is offline, corpus-grounded, and does not browse the internet, generate citations, add statistical methods, or alter empirical findings.

## Phase 15: Curated WHO Health Panel Integration (complete)

Objective: convert the locally acquired WHO GHO collection into a deterministic reviewed country-year health panel.

Deliverables: WHO acquisition-catalog loading, indicator schema profiling, reviewed variable mappings, dimension-selection rules, country/year filtering, aggregate exclusion, sex/age/status/projection handling, unit validation, value-level provenance, immutable `WHOHealthRecord` and `WHOHealthPanel` models, quality summary, deferred-indicator registry, Phase 3-compatible export, generic Phase 12 compatibility, WDI plus WHO project example, tests, documentation, and ADR-018.

Verification: `tests/who` covers catalog loading, profiling, mappings, dimensions, country handling, panel determinism, export, Phase 3 ingestion, Phase 12 harmonization, and Phase 13 project execution. The current local WHO panel integrates 28 reviewed indicators and defers 14 catalog targets.

## Phase 16: Governance Indicator Panel Integration (complete)

Objective: add a deterministic, analysis-ready governance panel from official World Bank Worldwide Governance Indicators.

Deliverables: official WGI API ZIP acquisition, source validation, schema profiling, six reviewed canonical governance variables, exact country/year normalization, central-estimate selection, uncertainty metadata preservation, aggregate and territory exclusions, immutable `WGIGovernanceRecord` and `WGIGovernancePanel` models, value-level provenance, quality summary, deterministic panel identity, Phase 3 export, generic Phase 12 WDI+WGI and WDI+WHO+WGI examples, Phase 13 associational project example, tests, documentation, and ADR-019.

Verification: `tests/wgi` covers acquisition URL shape, mappings, profiling, panel determinism, uncertainty preservation, Phase 3 ingestion, Phase 12 compatibility, and Phase 13 Governance/Economics/Public Health project execution. Local examples under `examples/wgi` use official WGI snapshots when present.

## Phase 17: UNESCO Education Panel Integration (complete)

Objective: convert locally downloaded UNESCO UIS data into a deterministic reviewed education country-year panel.

Deliverables: local UNESCO DEM/SDG/SCN-SDG/SDG11 profiling, reviewed SDG education mappings, dimension parsing, aggregate/territory exclusion, value-level provenance, immutable `UNESCOEducationRecord` and `UNESCOEducationPanel` models, quality summary, deferred-indicator registry, deterministic panel identity, Phase 3 export, generic Phase 12 WDI+UNESCO and WDI+WHO+WGI+UNESCO examples, Phase 13 associational project example, tests, documentation, and ADR-020.

Verification: `tests/unesco` covers catalog loading, profiling, mappings, dimensions, panel determinism, provenance preservation, Phase 3 ingestion, and Phase 12 WDI+UNESCO compatibility. Local examples under `examples/unesco` use existing downloaded UNESCO files only.

## Phase 18: Evidence-Grounded Reasoning Engine (complete)

Objective: add a structured reasoning layer that interprets existing empirical evidence, coordinated domain assessments, and optional literature context without modifying underlying evidence.

Deliverables: `ReasoningRequest`, `ReasoningStatement`, `ReasoningArtifact`, explicit reasoning taxonomy, epistemic status and support-level categories, mandatory grounding IDs, deterministic fallback reasoning, optional provider-backed structured reasoning, prompt/version provenance, grounding validation, causal-language guardrails, alternative explanations, candidate confounders, plausible mechanisms labeled unproven, contradiction records, limitation reasoning, follow-up hypotheses/questions, Phase 8/9/13 integration, examples, tests, documentation, and ADR-021.

Verification: `tests/reasoning` covers strict/frozen models, deterministic IDs, grounding rejection, causal guardrails, mechanisms, alternatives/confounders, contradictions, provider-backed fake-provider behavior, deterministic fallback, synthesis/report/project integration, and network-free operation.

## Phase 19: Reasoning Evaluation and Benchmarking (complete)

Objective: evaluate whether Phase 18 reasoning outputs are grounded, faithful to evidence, appropriately uncertain, causally restrained, internally consistent, contradiction-aware, reproducible, and structurally valid.

Deliverables: `BenchmarkCase`, `ExpectedReasoningBehavior`, `BenchmarkSuite`, `ReasoningEvaluationResult`, `BenchmarkSuiteResult`, deterministic evaluation dimensions, deterministic/provider comparison summaries, adversarial fixtures, regression benchmark support, JSON/Markdown benchmark reports, examples, tests, documentation, and ADR-022.

Verification: `tests/evaluation` covers deterministic benchmark reproducibility, adversarial fabricated grounding and citation detection, causal overclaims, evidence direction mismatch, contradiction omission, material limitation loss, literature separation, fake-provider comparison, and benchmark report rendering. Default tests are network-free and require no provider secrets.

## Phase 20: Additional Deterministic Agents

Objective: implement typed agents for coordination, question interpretation, dataset selection, data quality, and statistical analysis.

Deliverables: agent contracts, deterministic strategies, validation failures, and contribution records.

Verification: contract tests and end-to-end artifact generation.

## Phase 21: Persistent Orchestration Runtime

Objective: add persistence only if project orchestration later requires durable state beyond the Phase 13 in-process service.

Deliverables: orchestration graph, retry policy, stop conditions, and partial-result handling.

Verification: workflow tests for success, insufficient evidence, and conflicting-source outcomes.

## Phase 22: Evidence Critic and Retrieval-Grounded Synthesis

Objective: critique analytical outputs and generate cautious reports from artifacts.

Deliverables: evidence-quality assessment, limitation extraction, conflict representation, and report templates.

Verification: tests preventing unsupported causal or quantitative claims.

## Phase 23: Causal Identification Assessment

Objective: assess whether a question and dataset support explicit causal interpretation.

Deliverables: identification taxonomy, design checks, assumption records, and unsupported-causal-language diagnostics.

Verification: fixture tests for descriptive, regression-adjusted, quasi-experimental, and experimental cases.

## Phase 24: Robustness and Sensitivity

Objective: evaluate stability of findings under reasonable alternative specifications.

Deliverables: robustness-test registry, sensitivity outputs, and reporting rules.

Verification: reproducible robustness results on fixed fixtures.

## Phase 25: Domain Agent Expansion

Objective: introduce deterministic domain agents incrementally.

Deliverables: governance, economics, education, public health, society, demographics, environment, innovation, conflict, and historical-context agent stubs as needed.

Verification: typed outputs and domain-specific warning tests.

Non-goal: implementing every target agent at once.

## Phase 26: Human-Readable Report Renderer

Objective: generate readable reports from research artifacts.

Deliverables: report templates, citations, tables, figures, limitations, and reproducibility appendix.

Verification: snapshot tests and manual report review.

## Phase 27: Frontend Research Workspace

Objective: provide a usable interface for submitting questions and reviewing artifacts.

Deliverables: question form, investigation status, dataset views, evidence panels, diagnostics, and report view.

Verification: browser tests for primary workflows.

## Phase 28: Evidence-Grounded LLM Evaluation

Objective: evaluate whether selected agents benefit from LLM strategies.

Deliverables: candidate tasks, grounding constraints, evaluation set, refusal behavior, and comparison to deterministic baselines.

Verification: LLM outputs cannot alter deterministic analytical results or add unsupported claims.

## Phase 29: Controlled LLM Enhancement

Objective: add evidence-grounded LLM strategies only where Phase 25 justifies them.

Deliverables: strategy adapters, prompt/version records, grounding checks, and fallback behavior.

Verification: regression tests for unsupported evidence, uncertainty concealment, and contract stability.

## Phase 30: Deployment Baseline

Objective: package a minimal deployable system after core workflows exist.

Deliverables: deployment decision record, runtime configuration, persistence configuration, and operational documentation.

Verification: reproducible deployment in the selected environment.

## Phase 31: Observability and Governance

Objective: monitor investigations, failures, provenance, and methodological policy enforcement.

Deliverables: structured logs, metrics, audit views, and review queues.

Verification: traceability tests from report claims to artifacts and logs.

## Phase 32: Public Demo and Documentation Hardening

Objective: publish a constrained public demonstration using reviewed datasets and documented limitations.

Deliverables: demo investigation set, public documentation, limitation notices, and reproducibility packages.

Verification: public workflows reproduce expected artifacts and reports.

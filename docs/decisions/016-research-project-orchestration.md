# ADR-016: Research Project Orchestration

## Status

Accepted.

## Context

Phases 3 through 12 provide deterministic, typed services for ingestion, analysis, evidence extraction, domain-agent assessment, coordination, synthesis, reporting, provider validation, and cross-provider country-year harmonization. Running a complete research workflow still required manual wiring of each phase and ad hoc tracking of intermediate artifacts.

Polaris needs a single reproducible project workflow while preserving the methodological boundary that orchestration coordinates existing services and does not perform analysis itself.

## Decision

Add a focused `polaris.projects` package with frozen request/result models, deterministic planning, project provenance aggregation, and a synchronous `run_research_project(...)` service.

The orchestrator reuses the existing Phase 3 ingestion service, Phase 12 harmonization service and export bridge, Phase 4 analysis service, Phase 5 evidence service, Phase 6 domain-agent service, Phase 7 coordinator, Phase 8 synthesis service, and Phase 9 reporting service. It does not duplicate statistical, ingestion, harmonization, evidence, synthesis, agent, or reporting logic.

Execution stages are explicit: dataset resolution, ingestion, optional harmonization, analysis, evidence extraction, selected agent execution, coordination, synthesis, reporting, and completion. If a fatal stage fails, downstream stages are skipped and completed upstream artifacts remain available in the returned result. Project IDs are deterministic and exclude timestamps. Dataset selection, harmonization mappings, statistical specifications, selected agents, synthesis mode, and report format remain explicit inputs.

Project-level provenance aggregates upstream identifiers and source checksums so a final report can be traced back to source datasets, while preserving phase-specific provenance records as the authoritative details for each step.

## Consequences

Callers can define a `ResearchProjectRequest` once and execute a complete in-process workflow with `run_research_project(...)`. Plans can be inspected before execution with `plan_research_project(...)`. Failed projects identify the exact failed stage and preserve the original error type and message.

The initial orchestrator remains synchronous and lightweight. It writes predictable project outputs when an output directory is supplied, but it does not introduce a workflow database, external scheduler, background jobs, or distributed execution.

The orchestrator does not infer datasets, mappings, statistical models, agents, or research questions. Autonomous research planning is deferred because Polaris currently prioritizes explicit reproducibility and reviewable methodological choices over self-directed automation.

## Alternatives Considered

Embedding orchestration into earlier phase services was rejected because it would blur ownership and make analysis services responsible for workflow policy.

Generating statistical specifications from research questions was rejected because Phase 4 requires explicit validated specifications and Polaris must not silently choose a model.

Automatically selecting datasets or invoking every agent was rejected because dataset choice and domain participation are methodological decisions that must remain visible.

Replacing upstream provenance with a project provenance record was rejected because each phase already records more precise lineage for its own outputs.

Using Airflow, Prefect, Dagster, Temporal, Celery, or a database-backed workflow engine was rejected for the initial implementation because the current need is a deterministic local service boundary, not durable distributed execution.

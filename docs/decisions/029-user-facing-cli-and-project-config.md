# ADR-029: User-Facing CLI and Project Configuration

## Status

Accepted.

## Context

Polaris has mature typed contracts and deterministic services, but the primary interface has been
Python modules, examples, tests, and MCP adapters. Researchers need a stable local command that can
inspect datasets, validate a complete research configuration, run Phase 13 orchestration, inspect
outputs, and reproduce completed runs without importing Python APIs directly.

## Decision

Add a `polaris` command-line interface under `src/polaris/cli`. The CLI is the first user-facing
workflow because it is scriptable, local, auditable, and compatible with existing artifact files. A
web UI is deferred until the workflow contract stabilizes.

Phase 13 remains the research orchestrator. CLI commands parse user input, validate it, translate
YAML/JSON into existing Pydantic contracts, and call existing public APIs such as
`plan_research_project(...)`, `run_research_project(...)`, registry inspection, causal-study
readiness, reporting, and visualization services. CLI commands must not contain independent
research methodology.

Project configuration uses strict typed YAML or JSON. YAML improves readability for researchers;
JSON supports automation. YAML is loaded with `yaml.safe_load` only. Configuration is data, not
executable code, and cannot load arbitrary Python modules.

Research choices remain explicit. The CLI does not select datasets, variables, statistical models,
causal designs, controls, treatment dates, robustness variants, agents, or AI behavior. Provider
backed reasoning must be explicitly requested and fails clearly when no provider is configured.

Deterministic project identity remains important. Project IDs come from Phase 13 planning and
exclude timestamps. Every CLI run stores the normalized validated configuration and a
`reproducibility-manifest.json` alongside existing Phase 13 outputs so the run can be inspected and
reproduced without silently substituting newer data.

Raw tracebacks are hidden by default. User-facing errors include a stage, concise reason, and
deterministic suggestion where available. Developer details are available with `--debug` on project
execution.

## Consequences

The installed command is exposed through:

```toml
[project.scripts]
polaris = "polaris.cli.app:main"
```

`python -m polaris` delegates to the same app.

The optional `cli` extra adds Typer and PyYAML. Typer is lightweight, mature, and already aligned
with command-group workflows. PyYAML is limited to safe loading and is needed for the documented
researcher-facing YAML experience.

Default project outputs use:

```text
outputs/projects/<project_id>/
  project.json
  execution-plan.json
  reproducibility-summary.json
  normalized-config.json
  reproducibility-manifest.json
  report/
  visualizations/
```

Safe stage-level resume is deferred beyond compatibility checks because robust resume would require
artifact matching for each deterministic stage. Web dashboards, desktop apps, notebook UI,
interactive chart editing, conversational autonomous research, cloud execution, distributed job
queues, multi-user management, hosted storage, automatic research-question generation, automatic
model selection, and automatic causal-design selection remain deferred.

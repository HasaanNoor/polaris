# ADR 004: Python Schema Foundation

## Status

Accepted for Phase 1.

## Context

Phase 1 converts the Phase 0 architecture, methodology, provenance, and artifact concepts into executable schema contracts. These contracts need typed validation, JSON serialization, strict handling of unknown fields, compact examples, and tests. They must not introduce application services, persistence, orchestration, analytical execution, report rendering, or LLM integration.

## Decision

Polaris will use Python 3.12 or a compatible modern Python version with Pydantic v2 for the Phase 1 schema foundation. The package uses a `src/polaris/schemas` layout, keeps shared controlled vocabularies in common schema primitives, and defines separate modules for research questions, dataset manifests, agent messages, provenance records, statistical specifications, and research artifacts.

Pytest is used for schema-validation tests. Ruff is configured only for local linting and formatting checks because Phase 2 owns broader repository-tooling work.

## Consequences

The schema contracts are executable, typed, and testable while remaining independent of future API, storage, orchestration, analytics, and report-rendering choices. Pydantic v2 gives strict model validation, discriminated unions for agent-message payloads, timezone-aware datetime normalization, JSON round trips, and immutable records where appropriate.

The project now has a small Python dependency surface. Future phases can build parsers, registries, analytical services, agents, artifact storage, APIs, and reports against these contracts without treating internal implementation strategies as public schema contracts.

## Alternatives considered

JSON Schema only: rejected for Phase 1 because Python model types, discriminated unions, and test ergonomics are useful immediately, while standalone JSON Schema can still be generated later if needed.

Dataclasses only: rejected because they would require more custom validation and serialization behavior for strict contracts.

FastAPI, SQLAlchemy, Alembic, PostgreSQL, orchestration frameworks, analytics libraries, and LLM libraries: deferred because Phase 1 defines contracts only and does not implement APIs, persistence, workflows, statistical execution, or language-model behavior.

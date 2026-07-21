# ADR 005: Deterministic Dataset Registry

## Status

Accepted for Phase 2.

## Context

Polaris needs an early deterministic step that can identify candidate datasets before data-quality review, statistical specification, causal assessment, and artifact generation. Phase 1 already defines the `DatasetManifest` contract, including provider, status, variables, coverage, license, methodology, warnings, and access restrictions.

Phase 2 manages metadata only. It must not retrieve observations, download data, introduce application services, use databases, or delegate candidate selection to probabilistic systems.

## Decision

Polaris will use a small in-memory `DatasetRegistry` backed by local JSON manifest files. Loaders parse UTF-8 JSON, validate every record through the existing `DatasetManifest` schema, load files in deterministic filename order, reject malformed or schema-invalid manifests with path context, and ignore non-JSON files.

Search uses a frozen structured `DatasetSearchQuery` and returns frozen `DatasetSearchResult` records. Filters across fields use AND semantics. Multiple values within one field use ANY semantics unless keyword matching explicitly requests `all`. Identifiers use exact normalized matching. Text filters use case-insensitive substring checks. Results include matched variable identifiers, match reasons, warning and access-restriction metadata, and temporal or geographic coverage details when those filters are requested.

Temporal coverage matching supports full containment, partial overlap, no overlap, and open-ended ranges. Geographic matching is limited to exact manifest codes and names represented in manifest descriptions. Phase 2 does not infer country membership from broad regional or global labels.

## Consequences

The registry is deterministic, testable, local, and aligned with the Phase 1 schema boundary. It gives future dataset-selection agents a stable metadata-search surface without requiring network access, persistence infrastructure, analytical engines, or LLMs.

File-backed manifests are sufficient now because the catalog is small, candidate-focused, and versionable in Git. Future persistence can be added behind the registry interface once scale, concurrency, indexing, or operational requirements are demonstrated.

The registry does not claim dataset suitability. A match only means manifest metadata satisfied explicit filters. Warning-bearing datasets remain visible by default so later review stages can evaluate limitations.

## Alternatives considered

Database-backed registry: deferred because Phase 2 does not need concurrency, querying at scale, migrations, or operational persistence.

Elasticsearch or other search services: deferred because structured deterministic filters are enough for current metadata search and are easier to test and explain.

Embedding or vector search: rejected for Phase 2 because semantic retrieval would introduce probabilistic behavior, external dependencies, and less transparent match explanations.

LLM-based dataset selection: deferred because early candidate search must be auditable and must not infer suitability beyond validated manifest metadata.

Custom registry schemas separate from `DatasetManifest`: rejected because Phase 1 already established the metadata contract, and duplicating it would create drift.

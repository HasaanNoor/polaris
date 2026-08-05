# ADR 014: Real Dataset Validation Runner

## Status

Accepted

## Context

Phase 11 must prove that Polaris can process official downloaded datasets through the
existing Phase 3 through Phase 9 research pipeline. The phase is validation-focused and
must not introduce new analytical methods, new agents, retrieval, databases, APIs, or
frontend surfaces.

The available official downloads include World Bank WDI, WHO GHO exports, and UNESCO
UIS exports. These sources use provider-native layouts. In particular, the World Bank
WDI bulk CSV stores one indicator per row with years as columns, while Phase 3 ingestion
expects a manifest whose variables map directly to source columns.

## Decision

Add a `polaris.realdata` package for Phase 11 validation. It provides:

- automatic discovery of downloaded official CSV datasets under `data/raw`;
- schema, country identifier, year identifier, variable, and missing-value inspection;
- manifest-to-file checksum, access URL, and column compatibility checks;
- a deterministic World Bank WDI validation extract that reshapes selected official WDI
  indicators into the existing Phase 3 country-year tabular contract;
- an end-to-end runner that executes ingestion, statistical analysis, evidence
  extraction, all domain agents, coordination, deterministic synthesis, and report
  generation without changing prior phase services.

The compatibility extract is a validation artifact, not a new ingestion architecture.
It preserves the original downloaded source path in the generated manifest description
and records the prepared extract checksum in the manifest used by Phase 3.

## Consequences

Phase 11 validates the existing architecture against real official source data while
keeping earlier phase boundaries intact. Provider-native reshaping remains explicit and
deterministic in the validation layer, avoiding hidden changes to ingestion behavior.

The runner currently uses WDI as the complete end-to-end dataset because the existing
provider metadata declares health, economic, and education variables from one official
bulk file. WHO and UNESCO downloads are discovered and schema-profiled, but broader
provider-specific end-to-end extracts are deferred until their manifests declare
pipeline-ready variable sets.

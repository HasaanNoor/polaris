# ADR-018: Curated WHO Health Panel

## Status

Accepted.

## Context

Polaris now has a reproducible WHO Global Health Observatory acquisition catalog and local official WHO GHO OData snapshots. Acquisition alone is not integration: downloaded files include country rows, aggregates, sex-specific rows, age-specific concepts, modeled estimates, projections, sparse survey-like series, and indicator-specific schemas. Promoting all downloaded rows would mix incompatible concepts and weaken downstream provenance.

## Decision

Phase 15 adds `src/polaris/who` as a curated integration layer between immutable WHO raw snapshots and the existing Phase 3/12/13 pipeline. The layer profiles each downloaded indicator, validates catalog SHA-256 checksums, applies explicit reviewed variable mappings, filters dimensions deterministically, excludes aggregate entities from the default country-year panel, and preserves value-level WHO provenance.

The default panel promotes all compatible HIGH-suitability indicators and selected MEDIUM indicators whose actual schemas support a single reviewed country-year headline concept. LOW indicators are profiled and tracked as deferred by default. Both-sexes rows are preferred only when WHO supplies an explicit both-sexes category; male and female rows are never averaged. Age groups are retained only when they are part of the indicator definition, such as neonatal, under-five, or adult indicators; age groups are never silently collapsed. WHO modeled estimates may be retained when they are the provider's headline comparable series, but projection rows are kept separate from historical observations and excluded unless a mapping explicitly accepts projections.

WHOHealthPanel exports a deterministic analytical CSV, a Phase 3-compatible DatasetManifest, a JSON quality summary, variable catalog, deferred-indicator registry, and separate value-provenance metadata. The exported panel enters Phase 12 as an ordinary provider dataset through existing generic `DatasetIngestionResult`, `DatasetHarmonizationConfig`, and `VariableMapping` contracts. Phase 13 examples reuse the existing project orchestrator; no WHO-specific agent or orchestration path is introduced.

## Consequences

The raw WHO provider files remain immutable and ignored by Git. Integration rules are versioned and auditable. Downstream analysis can use a compact country-year panel while still tracing every value to a WHO indicator ID, source row, source file, checksum, dimension filters, unit, and acquisition catalog reference. Not all acquired WHO indicators are analysis-ready: deferred indicators remain visible in a machine-readable registry with reasons and future work.

The current Phase 15 panel is deterministic and offline. It does not infer undocumented units, fuzzy-match country names, impute missing values, average sex groups, average age groups, merge projections with history, or resolve duplicate selected rows arbitrarily. Some country names remain ISO-3 codes where the existing exact normalizer has no reviewed country-name table.

## Alternatives considered

- Integrate all downloaded WHO indicators: rejected because low- and medium-suitability files include aggregate-only, projected, sparse, or highly dimensional structures.
- Treat acquisition catalog suitability as sufficient: rejected because each actual snapshot still requires schema inspection, unit review, and duplicate-key validation.
- Average male and female rows into both-sexes values: rejected because WHO supplies explicit sex categories for headline series and averaging would create derived values outside provider definitions.
- Collapse age groups into all-age values: rejected because some age groups define the concept and others are subgroup dimensions that require separate review.
- Add WHO-specific Phase 12 logic or a WHO agent: rejected because the exported panel can adapt to existing generic ingestion, harmonization, evidence, agent, synthesis, reporting, and project APIs.
- Mutate raw OData snapshots into normalized files: rejected because raw provider bytes and catalog checksums must remain stable evidence inputs.

# ADR-015: Cross-Dataset Country-Year Harmonization

## Status

Accepted.

## Context

Phase 11 validated one official provider dataset through the existing Polaris pipeline. Phase 12 needs a way to combine reviewed variables from multiple official providers without changing definitions silently, guessing country identifiers, hiding missingness, or losing traceability to source rows.

The available local files include World Bank WDI, WHO GHO exports, and UNESCO UIS archives. WDI has already been prepared into a Phase 3-compatible validation extract. WHO life expectancy has country-level annual records with `SpatialDimValueCode`, `Period`, `Location type`, `Period type`, sex dimensions, and numeric values. UNESCO national files expose country/year/value structures, but indicator-specific unit and definition review is still incomplete for the initial subset.

## Decision

Polaris adds a separate `polaris.harmonization` package between Phase 3 ingestion and Phase 4 analysis. Harmonization consumes immutable `DatasetIngestionResult` objects and produces a derived `HarmonizedDataset` with country-year records, value-level provenance, dataset-level provenance, findings, missingness reasons, and a quality summary.

Country-year is the initial canonical unit because the current analysis pipeline already supports tabular country-year records and the first official providers publish annual country indicators. ISO 3166-1 alpha-3-style codes are preferred where providers expose them. Aggregates, regions, income groups, and global records are not treated as countries; they are excluded from country-level joins by default and counted in findings.

Country matching is exact and rule-based. Fuzzy matching is prohibited because it can turn ambiguous names into false country identities. Variable equivalence requires explicit reviewed `VariableMapping` records. Similar labels from different providers remain separate canonical variables unless a request declares a shared canonical variable and explicit provider precedence. Units and definitions are not silently converted. Only declared transformations such as canonical renaming and explicit percent/proportion conversion are supported.

Duplicate country-year-variable values are never averaged automatically. Requests either reject duplicates or preserve unresolved conflicts as findings. Provider precedence is permitted only when explicitly configured and is recorded as provenance/finding metadata. Every harmonized value carries a receipt: source dataset ID, provider, checksum, source variable, source field, source row and line numbers, original country/year/value, normalized value, transformation, unit, retrieval timestamp, manifest ID, and source path.

The harmonized CSV export is Phase 3-compatible and generated with a manifest, but it is explicitly a derived artifact. Raw provider files and Phase 3 ingestion results are not mutated.

Phase 12 integrates a small real subset: WDI GDP per capita with WHO life expectancy at birth for both sexes. WHO HALE and UNESCO DEM, SDG, SCN-SDG, and SDG11 files are deferred from initial harmonization until variable-specific mapping, units, and definitions are reviewed.

## Consequences

- Multi-provider analysis can enter the existing Phase 4-9 pipeline without redesigning those phases.
- Harmonized examples can be reproduced offline from local raw files and generated manifests.
- Missingness, excluded aggregates, duplicate keys, conflicts, and transformations are visible rather than collapsed into one null category.
- The country normalizer remains intentionally conservative and will need reviewed mapping additions as more providers and territories are integrated.
- UNESCO integration remains schema-profiled but not claimed as end-to-end harmonized.

## Alternatives considered

- Extending Phase 3 ingestion to join providers was rejected because ingestion validates one source file against one manifest and should not own cross-provider semantics.
- Using fuzzy country-name matching was rejected because false positives would be hard to audit and could silently alter geography.
- Automatically merging same-named variables was rejected because provider definitions, sex/age scope, estimate methods, and revisions can differ.
- Averaging duplicate provider values was rejected because duplicates usually indicate dimensional ambiguity or unresolved source conflict.
- Converting units automatically was rejected except for explicitly declared transformations because scale and definition changes require review.
- Integrating all WHO and UNESCO files immediately was rejected because a small reviewed subset is safer than broad unreviewed harmonization.

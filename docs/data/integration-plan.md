# Real-Data Integration Plan

## Phase 15 WHO Panel Integration

WHO acquisition and WHO integration are separate. Acquisition stores immutable official OData snapshots and an acquisition catalog. Integration reads those local files, validates checksums, profiles observed schemas, applies reviewed mappings, filters dimensions, excludes aggregates, normalizes countries/years through existing Phase 12 behavior, and exports a derived Phase 3-compatible CSV plus metadata.

The WHO panel enters Phase 12 as a generic provider dataset. Phase 12 does not depend on WHO-specific logic; it receives `DatasetIngestionResult`, `DatasetHarmonizationConfig`, and `VariableMapping` objects as it does for other providers. Example artifacts under `examples/who` demonstrate WDI plus WHO harmonization and a Phase 13 project.

## Phase 16 WGI Panel Integration

WGI acquisition stores official World Bank API CSV ZIP snapshots under `data/raw/world_bank/wgi/`. Integration validates checksums, profiles actual CSV ZIP schemas, selects the official central governance estimate for analysis, preserves uncertainty companion series, excludes aggregates and territories by default, and exports a derived Phase 3-compatible CSV plus metadata.

The WGI panel enters Phase 12 as a generic provider dataset. Phase 12 does not depend on WGI-specific logic; WDI+WGI and WDI+WHO+WGI examples under `examples/wgi` use the same ingestion, harmonization, analysis, evidence, agent, coordination, synthesis, reporting, and project orchestration contracts as other providers.

## Phase 17 UNESCO Education Panel Integration

UNESCO acquisition and UNESCO education integration are separate. Phase 17 reads only existing local files under `data/raw/unesco/`, profiles DEM, SDG, SCN-SDG, and SDG11, and integrates only reviewed SDG national education indicators. Raw UNESCO files remain unchanged and excluded from Git.

The UNESCO panel enters Phase 12 as a generic provider dataset. Phase 12 does not depend on UNESCO-specific logic; WDI+UNESCO and WDI+WHO+WGI+UNESCO examples under `examples/unesco` use the same ingestion, harmonization, analysis, evidence, agent, coordination, synthesis, reporting, and project orchestration contracts as other providers. Phase 17 does not average sex categories, combine age cohorts, merge education levels, interpolate missing years, impute values, or create an education index.

Phase 10 provides acquisition infrastructure, Phase 11 validated official WDI data through Phases 3-9, and Phase 12 adds deterministic country-year harmonization for reviewed multi-provider subsets. Real-data research integration remains staged because provider files must be selected, snapshotted, validated, reviewed, harmonized where needed, analyzed, and carried through the existing deterministic artifact pipeline before they become reliable Polaris research inputs.

## Workflow

1. Select official dataset and release/version.
2. Record source page, license, citation, and retrieval date.
3. Download through Polaris provider adapter where supported.
4. If automated acquisition is unavailable, place the official file into the expected acquisition workflow without modifying raw bytes.
5. Create immutable raw snapshot.
6. Calculate and store SHA-256 checksum.
7. Generate Phase 3-compatible `DatasetManifest`.
8. Register the dataset as `real_provider`.
9. Run Phase 3 validation.
10. Inspect schema, country identifiers, year identifiers, missingness, units, and coverage.
11. Define a reviewed variable subset.
12. For multi-provider work, define explicit country-year harmonization configs and variable mappings.
13. Validate country/year normalization, unit and definition compatibility, duplicate keys, aggregate exclusions, conflicts, and missingness.
14. Export a derived Phase 3-compatible harmonized dataset when harmonization succeeds.
15. Run Phase 4 analysis.
16. Verify evidence, agent, coordination, synthesis, and reporting behavior through Phases 5-9.
17. Preserve all outputs and provenance for reproducibility.

## Rollout

### Round 1

Datasets:

- World Bank WDI
- WHO GHO
- UNESCO UIS

Goal: prove the complete Phase 2-9 pipeline using real economic, education, and health data.

Round 1 now has WDI end-to-end validation, a Phase 12 WDI plus WHO life-expectancy harmonization example, a curated WHO health panel, and a curated UNESCO education panel. Additional WHO and UNESCO variables remain staged or deferred until reviewed mappings and dimensions are safe.

### Round 2

Datasets:

- V-Dem
- Worldwide Governance Indicators (integrated first in Phase 16)
- Transparency International CPI

Goal: add governance and institutional analysis.

Round 2 should begin only after Round 1 produces at least one reproducible case study. It should end with a governance-focused case study that documents expert-coded, perception-based, and composite-measure limitations.

### Round 3

Datasets:

- UNDP HDI
- Our World in Data
- IMF WEO

Goal: add composite development, environmental, and macroeconomic context.

Round 3 should begin only after governance integration has been validated through an end-to-end case study. It should end with a cross-domain case study that distinguishes observed indicators, composite indices, estimates, and forecasts.

## Operating Rules

- Do not mutate raw provider files.
- Do not treat adapter availability as evidence that acquisition succeeded.
- Do not treat dataset selection as validation.
- Do not add exact indicator codes until they are verified against current repository metadata or an acquired source snapshot.
- Do not promote a variable subset without review of units, missingness, coverage, and comparability.
- Preserve source provenance in every step so downstream reports can identify which source bytes produced each result.
- Do not harmonize country names fuzzily.
- Do not treat regions, income groups, or global aggregates as country observations.
- Do not merge same-named variables across providers without reviewed mappings, compatible units/definitions, and explicit precedence when needed.

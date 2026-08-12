# ADR-020: UNESCO Education Panel

## Status

Accepted.

## Context

Polaris needs a reviewed education source that can join with WDI, WHO, and WGI for country-year research without weakening provenance or comparability rules. Local UNESCO UIS files are already present under `data/raw/unesco/` for DEM, SDG, SCN-SDG, and SDG11. The SDG national file contains education indicators with provider labels and country-year values. DEM contains demographic/economic support indicators, SCN-SDG contains science/R&D indicators, and SDG11 contains cultural heritage expenditure indicators, so they are profiled but not promoted into the default education panel.

## Decision

Phase 17 adds `src/polaris/unesco` to build a deterministic `UNESCOEducationPanel` from locally downloaded UNESCO UIS SDG national data. Only reviewed headline indicators with explicit UNESCO IDs and labels are integrated. The default panel preserves literacy cohorts, completion levels, tertiary gross enrolment, pre-primary net enrolment, out-of-school age groups, selected attainment rates, teacher ratios, and education expenditure measures as separate variables.

The panel excludes aggregate entities and territories by default through Phase 12 country normalization. It does not fuzzy-match names, average sex-specific values, average age cohorts, aggregate education levels, interpolate missing years, impute values, convert units silently, or create a custom education index. Value-level provenance records source file, checksum, row number, original country/year/value, normalized value, unit, dimensions, applied filters, UNESCO indicator ID, and ruleset version.

The exported CSV and manifest remain Phase 3-compatible. Phase 12 consumes the UNESCO export through generic `DatasetIngestionResult`, `DatasetHarmonizationConfig`, and `VariableMapping` contracts. Phase 13 examples remain associational and non-causal.

## Consequences

UNESCO becomes the primary Polaris education source for reviewed cross-domain education analysis. Enrollment definitions remain distinct because gross enrolment, net enrolment, adjusted net enrolment, attendance, completion, and attainment measure different concepts. Adult and youth literacy remain separate cohorts. Primary, lower-secondary, upper-secondary, tertiary, and pre-primary variables remain separate education levels. Missing years remain missing.

The deferred registry is intentionally large because the local SDG label file includes many subgroup, parity, sex-specific, wealth, location, disability, proficiency, and learning-assessment variants. These indicators may support future equity or learning-outcome research after separate dimension review, but they are not collapsed into the default country-year panel.

## Alternatives considered

- Integrating every UNESCO SDG indicator was rejected because it would mix education and non-education concepts and silently collapse dimensions.
- Using DEM, SCN-SDG, or SDG11 as education panel sources was rejected for the default panel because their downloaded content is demographic/economic, science/R&D, or cultural heritage rather than headline education.
- Deriving gender parity or education composite scores was rejected because Phase 17 preserves provider-supplied values and does not fabricate derived measures.
- Adding UNESCO-specific Phase 12 logic was rejected because the generic harmonization contracts already support provider-neutral country-year integration.

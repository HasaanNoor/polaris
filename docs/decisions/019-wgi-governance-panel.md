# ADR-019: WGI Governance Panel

## Status

Accepted.

## Context

Polaris needs a reviewed governance dataset that can join with WDI and WHO country-year data without adding provider-specific downstream paths. The World Bank Worldwide Governance Indicators are the first dedicated governance source integrated because they provide official country-year governance estimates for six institutional dimensions, expose uncertainty metadata, and are available through official World Bank DataBank/API downloads.

WGI indicators are composite perception-based estimates, not causal measures or direct administrative observations. The 2025 revision recalculates historical values and reports central governance estimates plus companion uncertainty and absolute-score metadata.

## Decision

Phase 16 adds `src/polaris/wgi` as a deterministic integration layer for official World Bank WGI API CSV ZIP snapshots. Acquisition downloads one official World Bank source `3` (`WGI`) ZIP per dimension into `data/raw/world_bank/wgi/`, records retrieval timestamps and SHA-256 checksums, and reuses identical snapshots by checksum.

All six WGI dimensions remain separate canonical variables: voice and accountability, political stability, government effectiveness, regulatory quality, rule of law, and control of corruption. No composite governance score is created. The analytical value is the official central governance estimate (`GOV_WGI_*.EST`). Standard errors (`*.SE`), source counts (`*.SR`), absolute governance scores (`*.SC`), and score confidence bounds (`*.SC_LB`, `*.SC_UB`) are preserved as metadata and value provenance. Current WGI 2025 API exports do not expose percentile-rank series in the integrated source; percentile fields remain explicit and null rather than substituting absolute scores.

Country-year remains the integration grain. Country and year handling reuse Phase 12 exact normalization and safe integer years. Aggregates and territories are excluded from the default WGI panel. Missing years and missing dimensions are not interpolated, forward-filled, backfilled, smoothed, or imputed.

The `WGIGovernancePanel` exports a deterministic CSV, Phase 3-compatible manifest, JSON quality summary, variable catalog, and optional separate value provenance. The exported CSV enters Phase 12 as a generic dataset. Phase 13 examples use WDI GDP per capita, WHO life expectancy, and WGI government effectiveness in an associational OLS specification with Governance, Economics, and Public Health agents.

## Consequences

WGI can now be combined with WDI and WHO through existing Phase 3, Phase 12, and Phase 13 contracts. Raw provider ZIPs remain ignored by Git and immutable. Panel identity is deterministic from source checksums, selected variables, country/temporal rules, schema version, and ruleset version; creation timestamps do not affect identity.

The integration preserves measurement uncertainty but does not introduce uncertainty-weighted regression because Phase 4 does not yet support it. Reports and evidence must describe WGI relationships as associations, not causal effects. Users can trace every analytical governance value back to an official indicator ID, source snapshot, checksum, row, original country/year, estimate, and companion uncertainty metadata.

## Alternatives considered

- Integrate V-Dem first: deferred because its expert-coded variable universe requires broader concept selection, versioning, and uncertainty review.
- Integrate Transparency International CPI first: deferred because it covers one corruption concept rather than the broader institutional dimensions needed for cross-domain analysis.
- Average the six WGI dimensions into one governance score: rejected because the dimensions measure distinct institutional concepts and averaging would create a custom composite outside the provider definition.
- Use WGI absolute scores or percentile-style ranks as analytical substitutes for estimates: rejected because Phase 16 uses the central governance estimate and preserves secondary scale metadata separately.
- Interpolate missing WGI years: rejected because missingness is meaningful source coverage information and interpolation would create non-provider values.
- Add WGI-specific Phase 12 logic: rejected because the derived panel fits existing generic Phase 3 and Phase 12 interfaces.
- Make governance examples causal: rejected because the data and default Polaris evidence standards support associational, non-causal interpretation only.

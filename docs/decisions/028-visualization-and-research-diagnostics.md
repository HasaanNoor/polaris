# ADR-028: Visualization and Research Diagnostics

## Status

Accepted.

## Context

Polaris now produces validated ingestion artifacts, harmonized country-year panels,
statistical results, panel results, causal results, causal-study metadata, robustness
artifacts, evidence artifacts, reasoning artifacts, project outputs, reports, and MCP
responses. Researchers need clear figures and diagnostics for inspecting those artifacts.

## Decision

Phase 25 adds `src/polaris/visualization` as a downstream representation layer:

`statistical engine -> research result -> visualization layer -> human interpretation`

The package introduces strict `VisualizationSpecification` contracts, structured
`VisualizationArtifact` outputs, deterministic visualization IDs, plotting-ready data rows,
axis/legend/annotation metadata, warnings, limitations, provenance, and output references.

Visualization is not statistical estimation. Builders consume existing values from Phase 3,
Phase 4, Phase 12, Phase 21, Phase 22, Phase 23, and Phase 24 artifacts. They do not rerun
alternative models, select interesting countries, impute data, infer treatment timing, or
create empirical claims from visual appearance.

Matplotlib is selected as an optional dependency through the `visualization` extra because it is
mature, local, scriptable, suitable for deterministic PNG/SVG research figures, and does not
require a browser runtime or dashboard server. Rendering uses the noninteractive Agg backend.

Plotting-ready data is preserved as CSV/JSON because the rendered figure is not the only
reproducibility artifact. A reviewer should be able to inspect the exact rows rendered even when
graphical rendering is disabled.

Visualization IDs depend on source artifact IDs, available dataset/checksum provenance,
the full specification, schema version, and ruleset version. Timestamps are excluded from
identity. Generated PNG, SVG, CSV, and JSON files are derived artifacts under predictable
visualization output directories.

Visual integrity rules are part of the contract. Phase 25 preserves axis values, negative
values, confidence intervals, missing-data status, failed robustness variants, non-significant
estimates, explicit units, event-time ordering, and placebo-vs-actual distinctions. Axis
truncation and many-entity plots require explicit configuration.

Reports may embed or reference visualization artifacts. Project orchestration gains an opt-in
`VISUALIZE` stage. MCP gains typed visualization tools. Evidence and reasoning remain separate:
visualizations represent evidence but do not independently generate claims.

## Deferred

Phase 25 defers interactive dashboards, browser-based visualization editors, arbitrary user
plotting code, geographic choropleths, animated time-series maps, automated chart
recommendation, AI-generated chart selection, automatic outlier interpretation, publication-theme
customization, and a frontend visualization UI.

## Consequences

Polaris becomes easier to inspect and demonstrate while preserving the deterministic analytical
core. The dependency footprint remains controlled because matplotlib is optional and isolated.
Future interactive or frontend visualization work can build on `VisualizationArtifact` without
changing statistical estimators or evidence contracts.

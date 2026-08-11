# Planned Dataset Catalog

## Curated WHO GHO Panel

Phase 15 adds a derived reviewed dataset, `WHOHealthPanel`, built from official local WHO GHO OData snapshots recorded in `data/raw/who/gho/acquisition_catalog.json`. The panel is not a raw provider file. It exports `examples/who/who_health_panel_sample.csv` and `examples/who/who_health_panel_manifest.json` as Phase 3-compatible derived artifacts, with quality and deferred-indicator metadata beside the CSV.

Current local status: 42 conceptual WHO targets, 41 resolved/downloaded official snapshots, 28 indicators integrated into the reviewed country-year panel, and 14 deferred. Deferred indicators are not forgotten; they are listed in `examples/who/who_deferred_indicators.json` with reasons and future work.

## Curated World Bank WGI Governance Panel

Phase 16 adds a derived reviewed dataset, `WGIGovernancePanel`, built from official World Bank WGI source `3` API CSV ZIP snapshots stored under `data/raw/world_bank/wgi/`. The panel exports `examples/wgi/wgi_governance_panel_sample.csv`, `examples/wgi/wgi_governance_panel_manifest.json`, `examples/wgi/wgi_governance_quality_summary.json`, and `examples/wgi/wgi_variable_catalog.json` as small provider-derived artifacts.

Current local status: six WGI dimensions acquired, validated, and integrated from the 2025 revision API source last updated 2026-03-18. The panel keeps all dimensions separate and preserves standard errors, number of sources, absolute governance scores, and score confidence bounds in metadata/provenance. V-Dem and Transparency International CPI remain planned only.

This catalog records planned real-world dataset support. It distinguishes provider adapter implementation from dataset selection, download, validation, and end-to-end integration. A selected dataset has been identified as strategically relevant, but it must still pass acquisition, manifest generation, Phase 3 validation, variable review, and at least one reproducible Phase 4-9 case study before Polaris treats it as integrated.

| Provider | Dataset | Research domain | Geographic coverage | Temporal structure | Expected format | Polaris priority | Adapter status | Download status | Integration status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| World Bank | World Development Indicators | economics, development, demographics, infrastructure, education, health | Broad global country and economy coverage, subject to indicator-specific availability | Country-year indicator time series | Provider file or API-derived tabular snapshot | Round 1 | Implemented | Not assumed downloaded | Not yet validated end to end | First baseline source for controls, outcomes, and cross-domain context. |
| World Health Organization | Global Health Observatory | public health, mortality, disease burden, health systems | Broad global country coverage, subject to indicator-specific reporting and modeled estimates | Country-year or country-period indicator series, depending on indicator | Provider file or API-derived tabular snapshot | Round 1 | Implemented | Not assumed downloaded | Not yet validated end to end | Primary health source; units and estimate methods must be reviewed per indicator family. |
| UNESCO Institute for Statistics | UIS education data | education, human development | Broad global country coverage, subject to national reporting gaps | Country-year education indicator series | Provider file or API-derived tabular snapshot | Round 1 | Implemented | Not assumed downloaded | Not yet validated end to end | Primary education source; level definitions and reporting gaps require review. |
| V-Dem Institute | V-Dem dataset | governance, democracy, institutions, civil liberties | Broad country coverage, with historical and contemporary observations depending on variable | Country-year institutional indicators | Official release file | Round 2 | Not implemented | Not downloaded | Planned only | Expert-coded measures require versioning, uncertainty review, and careful concept selection. |
| World Bank | Worldwide Governance Indicators | governance, institutions | Broad country coverage, subject to source availability | Country-year governance indicators | Official World Bank API CSV ZIP | Round 2 | Implemented | Downloaded locally | Integrated | Six separate WGI dimensions; central estimates used analytically and uncertainty preserved. |
| Transparency International | Corruption Perceptions Index | governance, corruption | Broad country coverage, but not universal and may vary by year | Annual country score series | Official release file | Round 2 | Not implemented | Not downloaded | Planned only | Perception-based composite; should be used with interpretation limits. |
| UNDP Human Development Reports | Human Development Index data | human development, education, health, income | Broad country coverage, subject to reporting and release availability | Annual country indicators and composite indices | Official release file | Round 3 | Not implemented | Not downloaded | Planned only | Composite and component indices must preserve release/version and methodology notes. |
| Our World in Data | OWID cross-domain datasets | environment, energy, health, demographics, development | Varies by dataset and upstream source | Usually country-year or location-year series | Public tabular files | Round 3 | Not implemented | Not downloaded | Planned only | Requires source-lineage review because OWID often curates upstream providers. |
| International Monetary Fund | World Economic Outlook | macroeconomics, fiscal, growth, inflation | Broad IMF member and economy coverage, subject to series availability | Annual and forecast vintage series | Official release file | Round 3 | Not implemented | Not downloaded | Planned only | Forecasts, estimates, and historical observations must be distinguished by release vintage. |

## Status Definitions

- Adapter implemented: Polaris has a provider adapter in `src/polaris/providers`.
- Dataset selected: the dataset is included in the planned data strategy.
- Dataset downloaded: an official source file has been acquired through the Phase 10 workflow and stored as an immutable raw snapshot.
- Dataset validated: Phase 3 validation and schema review have been run against the acquired snapshot.
- Integrated end to end: the dataset has supported a reproducible case study through analysis, evidence, agents, coordination, synthesis, and reporting.

Current Phase 10 built-in adapters exist only for World Bank WDI, WHO GHO, and UNESCO UIS. This catalog does not imply that any selected dataset has already been downloaded, validated, or integrated end to end.

# Provider Selection Strategy

Polaris selects real-world datasets for deterministic, provenance-first country-year research. A selected provider is not the same as a downloaded, validated, harmonized, or fully integrated dataset. Phase 10 implements acquisition infrastructure and built-in adapters for the first three providers: World Bank WDI, WHO GHO, and UNESCO UIS. Phase 11 validates WDI end to end. Phase 12 validates a narrow WDI plus WHO life-expectancy country-year harmonization example. Phase 15 integrates a curated subset of locally downloaded official WHO GHO snapshots into a reviewed WHOHealthPanel. Phase 16 integrates official World Bank WGI API snapshots into a reviewed WGIGovernancePanel.

## Phase 15 WHO Status

WHO GHO status is tracked as four separate states:

- Acquired: 41 official WHO GHO OData snapshots are present under `data/raw/who/gho`.
- Profiled: each downloaded snapshot can be profiled by `src/polaris/who/profiling.py` against the acquisition catalog.
- Integrated: 28 reviewed indicators are promoted into the default WHOHealthPanel with explicit country/year, dimension, unit, and provenance rules.
- Deferred: 14 targets remain machine-readable deferrals because they are unresolved, LOW suitability, projection-prone, aggregate-only, sparse, or require additional dimension review.

## Selection Criteria

Provider selection favors sources that can support reproducible downstream analysis without weakening the evidence boundary between source data, validation, analysis, synthesis, and reporting.

- Official or academically credible source: the publisher should be a recognized public institution, research consortium, or established statistical source.
- Transparent methodology: definitions, collection methods, revisions, caveats, and uncertainty should be documented enough for review.
- Broad country coverage: sources should support cross-country comparison, with limitations recorded instead of hidden.
- Longitudinal coverage where possible: annual or repeated time coverage is preferred for country-year analysis.
- Stable identifiers: countries, years, variables, and releases should have stable identifiers or stable mapping rules.
- Documented variables and units: variable meaning, units, scaling, and transformations must be explicit before analysis.
- Reproducible access: the source file, release, or API response should be capturable as an immutable raw snapshot.
- Licensing clarity: access and reuse terms must be reviewable before a dataset is promoted beyond selection.
- Relevance to Polaris research domains: the dataset should support governance, economics, education, public health, human development, environment, or macroeconomic research.
- Source provenance preservation: Polaris must be able to record source page, citation, retrieval date, checksum, and raw snapshot metadata.
- Country-year compatibility: records should be transformable into country-year or country-year-indicator structures without uncontrolled manual editing.
- Deterministic downstream suitability: the dataset should support repeatable validation, missingness review, variable selection, and statistical analysis.

## Priority Groups

### Round 1: Core Development, Health, and Education

Round 1 is intended to prove the complete Phase 2-9 pipeline using real economic, education, and health data. These providers already have Phase 10 adapter implementations, but that does not mean their datasets have been downloaded, validated, or used in an end-to-end case study.

| Provider | Primary research role | Supported domains | Reason for inclusion | Known limitations | Intended round | Adapter implemented | Dataset selected | Dataset downloaded | Dataset validated | Integrated end to end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| World Bank World Development Indicators | Cross-country development baseline | economics, development, demographics, infrastructure, health, education | Broad country-year indicator coverage and strong fit for baseline controls and outcomes. | Indicator definitions vary by series; missingness and country aggregation rules require review; revisions can change historical values. | Round 1 | Yes | Yes | Yes, locally | Yes | Yes |
| WHO Global Health Observatory | Public-health outcomes and system indicators | public health, mortality, health systems, disease burden | Official global health source with health-specific methodology and country-level indicators. | Health estimates may depend on modeled values, reporting quality, and changing definitions; units must be reviewed by indicator family. | Round 1 | Yes | Yes | Yes, locally | Life expectancy subset validated | WDI+WHO life expectancy subset |
| UNESCO Institute for Statistics | Education access, attainment, and finance | education, human development | Official education statistics source with education-specific definitions and global coverage. | Education systems differ across countries; enrollment and completion metrics need level-specific comparability review; reporting gaps are expected. | Round 1 | Yes | Yes | Yes, locally | Schema-profiled | Not yet |

### Round 2: Governance and Institutions

Round 2 adds institutional context after the core real-data pipeline is proven. These datasets are selected for future integration, but no Phase 10 provider adapters currently exist for them.

| Provider | Primary research role | Supported domains | Reason for inclusion | Known limitations | Intended round | Adapter implemented | Dataset selected | Dataset downloaded | Dataset validated | Integrated end to end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V-Dem | Democracy and institutional measurement | governance, institutions, civil liberties | Academically credible source for institutional concepts that are not captured by administrative economic or health data. | Expert-coded measures require uncertainty review, version tracking, and careful interpretation; variables are numerous and conceptually overlapping. | Round 2 | No | Yes | Not assumed | Not yet | Not yet |
| World Bank Worldwide Governance Indicators | Governance perception and institutional quality | governance, institutions | Useful country-year governance series aligned with common research controls and cross-country comparisons. | Composite perception indicators require methodological caution; margins of error and source aggregation must be surfaced. | Round 2 | Yes | Yes | Yes, locally | WGI panel validated | WDI+WGI and WDI+WHO+WGI examples |
| Transparency International Corruption Perceptions Index | Corruption perception context | governance, institutions | Widely used summary measure for perceived public-sector corruption. | Perception-based and composite; scale changes, uncertainty, and limited causal interpretation require explicit warnings. | Round 2 | No | Yes | Not assumed | Not yet | Not yet |

### Round 3: Human Development, Environment, and Macroeconomics

Round 3 broadens Polaris from core sector indicators into composite development, environmental, and macroeconomic context. These providers are selected for planning only until adapters and validation work are added.

| Provider | Primary research role | Supported domains | Reason for inclusion | Known limitations | Intended round | Adapter implemented | Dataset selected | Dataset downloaded | Dataset validated | Integrated end to end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UNDP Human Development Reports / Human Development Index data | Composite human development measures | human development, education, health, income | Provides interpretable composite indices for high-level development comparisons. | Composite construction can hide component tradeoffs; release/version and methodology changes must be recorded. | Round 3 | No | Yes | Not assumed | Not yet | Not yet |
| Our World in Data | Curated cross-domain context | environment, energy, health, demographics, development | Useful harmonized public datasets and documentation across many research domains. | Aggregates many upstream sources; source lineage and variable-specific provenance must be checked before use. | Round 3 | No | Yes | Not assumed | Not yet | Not yet |
| IMF World Economic Outlook | Macroeconomic context and forecasts | macroeconomics, fiscal, growth, inflation | Established macroeconomic source for country-level macro context. | Forecast and estimate vintages must be separated from observed historical data; release versioning is essential. | Round 3 | No | Yes | Not assumed | Not yet | Not yet |

## Deferred Survey-Based Sources

Survey-based sources are valuable for social trust, values, attitudes, beliefs, public opinion, democratic legitimacy, and subjective wellbeing. Polaris defers them until the deterministic pipeline can handle wave-based samples, respondent-level metadata, weighting, and cross-wave harmonization without losing provenance.

Deferred sources include:

- World Values Survey
- Gallup World Poll
- Afrobarometer
- Arab Barometer
- European Social Survey
- Pew Research datasets

They are deferred because they commonly involve non-annual survey waves, changing variables across waves, restricted access, complex weighting, respondent-level harmonization, licensing constraints, and limited cross-country comparability. They may later enter Polaris through a survey-specific workflow rather than the initial country-year provider path.

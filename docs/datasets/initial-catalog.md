# Initial Dataset Catalog

All entries are **candidates pending review**. This catalog does not represent approved integrations.

Phase 2 adds a compact metadata-only example catalog in `catalog/datasets`. These JSON manifests are illustrative candidate records used to exercise registry loading, search, warnings, access restrictions, and coverage matching. They do not represent production integrations and must not be treated as verified current metadata.

| Source | Domain | Candidate Use | Required Review |
| --- | --- | --- | --- |
| World Bank World Development Indicators | development, economics, health, education, demographics | cross-country indicators and time series | licensing, revisions, indicator definitions, missingness |
| OECD Data and Statistics | economics, governance, education, innovation, wellbeing | OECD-country comparisons | membership coverage, comparability, methodology notes |
| United Nations Statistics Division | official statistics, SDG indicators, national accounts | official statistical standards and global indicators | source lineage, SDG metadata, revisions |
| UN agencies including UNDP, UNICEF, UNODC, UNHCR, FAO, and IOM | development, children, crime, displacement, food, migration | domain-specific international indicators | agency-specific definitions and coverage |
| WHO Global Health Observatory | public health | health outcomes, service coverage, risk factors | measurement methods, reporting quality, country coverage |
| UNESCO Institute for Statistics | education | enrollment, attainment, learning, education finance | assessment comparability and reporting gaps |
| IMF Data | macroeconomics, finance, fiscal | macroeconomic and financial indicators | revisions, country coverage, metadata completeness |
| ILOSTAT | labor | employment, labor force, wages, working conditions | survey comparability and definitions |
| V-Dem | governance, democracy, institutions | democracy and institutional indicators | expert-coding uncertainty and versioning |
| Quality of Government Institute | governance, institutions | curated governance and institutional datasets | source aggregation, variable definitions |
| World Values Survey | society, social trust, values | survey attitudes and values | waves, sampling, weighting, question wording |
| European Social Survey | society, social trust, attitudes | European survey comparisons | country-wave coverage, weighting, mode notes |
| Pew Research Center | public opinion, society, media, religion | survey findings and methodology examples | data access terms, sampling frames, wording |
| Transparency International Corruption Perceptions Index | governance, corruption | perception-based corruption indicator | composite methodology, uncertainty, interpretation limits |
| Varieties of Democracy related datasets | governance | institutional and democracy measurement | expert survey methods and uncertainty |
| UCDP | conflict | conflict events and organized violence | reporting bias, definitions, geocoding |
| ACLED | conflict, protest, political violence | event-level conflict and protest data | licensing, methodology, reporting bias |
| Polity Project | governance, regime characteristics | historical regime indicators | coding rules, continuity, limitations |
| International IDEA | elections, democracy | electoral and democracy datasets | definitions, coverage, update practices |
| Global Innovation Index | innovation | innovation composite indicators | weighting, normalization, sensitivity |

## Phase 2 Example Manifest Files

| Manifest | Provider | Purpose |
| --- | --- | --- |
| `world_bank_wdi.json` | World Bank | Illustrative development, health, education, and economic metadata with global aggregate coverage and warning metadata. |
| `who_gho.json` | World Health Organization | Illustrative public-health metadata with overlapping life-expectancy variables and methodology reference. |
| `unesco_uis.json` | UNESCO Institute for Statistics | Illustrative education metadata with access-restriction and licensing-warning examples. |

## Phase 3 Example CSV Files

Small synthetic CSV files in `data/examples` exercise local ingestion behavior for the three illustrative manifests. They are not official provider exports and must not be treated as downloaded source data.

| File | Purpose |
| --- | --- |
| `world_bank_wdi_sample.csv` | Synthetic WDI-shaped rows with valid floats, a `null` value, and extra country/year context columns. |
| `who_gho_sample.csv` | Synthetic WHO-shaped rows with valid floats, a `null` value, and one intentional type-conversion issue. |
| `unesco_uis_sample.csv` | Synthetic UNESCO-shaped rows with valid floats plus `..` and `null` missing-value tokens. |

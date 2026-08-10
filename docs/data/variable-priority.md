# Variable Priority

Polaris prioritizes variable families that support country-year research while preserving clear units, source provenance, and interpretation limits. This document intentionally avoids exact provider indicator codes unless they are already verified in repository files. Provider-specific codes should be added only during reviewed dataset integration.

## Phase 15 WHO Variables

WHO variables are promoted only through reviewed mappings in `src/polaris/who/mappings.py`. The current default panel includes core health outcomes and system-capacity measures such as life expectancy, HALE, adult mortality, maternal mortality, suicide mortality, health expenditure, doctor and nursing density, hospital beds, DTP3, MCV1, tuberculosis incidence, skilled birth attendance, under-five and neonatal mortality, UHC service coverage, selected NCD/nutrition/environment indicators, water, sanitation, PM2.5, and road-traffic mortality.

HIGH-suitability indicators form the core. MEDIUM indicators are integrated only where actual local schemas support deterministic filters, such as explicit both-sexes, total residence, child age, or adult age categories. LOW indicators remain deferred by default and require separate review before use.

## Economics and Development

| Variable family | Likely provider | Conceptual role | Likely analytical use | Unit or comparability concerns | Annual country-level coverage expected |
| --- | --- | --- | --- | --- | --- |
| GDP per capita | World Bank WDI; IMF WEO for macro context | Level of economic development and material living standards | Predictor, control, or outcome | Currency basis, constant versus current prices, purchasing-power adjustment, revisions | Yes, with gaps |
| GDP growth | World Bank WDI; IMF WEO | Economic performance and macroeconomic cycle | Outcome, predictor, or control | Real versus nominal growth and revised historical estimates | Yes, with gaps |
| Inflation | World Bank WDI; IMF WEO | Price stability and macroeconomic conditions | Predictor, control, or outcome | Consumer price methodology, extreme values, base-period differences | Yes, with gaps |
| Unemployment | World Bank WDI; IMF WEO where available | Labor-market slack and economic wellbeing | Outcome or control | Labor-force definitions, modeled estimates, informal employment differences | Often annual, with gaps |
| Poverty | World Bank WDI | Material deprivation and distributional development | Outcome or predictor | Poverty line definition, survey year interpolation, purchasing-power conversion | Not always annual |
| Trade openness | World Bank WDI | Exposure to international markets | Predictor or control | Goods and services definitions, current-price ratios, small-economy outliers | Yes, with gaps |
| Government expenditure | World Bank WDI; IMF WEO | Public-sector scale and fiscal context | Predictor or control | General government versus central government, functional classification differences | Often annual, with gaps |
| Urbanization | World Bank WDI | Settlement pattern and structural transformation | Predictor or control | National urban definitions differ | Yes, with gaps |
| Internet access | World Bank WDI; OWID for context | Connectivity and information access | Predictor, control, or outcome | User estimates, technology adoption timing, survey/model basis | Yes, with gaps |
| Electricity access | World Bank WDI; OWID for energy context | Infrastructure and basic service access | Outcome, predictor, or control | Access definitions and modeled estimates | Yes, with gaps |

## Education

| Variable family | Likely provider | Conceptual role | Likely analytical use | Unit or comparability concerns | Annual country-level coverage expected |
| --- | --- | --- | --- | --- | --- |
| Adult literacy | UNESCO UIS; World Bank WDI for selected series | Stock of basic human capital | Outcome, predictor, or control | Age thresholds, survey timing, self-reporting or assessment methods | Not always annual |
| Youth literacy | UNESCO UIS | Recent education-system performance | Outcome or predictor | Age bands and assessment/survey comparability | Not always annual |
| Primary enrollment | UNESCO UIS; World Bank WDI for selected series | Access to basic education | Outcome, predictor, or control | Gross versus net enrollment and level definitions | Yes, with gaps |
| Secondary enrollment | UNESCO UIS; World Bank WDI for selected series | Education progression and adolescent access | Outcome, predictor, or control | Gross versus net enrollment and national grade structures | Yes, with gaps |
| Tertiary enrollment | UNESCO UIS; World Bank WDI for selected series | Advanced human-capital formation | Outcome or predictor | Institution classification and age-cohort differences | Yes, with gaps |
| Completion rates | UNESCO UIS | Education-system throughput | Outcome | Level definitions, cohort tracking, late completion | Often annual, with gaps |
| Pupil-teacher ratios | UNESCO UIS; World Bank WDI for selected series | Education-system resourcing | Predictor or control | Teacher definitions and public/private sector inclusion | Yes, with gaps |
| Education expenditure | UNESCO UIS; World Bank WDI | Public investment in education | Predictor or control | Public versus total spending, share of GDP versus share of government spending | Often annual, with gaps |

## Public Health

| Variable family | Likely provider | Conceptual role | Likely analytical use | Unit or comparability concerns | Annual country-level coverage expected |
| --- | --- | --- | --- | --- | --- |
| Life expectancy | WHO GHO; World Bank WDI | Summary population health outcome | Outcome or control | Modeled estimates, sex aggregation, revision vintages | Yes, with gaps |
| Maternal mortality | WHO GHO; World Bank WDI | Maternal health and health-system performance | Outcome | Modeled estimates, live-birth denominator, uncertainty intervals | Often annual or periodic |
| Infant mortality | WHO GHO; World Bank WDI | Early-life health and system performance | Outcome or control | Modeled estimates and denominator conventions | Yes, with gaps |
| Under-five mortality | WHO GHO; World Bank WDI | Child health and survival | Outcome or control | Modeled estimates, uncertainty, reporting quality | Yes, with gaps |
| Vaccination coverage | WHO GHO | Preventive service coverage | Outcome or predictor | Antigen definitions, administrative versus survey estimates | Often annual, with gaps |
| Physician density | WHO GHO; World Bank WDI for selected series | Health workforce capacity | Predictor or control | Cadre definitions and reporting year gaps | Often annual, with gaps |
| Health expenditure | WHO GHO; World Bank WDI | Health-system financing | Predictor or control | Current versus constant units, public/private definitions, GDP share versus per-capita amount | Yes, with gaps |
| Communicable disease burden | WHO GHO; OWID for selected curated series | Infectious disease pressure | Outcome, predictor, or control | Case definitions, surveillance capacity, modeled burden | Varies by disease |
| Noncommunicable disease indicators | WHO GHO | Chronic disease burden and risk | Outcome or predictor | Age standardization, modeled estimates, risk-factor definitions | Varies by indicator |

## Governance

| Variable family | Likely provider | Conceptual role | Likely analytical use | Unit or comparability concerns | Annual country-level coverage expected |
| --- | --- | --- | --- | --- | --- |
| Rule of law | Worldwide Governance Indicators; V-Dem for related institutional measures | Legal predictability and institutional constraint | Predictor or control | Composite perception measures and uncertainty require caveats | Yes, with gaps |
| Government effectiveness | Worldwide Governance Indicators | State capacity and service quality | Predictor or control | Perception/source aggregation and confidence intervals | Yes, with gaps |
| Regulatory quality | Worldwide Governance Indicators | Policy and market-governance environment | Predictor or control | Composite construction and interpretation limits | Yes, with gaps |
| Political stability | Worldwide Governance Indicators | Political risk and institutional disruption | Predictor or control | Perception-based source aggregation | Yes, with gaps |
| Voice and accountability | Worldwide Governance Indicators; V-Dem for related concepts | Political participation and accountability | Predictor or control | Scale interpretation and concept overlap with democracy indicators | Yes, with gaps |
| Control of corruption | Worldwide Governance Indicators; Transparency International CPI | Corruption perception and institutional integrity | Predictor or control | Perception-based measures must not be treated as observed corruption incidence | Yes, with gaps |
| Electoral democracy | V-Dem | Democratic institutional quality | Predictor, control, or outcome | Expert-coded index, uncertainty, versioning, and concept selection | Yes, with gaps |
| Civil liberties | V-Dem | Rights environment and political freedom | Predictor, control, or outcome | Expert coding and overlapping subdimensions | Yes, with gaps |
| Judicial independence | V-Dem | Institutional constraint and rule-of-law component | Predictor or control | Expert-coded concepts and scale interpretation | Yes, with gaps |
| Media freedom | V-Dem | Information environment and accountability | Predictor or control | Expert coding, country context, and conceptual overlap with civil liberties | Yes, with gaps |

## Human Development and Environment

| Variable family | Likely provider | Conceptual role | Likely analytical use | Unit or comparability concerns | Annual country-level coverage expected |
| --- | --- | --- | --- | --- | --- |
| Human Development Index | UNDP HDI | Composite human development summary | Outcome, predictor, or descriptive context | Composite weighting, component changes, and release versioning | Yes, with gaps |
| Education index | UNDP HDI; UNESCO UIS components | Education component of human development | Outcome, predictor, or control | Composite construction and source component definitions | Yes, with gaps |
| Income index | UNDP HDI; World Bank WDI for income components | Income component of human development | Outcome, predictor, or control | Purchasing-power conversion and index normalization | Yes, with gaps |
| Life expectancy index | UNDP HDI; WHO GHO for source health context | Health component of human development | Outcome, predictor, or control | Index construction and underlying life-expectancy revisions | Yes, with gaps |
| Carbon emissions | OWID; World Bank WDI for selected series | Environmental pressure and energy-system outcome | Outcome, predictor, or control | Territorial versus consumption accounting, per-capita versus total units | Yes, with gaps |
| Energy consumption | OWID | Energy-system scale and development context | Predictor, control, or outcome | Primary versus final energy and unit conversions | Yes, with gaps |
| Renewable-energy share | OWID; World Bank WDI for selected series | Energy transition and environmental context | Outcome or predictor | Electricity versus total energy share and denominator differences | Yes, with gaps |
| Population | World Bank WDI; UNDP or OWID for context | Scale denominator and demographic context | Control or denominator | De facto versus de jure population and revision vintages | Yes, with gaps |
| Demographic structure | World Bank WDI; OWID for curated context | Age composition and dependency structure | Predictor or control | Age-bin definitions and projection versus estimate status | Yes, with gaps |

## Review Rules

Before a variable family is promoted into a reviewed subset, Polaris should confirm source definitions, units, country identifiers, year identifiers, missingness, comparability warnings, and provenance fields. Variables with unclear units, opaque transformations, or unstable identifiers should remain excluded even if they are available in a downloaded file.

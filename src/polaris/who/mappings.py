"""Reviewed canonical WHO variable mappings."""

from __future__ import annotations

from polaris.who.dimensions import both_sexes_rule, exact_dimension_rule, total_residence_rule
from polaris.who.errors import WHOMappingError
from polaris.who.models import WHOIntegrationStatus, WHOVariableMapping


def _m(
    who_indicator_id: str,
    canonical_variable_id: str,
    canonical_label: str,
    definition: str,
    unit: str,
    *,
    filters=(),
    modeled: bool = False,
    projections: bool = False,
    years: tuple[int, int] | None = None,
    notes: tuple[str, ...] = (),
) -> WHOVariableMapping:
    return WHOVariableMapping(
        who_indicator_id=who_indicator_id,
        canonical_variable_id=canonical_variable_id,
        canonical_label=canonical_label,
        conceptual_definition=definition,
        unit=unit,
        required_dimension_filters=tuple(filters),
        modeled_estimates_accepted=modeled,
        projections_accepted=projections,
        supported_year_range=years,
        integration_status=WHOIntegrationStatus.INTEGRATED,
        notes=notes,
    )


REVIEWED_WHO_VARIABLE_MAPPINGS: tuple[WHOVariableMapping, ...] = (
    _m(
        "WHOSIS_000001",
        "who_life_expectancy_birth_years",
        "WHO life expectancy at birth, both sexes",
        "Life expectancy at birth in years, explicit WHO both-sexes category.",
        "years",
        filters=(both_sexes_rule(),),
        modeled=True,
        years=(2000, 2021),
    ),
    _m(
        "WHOSIS_000002",
        "who_hale_birth_years",
        "WHO healthy life expectancy at birth, both sexes",
        "Healthy life expectancy at birth in years, explicit WHO both-sexes category.",
        "years",
        filters=(both_sexes_rule(),),
        modeled=True,
        years=(2000, 2021),
    ),
    _m(
        "WHOSIS_000004",
        "who_adult_mortality_per_1000",
        "WHO adult mortality rate, both sexes",
        "Probability of dying between ages 15 and 60 per 1,000 population, both sexes.",
        "per 1,000 population",
        filters=(both_sexes_rule(),),
        modeled=True,
        years=(2000, 2021),
    ),
    _m(
        "MDG_0000000026",
        "who_maternal_mortality_per_100k",
        "WHO maternal mortality ratio",
        "Maternal mortality ratio per 100,000 live births.",
        "per 100,000 live births",
        modeled=True,
        years=(1985, 2023),
    ),
    _m(
        "MH_12",
        "who_suicide_rate_per_100k",
        "WHO age-standardized suicide rate, both sexes",
        "Age-standardized suicide mortality rate per 100,000 population, both sexes.",
        "per 100,000 population",
        filters=(both_sexes_rule(),),
        modeled=True,
        years=(2000, 2021),
    ),
    _m(
        "GHED_CHEGDP_SHA2011",
        "who_health_expenditure_pct_gdp",
        "WHO current health expenditure as percent of GDP",
        "Current health expenditure as a percentage of gross domestic product.",
        "percent of GDP",
        years=(2000, 2023),
    ),
    _m(
        "HWF_0001",
        "who_medical_doctors_per_10000",
        "WHO medical doctors per 10,000 population",
        "Medical doctors density per 10,000 population.",
        "per 10,000 population",
        years=(1990, 2024),
    ),
    _m(
        "HWF_0006",
        "who_nursing_midwifery_per_10000",
        "WHO nursing and midwifery personnel per 10,000 population",
        "Nursing and midwifery personnel density per 10,000 population.",
        "per 10,000 population",
        years=(1990, 2024),
    ),
    _m(
        "WHS6_102",
        "who_hospital_beds_per_10000",
        "WHO hospital beds per 10,000 population",
        "Hospital beds per 10,000 population.",
        "per 10,000 population",
        years=(2000, 2023),
    ),
    _m(
        "WHS4_100",
        "who_dtp3_immunization_pct",
        "WHO DTP3 immunization coverage among 1-year-olds",
        "DTP3 immunization coverage among 1-year-olds.",
        "percent",
        years=(2000, 2025),
    ),
    _m(
        "WHS8_110",
        "who_mcv1_immunization_pct",
        "WHO MCV1 immunization coverage among 1-year-olds",
        "Measles-containing-vaccine first-dose coverage among 1-year-olds.",
        "percent",
        years=(2000, 2025),
    ),
    _m(
        "MDG_0000000020",
        "who_tuberculosis_incidence_per_100k",
        "WHO tuberculosis incidence",
        "Incidence of tuberculosis per 100,000 population per year.",
        "per 100,000 population per year",
        modeled=True,
        years=(2000, 2024),
    ),
    _m(
        "MDG_0000000025",
        "who_skilled_birth_attendance_pct",
        "WHO births attended by skilled health personnel",
        "Births attended by skilled health personnel.",
        "percent",
        years=(2000, 2025),
    ),
    _m(
        "MDG_0000000007",
        "who_under5_mortality_per_1000_live_births",
        "WHO under-five mortality rate",
        (
            "Probability of dying by age 5 per 1,000 live births, both sexes and "
            "total wealth quintile."
        ),
        "per 1,000 live births",
        filters=(
            both_sexes_rule("Dim1"),
            exact_dimension_rule(
                "Dim2",
                "AGEGROUP_YEARSUNDER5",
                "Under-five mortality is inherently a child-age headline concept.",
            ),
            exact_dimension_rule(
                "Dim3",
                "WEALTHQUINTILE_TOTL",
                "Provider supplies total wealth quintile; wealth groups are not averaged.",
            ),
        ),
        modeled=True,
        years=(1931, 2024),
    ),
    _m(
        "WHOSIS_000003",
        "who_neonatal_mortality_per_1000_live_births",
        "WHO neonatal mortality rate",
        "Neonatal mortality rate per 1,000 live births, both sexes, days 0-27.",
        "per 1,000 live births",
        filters=(
            both_sexes_rule("Dim1"),
            exact_dimension_rule(
                "Dim2",
                "AGEGROUP_DAYS0-27",
                "Neonatal mortality is inherently a days 0-27 child-age concept.",
            ),
        ),
        modeled=True,
        years=(1951, 2024),
    ),
    _m(
        "GHED_CHE_pc_US_SHA2011",
        "who_health_expenditure_per_capita_usd",
        "WHO current health expenditure per capita in US dollars",
        "Current health expenditure per capita in current US dollars.",
        "current US dollars per capita",
        years=(2000, 2023),
        notes=("No price or exchange-rate conversion is applied.",),
    ),
    _m(
        "UHC_INDEX_REPORTED",
        "who_uhc_service_coverage_index",
        "WHO UHC service coverage index",
        "Reported SDG 3.8.1 UHC Service Coverage Index.",
        "index",
        modeled=True,
        years=(2000, 2023),
    ),
    _m(
        "NUTSTUNTINGPREV",
        "who_child_stunting_pct",
        "WHO child stunting prevalence",
        "Model-based prevalence of stunting among children under 5, both sexes.",
        "percent",
        filters=(both_sexes_rule(),),
        modeled=True,
        years=(1990, 2024),
    ),
    _m(
        "NUTOVERWEIGHTPREV",
        "who_child_overweight_pct",
        "WHO child overweight prevalence",
        "Model-based prevalence of overweight among children under 5, both sexes.",
        "percent",
        filters=(both_sexes_rule(),),
        modeled=True,
        years=(1990, 2024),
    ),
    _m(
        "NCDMORT3070",
        "who_premature_ncd_mortality_pct",
        "WHO premature NCD mortality probability",
        "Probability of dying between age 30 and 70 from selected NCD causes, both sexes.",
        "percent",
        filters=(
            both_sexes_rule("Dim1"),
            exact_dimension_rule(
                "Dim2",
                "AGEGROUP_YEARS30-69",
                "The indicator definition is inherently ages 30-69.",
            ),
        ),
        modeled=True,
        years=(2000, 2021),
    ),
    _m(
        "NCD_BMI_30A",
        "who_adult_obesity_pct",
        "WHO adult obesity prevalence",
        "Age-standardized adult obesity prevalence, ages 18+, both sexes.",
        "percent",
        filters=(
            both_sexes_rule("Dim1"),
            exact_dimension_rule(
                "Dim2",
                "AGEGROUP_YEARS18-PLUS",
                "Adult obesity indicator is defined for ages 18+.",
            ),
        ),
        modeled=True,
        years=(1980, 2024),
    ),
    _m(
        "NCD_PAA",
        "who_insufficient_physical_activity_pct",
        "WHO insufficient physical activity prevalence",
        (
            "Age-standardized prevalence of insufficient physical activity among adults 18+, "
            "both sexes."
        ),
        "percent",
        filters=(
            both_sexes_rule("Dim1"),
            exact_dimension_rule(
                "Dim2",
                "AGEGROUP_YEARS18-PLUS",
                "Adult physical-activity indicator is defined for ages 18+.",
            ),
        ),
        modeled=True,
        years=(2000, 2022),
    ),
    _m(
        "SA_0000001688",
        "who_alcohol_consumption_litres_per_capita",
        "WHO alcohol consumption per capita",
        "Total per capita alcohol consumption for age 15+ in litres of pure alcohol, both sexes.",
        "litres pure alcohol per capita",
        filters=(both_sexes_rule("Dim1"),),
        modeled=True,
        years=(2000, 2024),
        notes=("WHO defines this as a three-year average.",),
    ),
    _m(
        "SDGHEPHBSAGPRV",
        "who_hepatitis_b_under5_pct",
        "WHO hepatitis B surface antigen prevalence under age 5",
        "HBsAg prevalence among children under 5.",
        "percent",
        filters=(
            exact_dimension_rule(
                "Dim1",
                "AGEGROUP_YEARSUNDER5",
                "The SDG hepatitis B indicator targets children under 5.",
            ),
            exact_dimension_rule(
                "DataSourceDim",
                "DATASOURCE_GLOBAL_HEPA_REPORT_2026",
                "Single observed data-source category retained explicitly.",
            ),
        ),
        modeled=True,
        years=(2015, 2024),
    ),
    _m(
        "WSH_WATER_SAFELY_MANAGED",
        "who_safely_managed_water_pct",
        "WHO safely managed drinking-water services",
        "Population using safely managed drinking-water services, total residence.",
        "percent",
        filters=(total_residence_rule(),),
        modeled=True,
        years=(2000, 2024),
    ),
    _m(
        "WSH_SANITATION_SAFELY_MANAGED",
        "who_safely_managed_sanitation_pct",
        "WHO safely managed sanitation services",
        "Population using safely managed sanitation services, total residence.",
        "percent",
        filters=(total_residence_rule(),),
        modeled=True,
        years=(2000, 2024),
    ),
    _m(
        "SDGPM25",
        "who_pm25_exposure",
        "WHO PM2.5 exposure",
        "Concentration of fine particulate matter, total residence.",
        "micrograms per cubic metre",
        filters=(total_residence_rule(),),
        modeled=True,
        years=(2010, 2023),
    ),
    _m(
        "RS_198",
        "who_road_traffic_mortality_per_100k",
        "WHO road traffic mortality rate",
        "Estimated road traffic death rate per 100,000 population.",
        "per 100,000 population",
        modeled=True,
        years=(2021, 2021),
    ),
)


def who_mapping_registry() -> tuple[WHOVariableMapping, ...]:
    """Return reviewed WHO mappings in stable canonical variable order."""

    return tuple(
        sorted(
            REVIEWED_WHO_VARIABLE_MAPPINGS,
            key=lambda item: item.canonical_variable_id,
        )
    )


def mapping_for_indicator(indicator_id: str) -> WHOVariableMapping:
    for mapping in REVIEWED_WHO_VARIABLE_MAPPINGS:
        if mapping.who_indicator_id == indicator_id:
            return mapping
    raise WHOMappingError(f"no reviewed WHO variable mapping for {indicator_id}")


def mappings_for_indicators(indicator_ids: tuple[str, ...]) -> tuple[WHOVariableMapping, ...]:
    found = {mapping.who_indicator_id: mapping for mapping in REVIEWED_WHO_VARIABLE_MAPPINGS}
    missing = tuple(indicator for indicator in indicator_ids if indicator not in found)
    if missing:
        raise WHOMappingError(f"missing reviewed WHO mappings: {', '.join(missing)}")
    return tuple(found[indicator] for indicator in indicator_ids)

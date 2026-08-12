"""Reviewed canonical UNESCO UIS education variable mappings."""

from __future__ import annotations

from polaris.unesco.errors import UNESCOEducationMappingError
from polaris.unesco.models import UNESCOEducationVariableMapping


def _m(
    indicator_id: str,
    canonical_id: str,
    label: str,
    unit: str,
    *,
    level: str | None = None,
    age: str | None = None,
    modeled: bool = False,
    notes: tuple[str, ...] = (),
) -> UNESCOEducationVariableMapping:
    return UNESCOEducationVariableMapping(
        unesco_indicator_id=indicator_id,
        official_title=label,
        canonical_variable_id=canonical_id,
        canonical_label=f"UNESCO {label}",
        definition=label,
        unit=unit,
        allowed_education_level=level,
        allowed_age_group=age,
        modeled_estimates_accepted=modeled,
        notes=(
            "Definition is preserved from the downloaded UNESCO label file; no separate "
            "indicator definition file was present locally.",
            *notes,
        ),
    )


REVIEWED_UNESCO_VARIABLE_MAPPINGS: tuple[UNESCOEducationVariableMapping, ...] = (
    _m(
        "LR.AG15T99",
        "uis_adult_literacy_rate",
        "Adult literacy rate, population 15+ years, both sexes (%)",
        "percent",
        age="15+ years",
    ),
    _m(
        "LR.AG15T24",
        "uis_youth_literacy_rate",
        "Youth literacy rate, population 15-24 years, both sexes (%)",
        "percent",
        age="15-24 years",
    ),
    _m(
        "CR.1",
        "uis_primary_completion_rate",
        "Completion rate, primary education, both sexes (%)",
        "percent",
        level="primary",
    ),
    _m(
        "CR.2",
        "uis_lower_secondary_completion_rate",
        "Completion rate, lower secondary education, both sexes (%)",
        "percent",
        level="lower secondary",
    ),
    _m(
        "CR.3",
        "uis_upper_secondary_completion_rate",
        "Completion rate, upper secondary education, both sexes (%)",
        "percent",
        level="upper secondary",
    ),
    _m(
        "GER.5T8",
        "uis_tertiary_gross_enrolment_ratio",
        "Gross enrolment ratio for tertiary education, both sexes (%)",
        "percent",
        level="tertiary",
    ),
    _m(
        "NER.02.CP",
        "uis_pre_primary_net_enrolment_rate",
        "Net enrolment rate, pre-primary, both sexes (%)",
        "percent",
        level="pre-primary",
    ),
    _m(
        "ROFST.1.CP",
        "uis_out_of_school_rate_primary_age",
        "Out-of-school rate for children of primary school age, both sexes (%)",
        "percent",
        age="primary school age",
        level="primary",
    ),
    _m(
        "ROFST.2.CP",
        "uis_out_of_school_rate_lower_secondary_age",
        "Out-of-school rate for adolescents of lower secondary school age, both sexes (%)",
        "percent",
        age="lower secondary school age",
        level="lower secondary",
    ),
    _m(
        "EA.2T8.AG25T99",
        "uis_lower_secondary_attainment_rate_25plus",
        (
            "Educational attainment rate, completed lower secondary education or higher, "
            "population 25+ years, both sexes (%)"
        ),
        "percent",
        age="25+ years",
        level="lower secondary",
    ),
    _m(
        "EA.3T8.AG25T99",
        "uis_upper_secondary_attainment_rate_25plus",
        (
            "Educational attainment rate, completed upper secondary education or higher, "
            "population 25+ years, both sexes (%)"
        ),
        "percent",
        age="25+ years",
        level="upper secondary",
    ),
    _m(
        "PTRHC.1.QUALIFIED",
        "uis_pupil_qualified_teacher_ratio_primary",
        "Pupil-qualified teacher ratio in primary education (headcount basis)",
        "ratio",
        level="primary",
    ),
    _m(
        "PTRHC.1.TRAINED",
        "uis_pupil_trained_teacher_ratio_primary",
        "Pupil-trained teacher ratio in primary education (headcount basis)",
        "ratio",
        level="primary",
    ),
    _m(
        "XGDP.FSGOV",
        "uis_education_expenditure_pct_gdp",
        "Government expenditure on education as a percentage of GDP (%)",
        "percent",
    ),
    _m(
        "XGOVEXP.IMF",
        "uis_education_expenditure_pct_government_expenditure",
        (
            "Expenditure on education as a percentage of total government expenditure (%) "
            "(UIS calculation)"
        ),
        "percent",
    ),
)


def unesco_mapping_registry() -> tuple[UNESCOEducationVariableMapping, ...]:
    return REVIEWED_UNESCO_VARIABLE_MAPPINGS


def mappings_for_indicators(
    indicator_ids: tuple[str, ...],
) -> tuple[UNESCOEducationVariableMapping, ...]:
    by_id = {mapping.unesco_indicator_id: mapping for mapping in REVIEWED_UNESCO_VARIABLE_MAPPINGS}
    missing = [indicator_id for indicator_id in indicator_ids if indicator_id not in by_id]
    if missing:
        raise UNESCOEducationMappingError(
            f"Unknown reviewed UNESCO mapping(s): {', '.join(missing)}"
        )
    return tuple(by_id[indicator_id] for indicator_id in indicator_ids)

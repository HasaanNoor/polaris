import pytest

from polaris.unesco.dimensions import (
    age_dimension,
    education_level_dimension,
    is_headline_both_sexes,
    location_dimension,
    sex_dimension,
    unit_from_label,
)
from polaris.unesco.errors import UNESCOEducationMappingError
from polaris.unesco.mappings import mappings_for_indicators, unesco_mapping_registry


def test_explicit_mappings_and_ruleset():
    registry = unesco_mapping_registry()
    by_id = {mapping.unesco_indicator_id: mapping for mapping in registry}
    assert by_id["LR.AG15T99"].canonical_variable_id == "uis_adult_literacy_rate"
    assert by_id["CR.2"].allowed_education_level == "lower secondary"
    assert by_id["LR.AG15T24"].allowed_age_group == "15-24 years"
    assert by_id["XGDP.FSGOV"].unit == "percent"
    assert by_id["LR.AG15T99"].ruleset_version == "2026-08-12"


def test_unknown_mapping_is_not_guessed():
    with pytest.raises(UNESCOEducationMappingError):
        mappings_for_indicators(("MADE.UP",))


def test_dimension_helpers_do_not_average_or_aggregate():
    assert (
        sex_dimension("LR.AG15T99.F", "Adult literacy rate, population 15+ years, female (%)")
        == "female"
    )
    assert (
        sex_dimension("LR.AG15T99", "Adult literacy rate, population 15+ years, both sexes (%)")
        == "both sexes"
    )
    assert (
        age_dimension("LR.AG15T24", "Youth literacy rate, population 15-24 years, both sexes (%)")
        == "15-24 years"
    )
    assert (
        education_level_dimension("CR.1", "Completion rate, primary education, both sexes (%)")
        == "primary"
    )
    assert (
        education_level_dimension(
            "CR.2", "Completion rate, lower secondary education, both sexes (%)"
        )
        == "lower secondary"
    )
    assert (
        location_dimension("CR.1.RUR", "Completion rate, primary education, rural, both sexes (%)")
        == "rural"
    )
    assert (
        unit_from_label("Gross enrolment ratio for tertiary education, both sexes (%)") == "percent"
    )
    assert is_headline_both_sexes("CR.1", "Completion rate, primary education, both sexes (%)")
    assert not is_headline_both_sexes("CR.1.F", "Completion rate, primary education, female (%)")
    assert not is_headline_both_sexes(
        "CR.1.RUR", "Completion rate, primary education, rural, both sexes (%)"
    )

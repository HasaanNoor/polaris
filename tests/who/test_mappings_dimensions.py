from polaris.who.dimensions import both_sexes_rule, is_projected_row, row_matches_mapping
from polaris.who.errors import WHOMappingError
from polaris.who.mappings import mapping_for_indicator, who_mapping_registry


def test_explicit_mapping_and_ruleset_version() -> None:
    mapping = mapping_for_indicator("WHOSIS_000001")

    assert mapping.canonical_variable_id == "who_life_expectancy_birth_years"
    assert mapping.unit == "years"
    assert mapping.ruleset_version == "2026-08-10"
    assert mapping.allowed_dimension_values == {"Dim1": ("SEX_BTSX",)}


def test_missing_mapping_is_not_guessed() -> None:
    try:
        mapping_for_indicator("UNKNOWN_WHO")
    except WHOMappingError as exc:
        assert "no reviewed WHO variable mapping" in str(exc)
    else:
        raise AssertionError("missing mapping should fail")


def test_both_sexes_filter_excludes_sex_specific_rows() -> None:
    mapping = mapping_for_indicator("WHOSIS_000001")
    base = {
        "SpatialDimType": "COUNTRY",
        "SpatialDim": "PAK",
        "TimeDim": 2020,
        "NumericValue": 65.0,
    }

    assert row_matches_mapping({**base, "Dim1": "SEX_BTSX"}, mapping) is True
    assert row_matches_mapping({**base, "Dim1": "SEX_MLE"}, mapping) is False


def test_age_specific_headline_filter_is_deterministic() -> None:
    mapping = mapping_for_indicator("NCD_BMI_30A")
    row = {
        "SpatialDimType": "COUNTRY",
        "SpatialDim": "NPL",
        "TimeDim": 2020,
        "NumericValue": 6.2,
        "Dim1": "SEX_BTSX",
        "Dim2": "AGEGROUP_YEARS18-PLUS",
    }

    assert row_matches_mapping(row, mapping) is True
    assert row_matches_mapping({**row, "Dim2": "AGEGROUP_YEARS30-PLUS"}, mapping) is False


def test_projection_exclusion_rule_is_explicit() -> None:
    mapping = mapping_for_indicator("WHOSIS_000001")

    assert is_projected_row({"TimeDim": 2030}, mapping.who_indicator_id) is False


def test_registry_contains_no_low_default_tobacco_mapping() -> None:
    indicators = {mapping.who_indicator_id for mapping in who_mapping_registry()}

    assert "M_Est_tob_curr_std" not in indicators
    assert both_sexes_rule().allowed_values == ("SEX_BTSX",)

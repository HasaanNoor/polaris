from polaris.harmonization.countries import normalize_country_identifier
from polaris.harmonization.models import GeographicEntityType


def test_country_normalization_exact_iso3_iso2_and_name() -> None:
    assert normalize_country_identifier("PAK").canonical_code == "PAK"
    assert normalize_country_identifier("PK").canonical_code == "PAK"
    assert normalize_country_identifier("Pakistan").canonical_code == "PAK"


def test_country_normalization_classifies_aggregates_and_territories() -> None:
    assert normalize_country_identifier("WLD").entity_type is GeographicEntityType.GLOBAL_AGGREGATE
    assert normalize_country_identifier("AFE").entity_type is GeographicEntityType.REGION
    assert normalize_country_identifier("HIC").entity_type is GeographicEntityType.INCOME_GROUP
    assert normalize_country_identifier("ABW").entity_type is GeographicEntityType.TERRITORY


def test_country_normalization_does_not_fuzzy_match() -> None:
    result = normalize_country_identifier("Pak")

    assert result.canonical_code is None
    assert result.entity_type is GeographicEntityType.UNKNOWN

from pathlib import Path

import pytest

from polaris.who.catalog import load_who_acquisition_catalog, target_by_indicator
from polaris.who.errors import WHOCatalogError
from polaris.who.profiling import profile_who_indicator

CATALOG = Path("data/raw/who/gho/acquisition_catalog.json")


def test_catalog_loading_preserves_suitability_and_checksum() -> None:
    catalog = load_who_acquisition_catalog(CATALOG)
    target = target_by_indicator(catalog, "WHOSIS_000001")

    assert target["integration_suitability"] == "HIGH"
    assert len(target["sha256"]) == 64
    assert target["local_snapshot_path"].endswith("WHOSIS_000001.json")


def test_missing_indicator_raises_catalog_error() -> None:
    catalog = load_who_acquisition_catalog(CATALOG)

    with pytest.raises(WHOCatalogError):
        target_by_indicator(catalog, "NOT_A_WHO_INDICATOR")


def test_profile_discovers_core_schema_patterns() -> None:
    catalog = load_who_acquisition_catalog(CATALOG)
    profile = profile_who_indicator(target=target_by_indicator(catalog, "WHOSIS_000001"))

    assert profile.geographic_field == "SpatialDim"
    assert profile.temporal_field == "TimeDim"
    assert "NumericValue" in profile.numeric_value_fields
    assert "SEX_BTSX" in profile.sex_dimensions
    assert profile.aggregate_count > 0
    assert profile.country_count > 100
    assert profile.year_range == (2000, 2021)
    assert profile.checksum_validated is True


def test_profile_detects_age_and_estimate_dimensions() -> None:
    catalog = load_who_acquisition_catalog(CATALOG)
    age_profile = profile_who_indicator(target=target_by_indicator(catalog, "NCD_BMI_30A"))
    source_profile = profile_who_indicator(target=target_by_indicator(catalog, "SDGHEPHBSAGPRV"))

    assert "AGEGROUP_YEARS18-PLUS" in age_profile.age_dimensions
    assert "DATASOURCE_GLOBAL_HEPA_REPORT_2026" in source_profile.estimate_status_dimensions

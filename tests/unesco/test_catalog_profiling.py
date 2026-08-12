from pathlib import Path

from polaris.unesco.catalog import load_indicator_labels, source_checksums
from polaris.unesco.profiling import profile_all_downloaded_datasets, profile_unesco_indicator

RAW_ROOT = Path("data/raw/unesco")


def test_source_loading_and_checksum_tracking():
    labels = load_indicator_labels(raw_root=RAW_ROOT)
    checksums = source_checksums(raw_root=RAW_ROOT)
    assert "SDG" in labels
    assert labels["SDG"]["LR.AG15T99"].startswith("Adult literacy rate")
    assert "SDG:data" in checksums
    assert len(checksums["SDG:data"]) == 64


def test_dataset_distinctions_are_profiled():
    profiles = profile_all_downloaded_datasets(raw_root=RAW_ROOT)
    assert profiles["DEM"]["indicator_count"] == 35
    assert profiles["SDG"]["indicator_count"] > 1000
    assert profiles["SCN-SDG"]["indicator_count"] == 2
    assert profiles["SDG11"]["indicator_count"] == 8


def test_indicator_profile_preserves_schema_and_dimensions():
    profile = profile_unesco_indicator(
        raw_root=RAW_ROOT,
        dataset="SDG",
        indicator_id="LR.AG15T24",
    )
    assert profile.country_field == "COUNTRY_ID"
    assert profile.year_field == "YEAR"
    assert profile.numeric_value_field == "VALUE"
    assert profile.unit == "percent"
    assert profile.sex_dimension == "both sexes"
    assert profile.age_dimension == "15-24 years"
    assert profile.country_coverage > 50


def test_unknown_indicator_profile_is_low_and_empty():
    profile = profile_unesco_indicator(raw_root=RAW_ROOT, dataset="SDG", indicator_id="UNKNOWN")
    assert profile.unesco_indicator_id == "UNKNOWN"
    assert profile.row_count == 0
    assert profile.schema_findings

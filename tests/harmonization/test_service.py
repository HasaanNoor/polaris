import pytest

from polaris.harmonization import JoinType, ProviderPrecedenceRule, harmonize_datasets
from polaris.harmonization.errors import HarmonizationCompatibilityError
from polaris.harmonization.models import (
    DuplicateKeyBehavior,
    HarmonizationFindingCode,
    HarmonizationStrictness,
    MissingnessReasonCode,
)
from tests.harmonization.helpers import request_for, wdi_result, who_result


def test_left_join_excludes_aggregates_and_tracks_join_missingness(tmp_path) -> None:
    harmonized = harmonize_datasets(request=request_for(wdi_result(tmp_path), who_result(tmp_path)))

    assert [record.canonical_country_code for record in harmonized.records] == ["IND", "PAK"]
    assert harmonized.records[0].values["wdi_gdp_per_capita_current_usd"] == 1900.0
    assert harmonized.records[1].values["who_life_expectancy_at_birth_both_sexes"] == 66.1
    assert harmonized.quality_summary.aggregate_entities_excluded == 1
    assert all(record.canonical_country_code != "WLD" for record in harmonized.records)


def test_inner_and_full_outer_join_semantics(tmp_path) -> None:
    wdi = wdi_result(tmp_path)
    who = who_result(tmp_path)

    inner = harmonize_datasets(request=request_for(wdi, who, join_type=JoinType.INNER))
    outer = harmonize_datasets(request=request_for(wdi, who, join_type=JoinType.FULL_OUTER))

    assert {(record.canonical_country_code, record.year) for record in inner.records} == {
        ("IND", 2020),
        ("PAK", 2020),
    }
    assert ("PAK", 2021) in {
        (record.canonical_country_code, record.year) for record in outer.records
    }
    pakistan_2021 = next(
        record
        for record in outer.records
        if record.canonical_country_code == "PAK" and record.year == 2021
    )
    assert (
        pakistan_2021.missingness["wdi_gdp_per_capita_current_usd"]
        is MissingnessReasonCode.JOIN_INDUCED_MISSING
    )


def test_duplicate_keys_rejected_by_default(tmp_path) -> None:
    who = who_result(
        tmp_path,
        rows=[
            [
                "SpatialDimValueCode",
                "Location",
                "Period",
                "IndicatorCode",
                "Dim1ValueCode",
                "FactValueNumeric",
            ],
            ["PAK", "Pakistan", "2020", "WHOSIS_000001", "SEX_BTSX", "66.1"],
            ["PAK", "Pakistan", "2020", "WHOSIS_000001", "SEX_BTSX", "66.2"],
        ],
    )

    with pytest.raises(HarmonizationCompatibilityError):
        harmonize_datasets(request=request_for(wdi_result(tmp_path), who))


def test_duplicate_keys_can_be_preserved_as_unresolved(tmp_path) -> None:
    who = who_result(
        tmp_path,
        rows=[
            [
                "SpatialDimValueCode",
                "Location",
                "Period",
                "IndicatorCode",
                "Dim1ValueCode",
                "FactValueNumeric",
            ],
            ["PAK", "Pakistan", "2020", "WHOSIS_000001", "SEX_BTSX", "66.1"],
            ["PAK", "Pakistan", "2020", "WHOSIS_000001", "SEX_BTSX", "66.2"],
        ],
    )
    request = request_for(wdi_result(tmp_path), who).model_copy(
        update={
            "strictness": HarmonizationStrictness(
                duplicate_key_behavior=DuplicateKeyBehavior.PRESERVE_CONFLICT
            )
        }
    )

    harmonized = harmonize_datasets(request=request)

    pakistan = next(
        record for record in harmonized.records if record.canonical_country_code == "PAK"
    )
    assert (
        pakistan.missingness["who_life_expectancy_at_birth_both_sexes"]
        is MissingnessReasonCode.UNRESOLVED_DUPLICATE
    )
    assert HarmonizationFindingCode.DUPLICATE_COUNTRY_YEAR in {
        finding.code for finding in harmonized.findings
    }


def test_conflicting_provider_mapping_requires_precedence(tmp_path) -> None:
    request = request_for(wdi_result(tmp_path), who_result(tmp_path))
    second = request.variable_mappings[1].model_copy(
        update={"canonical_variable_id": "wdi_gdp_per_capita_current_usd"}
    )
    bad_request = request.model_copy(
        update={"variable_mappings": (request.variable_mappings[0], second)}
    )

    with pytest.raises(HarmonizationCompatibilityError):
        harmonize_datasets(request=bad_request)

    good_request = bad_request.model_copy(
        update={
            "provider_precedence": (
                ProviderPrecedenceRule(
                    canonical_variable_id="wdi_gdp_per_capita_current_usd",
                    provider_order=("world_bank", "who"),
                ),
            )
        }
    )
    harmonized = harmonize_datasets(request=good_request)

    assert HarmonizationFindingCode.PROVIDER_PRECEDENCE_APPLIED in {
        finding.code for finding in harmonized.findings
    }


def test_value_level_provenance_preserves_source_receipt(tmp_path) -> None:
    harmonized = harmonize_datasets(request=request_for(wdi_result(tmp_path), who_result(tmp_path)))
    pakistan = next(
        record for record in harmonized.records if record.canonical_country_code == "PAK"
    )
    provenance = pakistan.value_provenance["who_life_expectancy_at_birth_both_sexes"]

    assert provenance.source_dataset_id == "who"
    assert provenance.source_variable_id == "fact_value_numeric"
    assert provenance.source_field_name == "FactValueNumeric"
    assert provenance.original_geographic_identifier == "PAK"
    assert provenance.original_year_value == "2020"
    assert provenance.normalized_value == 66.1
    assert len(provenance.source_checksum) == 64

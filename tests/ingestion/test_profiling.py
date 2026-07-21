from pathlib import Path

from polaris.ingestion import IngestionConfiguration, load_tabular_file
from polaris.ingestion.normalization import normalize_rows
from polaris.ingestion.profiling import build_quality_profile
from polaris.ingestion.validation import map_manifest_columns
from polaris.schemas.common import DataType, VariableRole
from tests.ingestion.helpers import manifest_with_variables, variable, write_csv


def test_profile_counts_ranges_types_and_duplicates(tmp_path: Path) -> None:
    manifest = manifest_with_variables(
        [
            variable("id", DataType.STRING, role=VariableRole.IDENTIFIER),
            variable("amount", DataType.FLOAT, missing=["null"]),
        ]
    )
    loaded = load_tabular_file(
        write_csv(
            tmp_path / "data.csv",
            [["id", "amount"], ["A", "1.5"], ["A", "null"], ["B", "3.0"], ["C", "bad"]],
        ),
        IngestionConfiguration(),
    )
    mappings, _, _, structural_findings = map_manifest_columns(
        manifest, loaded, IngestionConfiguration()
    )
    records, normalization_findings = normalize_rows(
        manifest, loaded, mappings, IngestionConfiguration()
    )

    profile = build_quality_profile(
        manifest,
        mappings,
        records,
        structural_findings + normalization_findings,
        source_row_count=4,
        rejected_row_count=1,
    )

    amount = profile.variables[1]
    assert profile.accepted_row_count == 3
    assert profile.rejected_row_count == 1
    assert profile.duplicate_record_count == 1
    assert amount.non_null_count == 2
    assert amount.null_count == 1
    assert amount.invalid_value_count == 1
    assert amount.unique_value_count == 2
    assert amount.minimum == 1.5
    assert amount.maximum == 3.0
    assert amount.observed_types == ("float",)


def test_empty_column_profile(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("amount", DataType.FLOAT)])
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["amount"], ["null"], [" "]]),
        IngestionConfiguration(),
    )
    mappings, _, _, findings = map_manifest_columns(manifest, loaded, IngestionConfiguration())
    records, row_findings = normalize_rows(manifest, loaded, mappings, IngestionConfiguration())

    profile = build_quality_profile(
        manifest,
        mappings,
        records,
        findings + row_findings,
        source_row_count=2,
        rejected_row_count=0,
    )

    assert profile.variables[0].non_null_count == 0
    assert profile.variables[0].null_count == 2
    assert profile.variables[0].minimum is None
    assert profile.variables[0].observed_types == ()

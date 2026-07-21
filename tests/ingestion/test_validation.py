from pathlib import Path

from polaris.ingestion import IngestionConfiguration, UnexpectedColumnMode, load_tabular_file
from polaris.ingestion.models import ValidationFindingCode, ValidationSeverity
from polaris.ingestion.validation import map_manifest_columns
from polaris.schemas.common import DataType
from tests.ingestion.helpers import manifest_with_variables, variable, write_csv


def test_mapping_by_declared_source_field_name(tmp_path: Path) -> None:
    manifest = manifest_with_variables(
        [variable("canonical", DataType.FLOAT, source_field_name="SOURCE_FIELD")]
    )
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["SOURCE_FIELD"], ["1.2"]]),
        IngestionConfiguration(),
    )

    mappings, missing, unexpected, findings = map_manifest_columns(
        manifest, loaded, IngestionConfiguration()
    )

    assert mappings[0].variable_id == "canonical"
    assert mappings[0].source_column == "SOURCE_FIELD"
    assert missing == ()
    assert unexpected == ()
    assert findings == ()


def test_fallback_to_variable_id_when_source_field_absent(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("canonical", DataType.FLOAT)])
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["canonical"], ["1.2"]]),
        IngestionConfiguration(),
    )

    mappings, _, _, _ = map_manifest_columns(manifest, loaded, IngestionConfiguration())

    assert mappings[0].source_column == "canonical"


def test_missing_required_column_is_error(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("canonical", DataType.FLOAT)])
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["other"], ["1.2"]]),
        IngestionConfiguration(),
    )

    _, missing, _, findings = map_manifest_columns(manifest, loaded, IngestionConfiguration())

    assert missing == ("canonical",)
    assert findings[0].code is ValidationFindingCode.MISSING_REQUIRED_COLUMN


def test_unexpected_column_strict_and_permissive(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("canonical", DataType.FLOAT)])
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["canonical", "extra"], ["1.2", "x"]]),
        IngestionConfiguration(),
    )

    _, _, strict_unexpected, strict_findings = map_manifest_columns(
        manifest, loaded, IngestionConfiguration()
    )
    _, _, permissive_unexpected, permissive_findings = map_manifest_columns(
        manifest,
        loaded,
        IngestionConfiguration(unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE),
    )

    assert strict_unexpected == ("extra",)
    assert strict_findings[0].severity is ValidationSeverity.ERROR
    assert permissive_unexpected == ("extra",)
    assert permissive_findings[0].severity is ValidationSeverity.WARNING


def test_ambiguous_mapping_rejected(tmp_path: Path) -> None:
    manifest = manifest_with_variables(
        [
            variable("first", DataType.FLOAT, source_field_name="same"),
            variable("second", DataType.FLOAT, source_field_name="same"),
        ]
    )
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["same"], ["1.2"]]),
        IngestionConfiguration(),
    )

    _, _, _, findings = map_manifest_columns(manifest, loaded, IngestionConfiguration())

    assert findings[0].code is ValidationFindingCode.AMBIGUOUS_COLUMN_MAPPING


def test_no_fuzzy_matching(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("life_expectancy", DataType.FLOAT)])
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["Life Expectancy"], ["70.1"]]),
        IngestionConfiguration(),
    )

    _, missing, _, findings = map_manifest_columns(manifest, loaded, IngestionConfiguration())

    assert missing == ("life_expectancy",)
    assert any(
        finding.code is ValidationFindingCode.MISSING_REQUIRED_COLUMN for finding in findings
    )

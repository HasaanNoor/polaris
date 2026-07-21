from pathlib import Path

from polaris.ingestion import IngestionConfiguration, load_tabular_file
from polaris.ingestion.models import ValidationFindingCode
from polaris.ingestion.normalization import normalize_rows, normalize_value
from polaris.ingestion.validation import map_manifest_columns
from polaris.schemas.common import DataType
from polaris.schemas.dataset import DatasetVariable
from tests.ingestion.helpers import manifest_with_variables, variable, write_csv


def _variable(data_type: DataType) -> DatasetVariable:
    return DatasetVariable.model_validate(
        {
            "variable_id": "value",
            "label": "Value",
            "data_type": data_type,
            "role": "predictor",
        }
    )


def test_whitespace_and_null_token_handling() -> None:
    value, finding = normalize_value(
        raw_value="  text  ",
        variable=_variable(DataType.STRING),
        configuration=IngestionConfiguration(),
        source_path="source.csv",
        row_number=1,
        source_column="value",
        null_tokens=(),
    )
    null_value, null_finding = normalize_value(
        raw_value="..",
        variable=_variable(DataType.FLOAT),
        configuration=IngestionConfiguration(),
        source_path="source.csv",
        row_number=2,
        source_column="value",
        null_tokens=("..",),
    )

    assert value == "text"
    assert finding is None
    assert null_value is None
    assert null_finding is None


def test_integer_float_boolean_and_zero_conversion() -> None:
    assert _normalized("0", DataType.INTEGER) == 0
    assert _normalized("1.5", DataType.FLOAT) == 1.5
    assert _normalized("false", DataType.BOOLEAN) is False


def test_invalid_integer_and_no_silent_rounding() -> None:
    value, finding = _normalize("1.2", DataType.INTEGER)

    assert value is None
    assert finding is not None
    assert finding.code is ValidationFindingCode.INVALID_VALUE_TYPE
    assert finding.raw_value == "1.2"


def test_invalid_float_and_locale_parsing_rejected() -> None:
    _, finding = _normalize("1,200.5", DataType.FLOAT)

    assert finding is not None
    assert finding.raw_value == "1,200.5"


def test_strict_boolean_conversion() -> None:
    _, finding = _normalize("yes", DataType.BOOLEAN)

    assert finding is not None
    assert finding.code is ValidationFindingCode.INVALID_VALUE_TYPE


def test_normalize_rows_rejects_invalid_rows(tmp_path: Path) -> None:
    manifest = manifest_with_variables([variable("value", DataType.INTEGER)])
    loaded = load_tabular_file(
        write_csv(tmp_path / "data.csv", [["value"], ["1"], ["bad"]]),
        IngestionConfiguration(),
    )
    mappings, _, _, _ = map_manifest_columns(manifest, loaded, IngestionConfiguration())

    records, findings = normalize_rows(manifest, loaded, mappings, IngestionConfiguration())

    assert len(records) == 1
    assert records[0].values == {"value": 1}
    assert findings[0].row_number == 2
    assert findings[0].raw_value == "bad"


def _normalized(raw_value: str, data_type: DataType) -> object:
    value, finding = _normalize(raw_value, data_type)
    assert finding is None
    return value


def _normalize(raw_value: str, data_type: DataType) -> tuple[object, object]:
    return normalize_value(
        raw_value=raw_value,
        variable=_variable(data_type),
        configuration=IngestionConfiguration(),
        source_path="source.csv",
        row_number=1,
        source_column="value",
        null_tokens=(),
    )

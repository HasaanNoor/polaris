from __future__ import annotations

from pathlib import Path
from typing import Any

from polaris.harmonization import (
    DatasetHarmonizationConfig,
    HarmonizationRequest,
    JoinType,
    VariableMapping,
)
from polaris.ingestion import (
    IngestionConfiguration,
    IngestionRequest,
    UnexpectedColumnMode,
    ingest_dataset,
)
from polaris.ingestion.models import DatasetIngestionResult
from polaris.registry import DatasetRegistry
from polaris.schemas.common import DatasetStatus, DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest


def write_csv(path: Path, rows: list[list[str]]) -> Path:
    path.write_text("\n".join(",".join(row) for row in rows) + "\n", encoding="utf-8")
    return path


def manifest(
    *,
    dataset_id: str,
    provider: str,
    variables: list[dict[str, Any]],
) -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": dataset_id,
            "title": dataset_id,
            "provider": provider,
            "source_url": "https://example.test/source",
            "status": DatasetStatus.REVIEWED_CANDIDATE,
            "geographic_coverage": {"codes": ["GLOBAL"]},
            "temporal_coverage": {"start": 2019, "end": 2021},
            "variables": variables,
            "frequency": "annual",
        }
    )


def variable(
    variable_id: str,
    data_type: DataType,
    *,
    source_field_name: str | None = None,
    role: VariableRole = VariableRole.PREDICTOR,
    unit: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "variable_id": variable_id,
        "label": variable_id.replace("_", " ").title(),
        "data_type": data_type,
        "role": role,
    }
    if source_field_name is not None:
        payload["source_field_name"] = source_field_name
    if unit is not None:
        payload["unit"] = unit
    return payload


def ingest(path: Path, dataset_manifest: DatasetManifest) -> DatasetIngestionResult:
    return ingest_dataset(
        registry=DatasetRegistry((dataset_manifest,)),
        request=IngestionRequest(
            dataset_id=dataset_manifest.dataset_id,
            source_path=path,
            configuration=IngestionConfiguration(
                unexpected_column_mode=UnexpectedColumnMode.PERMISSIVE,
            ),
        ),
    )


def wdi_result(tmp_path: Path, rows: list[list[str]] | None = None) -> DatasetIngestionResult:
    data = rows or [
        ["country_code", "country_name", "year", "gdp", "fertility"],
        ["PAK", "Pakistan", "2020", "1500", "3.4"],
        ["IND", "India", "2020", "1900", "2.1"],
        ["WLD", "World", "2020", "11000", ""],
    ]
    path = write_csv(tmp_path / "wdi.csv", data)
    dataset_manifest = manifest(
        dataset_id="wdi",
        provider="World Bank",
        variables=[
            variable("country_code", DataType.STRING, role=VariableRole.IDENTIFIER),
            variable("country_name", DataType.STRING, role=VariableRole.IDENTIFIER),
            variable("year", DataType.INTEGER, role=VariableRole.TIME),
            variable("gdp", DataType.FLOAT, unit="current US dollars"),
            variable("fertility", DataType.FLOAT, unit="births per woman"),
        ],
    )
    return ingest(path, dataset_manifest)


def who_result(tmp_path: Path, rows: list[list[str]] | None = None) -> DatasetIngestionResult:
    data = rows or [
        [
            "SpatialDimValueCode",
            "Location",
            "Period",
            "IndicatorCode",
            "Dim1ValueCode",
            "FactValueNumeric",
        ],
        ["PAK", "Pakistan", "2020", "WHOSIS_000001", "SEX_BTSX", "66.1"],
        ["IND", "India", "2020", "WHOSIS_000001", "SEX_BTSX", "70.1"],
        ["PAK", "Pakistan", "2020", "WHOSIS_000001", "SEX_MLE", "65.0"],
        ["PAK", "Pakistan", "2021", "WHOSIS_000001", "SEX_BTSX", "66.3"],
    ]
    path = write_csv(tmp_path / "who.csv", data)
    dataset_manifest = manifest(
        dataset_id="who",
        provider="WHO",
        variables=[
            variable(
                "location_code",
                DataType.STRING,
                source_field_name="SpatialDimValueCode",
                role=VariableRole.IDENTIFIER,
            ),
            variable("location", DataType.STRING, source_field_name="Location"),
            variable(
                "period",
                DataType.INTEGER,
                source_field_name="Period",
                role=VariableRole.TIME,
            ),
            variable("indicator_code", DataType.STRING, source_field_name="IndicatorCode"),
            variable("sex_code", DataType.STRING, source_field_name="Dim1ValueCode"),
            variable(
                "fact_value_numeric",
                DataType.FLOAT,
                source_field_name="FactValueNumeric",
                unit="years",
            ),
        ],
    )
    return ingest(path, dataset_manifest)


def request_for(
    wdi: DatasetIngestionResult,
    who: DatasetIngestionResult,
    *,
    join_type: JoinType = JoinType.LEFT,
) -> HarmonizationRequest:
    return HarmonizationRequest(
        ingestion_results=(wdi, who),
        dataset_configs=(
            DatasetHarmonizationConfig(
                dataset_id="wdi",
                alias="wdi",
                provider="world_bank",
                country_field="country_code",
                country_name_field="country_name",
                year_field="year",
            ),
            DatasetHarmonizationConfig(
                dataset_id="who",
                alias="who",
                provider="who",
                country_field="SpatialDimValueCode",
                country_name_field="Location",
                year_field="Period",
            ),
        ),
        variable_mappings=(
            VariableMapping(
                source_dataset_id="wdi",
                source_provider="world_bank",
                source_variable_id="gdp",
                source_field_name="gdp",
                canonical_variable_id="wdi_gdp_per_capita_current_usd",
                canonical_label="GDP per capita, current US dollars",
                source_unit="current US dollars",
                canonical_unit="current US dollars",
                conceptual_definition="WDI GDP per capita in current US dollars.",
                expected_data_type="float",
            ),
            VariableMapping(
                source_dataset_id="who",
                source_provider="who",
                source_variable_id="fact_value_numeric",
                source_field_name="FactValueNumeric",
                canonical_variable_id="who_life_expectancy_at_birth_both_sexes",
                canonical_label="WHO life expectancy at birth, both sexes",
                source_unit="years",
                canonical_unit="years",
                conceptual_definition="WHO life expectancy at birth for both sexes, in years.",
                expected_data_type="float",
                row_filters={
                    "IndicatorCode": "WHOSIS_000001",
                    "Dim1ValueCode": "SEX_BTSX",
                },
            ),
        ),
        join_type=join_type,
        anchor_dataset_id="wdi" if join_type is JoinType.LEFT else None,
    )

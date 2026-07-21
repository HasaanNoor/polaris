from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from polaris.schemas.common import DatasetStatus, DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest

DATA_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "examples"


def write_csv(path: Path, rows: list[list[str]]) -> Path:
    path.write_text("\n".join(",".join(row) for row in rows) + "\n", encoding="utf-8")
    return path


def manifest_with_variables(
    variables: list[dict[str, Any]],
    *,
    dataset_id: str = "test_dataset",
) -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": dataset_id,
            "title": "Test Dataset",
            "provider": "Test Provider",
            "source_url": "https://example.test/source",
            "status": DatasetStatus.CANDIDATE,
            "geographic_coverage": {"codes": ["TEST"]},
            "temporal_coverage": {"start": 2020, "end": 2021},
            "variables": variables,
        }
    )


def variable(
    variable_id: str,
    data_type: DataType,
    *,
    source_field_name: str | None = None,
    role: VariableRole = VariableRole.PREDICTOR,
    missing: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "variable_id": variable_id,
        "label": variable_id.replace("_", " ").title(),
        "data_type": data_type,
        "role": role,
    }
    if source_field_name is not None:
        payload["source_field_name"] = source_field_name
    if missing is not None:
        payload["missing_value_representation"] = missing
    return payload


def manifest_data_copy(manifest: DatasetManifest) -> dict[str, Any]:
    return deepcopy(manifest.model_dump(mode="json"))

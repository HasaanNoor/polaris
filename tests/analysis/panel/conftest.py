from pathlib import Path
from typing import Any

import pytest

from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.schemas.common import DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.statistics import StatisticalSpecification


@pytest.fixture
def panel_ingestion(tmp_path: Path):
    path = tmp_path / "panel.csv"
    rows = [["entity", "year", "y", "x", "z", "time_invariant", "label"]]
    entity_effects = {"A": 10.0, "B": -4.0, "C": 3.0, "D": 7.0}
    year_effects = {2020: -2.0, 2021: -1.0, 2022: 1.0, 2023: 2.0}
    invariant = {"A": 1.0, "B": 2.0, "C": 3.0, "D": 4.0}
    for entity_index, entity in enumerate(("A", "B", "C", "D"), start=1):
        for year in (2020, 2021, 2022, 2023):
            trend = year - 2019
            x = float(entity_index * trend)
            z = float((entity_index + trend) % 3)
            noise = float(((entity_index * trend) % 5) - 2) / 10.0
            y = 2.0 * x + 0.5 * z + entity_effects[entity] + year_effects[year] + noise
            rows.append(
                [entity, str(year), f"{y:.6f}", f"{x:.6f}", f"{z:.6f}", invariant[entity], entity]
            )
    path.write_text("\n".join(",".join(map(str, row)) for row in rows) + "\n", encoding="utf-8")
    return ingest_dataset(
        registry=DatasetRegistry((_panel_manifest(),)),
        request=IngestionRequest(dataset_id="panel_dataset", source_path=path),
    )


def panel_spec(
    *,
    procedure: str = "panel_two_way_fe",
    exposures: list[str] | None = None,
    covariates: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> StatisticalSpecification:
    payload: dict[str, Any] = {
        "specification_id": f"spec_{procedure}",
        "investigation_id": "investigation_panel",
        "analysis_type": "regression",
        "model_family": "linear",
        "procedure": procedure,
        "outcome_variable": {"variable_id": "y"},
        "exposure_variables": [{"variable_id": value} for value in (exposures or ["x"])],
        "covariates": [{"variable_id": value} for value in (covariates or [])],
        "entity_variable": {"variable_id": "entity"},
        "time_variable": {"variable_id": "year"},
        "fixed_effects": [{"variable_id": "entity"}, {"variable_id": "year"}],
        "unit_of_analysis": "entity-year",
        "missing_data_strategy": {"strategy": "complete_case", "rationale": "panel tests"},
        "standard_error_strategy": {
            "strategy": "cluster_robust",
            "cluster_variables": [{"variable_id": "entity"}],
        },
        "confidence_level": 0.95,
        "causal_identification_claim_level": "associational",
    }
    if procedure == "panel_entity_fe":
        payload["fixed_effects"] = [{"variable_id": "entity"}]
    if procedure == "first_difference":
        payload["fixed_effects"] = []
    if extra:
        payload.update(extra)
    return StatisticalSpecification.model_validate(payload)


def _panel_manifest() -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": "panel_dataset",
            "title": "Panel Dataset",
            "provider": "Test Provider",
            "source_url": "https://example.test/panel",
            "status": "candidate",
            "geographic_coverage": {"codes": ["TEST"]},
            "temporal_coverage": {"start": 2020, "end": 2023},
            "variables": [
                _variable("entity", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("year", DataType.INTEGER, VariableRole.TIME),
                _variable("y", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("x", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("z", DataType.FLOAT, VariableRole.COVARIATE),
                _variable("time_invariant", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("label", DataType.CATEGORICAL, VariableRole.GROUPING),
            ],
        }
    )


def _variable(variable_id: str, data_type: DataType, role: VariableRole) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "label": variable_id,
        "data_type": data_type,
        "role": role,
    }

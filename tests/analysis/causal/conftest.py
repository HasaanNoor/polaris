from pathlib import Path
from typing import Any

import pytest

from polaris.analysis.causal.models import CausalSpecification
from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.schemas.common import DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.statistics import StatisticalSpecification


@pytest.fixture
def causal_ingestion(tmp_path: Path):
    return synthetic_causal_ingestion(tmp_path)


def synthetic_causal_ingestion(
    tmp_path: Path,
    *,
    effect: float = 3.0,
    pretrend: bool = False,
    anticipation: bool = False,
    missing_pre_entity: str | None = None,
    no_controls: bool = False,
    staggered: bool = False,
):
    path = tmp_path / "synthetic_causal_panel.csv"
    rows = [["entity", "year", "outcome", "treated", "treat_start", "post_control"]]
    entities = ("A", "B", "C", "D", "E", "F")
    treated_entities = {"A", "B", "C"} if not no_controls else set(entities)
    entity_effect = {entity: float(index) for index, entity in enumerate(entities)}
    year_effect = {2018: -2.0, 2019: -1.0, 2020: 0.0, 2021: 1.0, 2022: 2.0}
    for entity in entities:
        for year in (2018, 2019, 2020, 2021, 2022):
            if entity == missing_pre_entity and year < 2020:
                continue
            treated = entity in treated_entities
            start = 2021.0 if staggered and entity == "C" else 2020.0
            y = entity_effect[entity] + year_effect[year]
            if pretrend and treated and year < 2020:
                y += 1.5 * (year - 2018)
            if anticipation and treated and year == 2019:
                y += effect / 2
            if treated and year >= start:
                y += effect
            post_control = (
                float((entities.index(entity) + 1) * (year - 2017))
                if treated and year >= start
                else 0.0
            )
            rows.append([entity, year, f"{y:.6f}", int(treated), f"{start:.1f}", post_control])
    path.write_text("\n".join(",".join(map(str, row)) for row in rows) + "\n", encoding="utf-8")
    return ingest_dataset(
        registry=DatasetRegistry((_manifest(),)),
        request=IngestionRequest(dataset_id="synthetic_causal_panel", source_path=path),
    )


def causal_spec(
    *,
    method: str = "difference_in_differences",
    covariates: tuple[str, ...] = (),
    event: bool = False,
    extra: dict[str, Any] | None = None,
) -> CausalSpecification:
    payload: dict[str, Any] = {
        "specification_id": f"causal_spec_{method}",
        "investigation_id": "causal_investigation",
        "method": method,
        "entity_variable": {"variable_id": "entity"},
        "time_variable": {"variable_id": "year"},
        "outcome_variable": {"variable_id": "outcome"},
        "treatment": {
            "treatment_variable": {"variable_id": "treated"},
            "treated_value": 1,
            "control_value": 0,
            "treatment_start_period": 2020,
            "treatment_timing_variable": {"variable_id": "treat_start"},
            "treatment_source": "synthetic_test_fixture",
        },
        "treated_group_description": "synthetic treated entities A-C",
        "comparison_group_description": "synthetic never-treated entities D-F",
        "pre_treatment_window": (2018, 2019),
        "post_treatment_window": (2020, 2022),
        "covariates": [{"variable_id": item} for item in covariates],
        "fixed_effects": {"entity_fixed_effects": True, "time_fixed_effects": True},
        "standard_error_strategy": {
            "strategy": "cluster_robust",
            "cluster_variables": [{"variable_id": "entity"}],
        },
        "estimand": "att",
        "confidence_level": 0.95,
    }
    if event:
        payload["method"] = "event_study"
        payload["event_study"] = {
            "min_event_time": -2,
            "max_event_time": 2,
            "reference_event_time": -1,
        }
    if extra:
        payload.update(extra)
    return CausalSpecification.model_validate(payload)


def statistical_spec() -> StatisticalSpecification:
    return StatisticalSpecification.model_validate(
        {
            "specification_id": "ordinary_spec_for_causal_project",
            "investigation_id": "causal_investigation",
            "analysis_type": "regression",
            "model_family": "linear",
            "procedure": "ordinary_least_squares",
            "outcome_variable": {"variable_id": "outcome"},
            "exposure_variables": [{"variable_id": "treated"}],
            "unit_of_analysis": "entity-year",
            "missing_data_strategy": {"strategy": "complete_case", "rationale": "test"},
            "confidence_level": 0.95,
            "causal_identification_claim_level": "associational",
        }
    )


def _manifest() -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": "synthetic_causal_panel",
            "title": "Synthetic Causal Panel",
            "provider": "Polaris tests",
            "source_url": "https://example.test/synthetic-causal",
            "status": "candidate",
            "geographic_coverage": {"codes": ["SYN"]},
            "temporal_coverage": {"start": 2018, "end": 2022},
            "variables": [
                _variable("entity", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("year", DataType.INTEGER, VariableRole.TIME),
                _variable("outcome", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("treated", DataType.INTEGER, VariableRole.EXPOSURE),
                _variable("treat_start", DataType.FLOAT, VariableRole.TIME),
                _variable("post_control", DataType.FLOAT, VariableRole.COVARIATE),
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

from pathlib import Path
from typing import Any

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis
from polaris.ingestion.models import IngestionRequest
from polaris.ingestion.service import ingest_dataset
from polaris.registry import DatasetRegistry
from polaris.schemas.common import DataType, VariableRole
from polaris.schemas.dataset import DatasetManifest
from polaris.schemas.statistics import StatisticalSpecification


def make_spec(
    *,
    procedure: str,
    analysis_type: str = "regression",
    model_family: str = "linear",
    outcome: str = "y",
    exposures: list[str] | None = None,
    covariates: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> StatisticalSpecification:
    payload: dict[str, Any] = {
        "specification_id": f"spec_{procedure}",
        "investigation_id": "investigation_evidence",
        "analysis_type": analysis_type,
        "model_family": model_family,
        "procedure": procedure,
        "outcome_variable": {"variable_id": outcome},
        "exposure_variables": [{"variable_id": value} for value in (exposures or [])],
        "covariates": [{"variable_id": value} for value in (covariates or [])],
        "unit_of_analysis": "row",
        "missing_data_strategy": {
            "strategy": "complete_case",
            "rationale": "Phase 5 test complete-case policy",
        },
        "confidence_level": 0.95,
        "causal_identification_claim_level": "associational",
    }
    if extra:
        payload.update(extra)
    return StatisticalSpecification.model_validate(payload)


def make_manifest() -> DatasetManifest:
    return DatasetManifest.model_validate(
        {
            "dataset_id": "evidence_dataset",
            "title": "Evidence Dataset",
            "provider": "Test Provider",
            "source_url": "https://example.test/evidence",
            "status": "candidate",
            "geographic_coverage": {"codes": ["TEST"]},
            "temporal_coverage": {"start": 2020, "end": 2021},
            "variables": [
                _variable("row_id", DataType.STRING, VariableRole.IDENTIFIER),
                _variable("y", DataType.FLOAT, VariableRole.OUTCOME),
                _variable("x", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("negative_x", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("z", DataType.FLOAT, VariableRole.COVARIATE),
                _variable("constant", DataType.FLOAT, VariableRole.PREDICTOR),
                _variable("category", DataType.CATEGORICAL, VariableRole.GROUPING),
                _variable("flag", DataType.BOOLEAN, VariableRole.QUALITY_FLAG),
            ],
        }
    )


def ingest_fixture(tmp_path: Path):
    path = tmp_path / "evidence.csv"
    path.write_text(
        "\n".join(
            [
                "row_id,y,x,negative_x,z,constant,category,flag",
                "a,3,1,9,10,5,A,true",
                "b,5,2,8,20,5,A,false",
                "c,7,3,7,30,5,B,true",
                "d,9,4,6,40,5,B,false",
                "e,11,5,5,50,5,B,true",
                "f,,6,4,60,5,C,false",
                "g,15,7,3,,5,C,true",
                "h,17,8,2,80,5,C,false",
                "i,19,9,1,90,5,D,true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return ingest_dataset(
        registry=DatasetRegistry((make_manifest(),)),
        request=IngestionRequest(dataset_id="evidence_dataset", source_path=path),
    )


def run_fixture_analysis(
    ingestion,
    *,
    procedure: str,
    analysis_type: str,
    model_family: str = "none",
    outcome: str = "y",
    exposures: list[str] | None = None,
    covariates: list[str] | None = None,
    significance_threshold: float | None = None,
):
    return run_analysis(
        request=AnalysisRequest(
            ingestion_result=ingestion,
            statistical_specification=make_spec(
                procedure=procedure,
                analysis_type=analysis_type,
                model_family=model_family,
                outcome=outcome,
                exposures=exposures,
                covariates=covariates,
            ),
            significance_threshold=significance_threshold,
        )
    )


def _variable(variable_id: str, data_type: DataType, role: VariableRole) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "label": variable_id,
        "data_type": data_type,
        "role": role,
    }

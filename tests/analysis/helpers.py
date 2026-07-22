from typing import Any

from polaris.schemas.statistics import StatisticalSpecification


def make_spec(
    *,
    procedure: str,
    analysis_type: str = "regression",
    model_family: str = "linear",
    outcome: str = "y",
    exposures: list[str] | None = None,
    covariates: list[str] | None = None,
    claim_level: str = "associational",
    extra: dict[str, Any] | None = None,
) -> StatisticalSpecification:
    payload: dict[str, Any] = {
        "specification_id": f"spec_{procedure}",
        "investigation_id": "investigation_analysis",
        "analysis_type": analysis_type,
        "model_family": model_family,
        "procedure": procedure,
        "outcome_variable": {"variable_id": outcome},
        "exposure_variables": [{"variable_id": value} for value in (exposures or [])],
        "covariates": [{"variable_id": value} for value in (covariates or [])],
        "unit_of_analysis": "row",
        "missing_data_strategy": {
            "strategy": "complete_case",
            "rationale": "Phase 4 initial deterministic policy",
        },
        "confidence_level": 0.95,
        "causal_identification_claim_level": claim_level,
    }
    if extra:
        payload.update(extra)
    return StatisticalSpecification.model_validate(payload)

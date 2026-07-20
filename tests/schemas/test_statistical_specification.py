import pytest
from pydantic import ValidationError

from polaris.schemas.common import CausalIdentificationLevel, StatisticalAnalysisType
from polaris.schemas.statistics import StatisticalSpecification


def test_valid_statistical_specification_creation(example_data):
    spec = StatisticalSpecification.model_validate(example_data["statistical_specification"])

    assert spec.analysis_type == StatisticalAnalysisType.REGRESSION
    assert spec.causal_identification_claim_level == CausalIdentificationLevel.ASSOCIATIONAL


def test_statistical_specification_json_round_trip(example_data):
    spec = StatisticalSpecification.model_validate(example_data["statistical_specification"])

    assert StatisticalSpecification.model_validate_json(spec.model_dump_json()) == spec


def test_statistical_specification_rejects_unknown_fields(example_data, copy_data):
    data = copy_data(example_data["statistical_specification"])
    data["p_value_claim"] = "causal"

    with pytest.raises(ValidationError):
        StatisticalSpecification.model_validate(data)


def test_statistical_specification_rejects_invalid_confidence_level(example_data, copy_data):
    data = copy_data(example_data["statistical_specification"])
    data["confidence_level"] = 1.2

    with pytest.raises(ValidationError):
        StatisticalSpecification.model_validate(data)


def test_regression_specification_requires_predictor_fields(example_data, copy_data):
    data = copy_data(example_data["statistical_specification"])
    data["exposure_variables"] = []

    with pytest.raises(ValidationError):
        StatisticalSpecification.model_validate(data)


def test_descriptive_specification_does_not_require_regression_fields(example_data, copy_data):
    data = copy_data(example_data["statistical_specification"])
    data["analysis_type"] = "descriptive"
    data["model_family"] = "none"
    data["exposure_variables"] = []
    data["covariates"] = []
    data["fixed_effects"] = []
    data["standard_error_strategy"] = None
    data["causal_identification_claim_level"] = "descriptive_only"

    spec = StatisticalSpecification.model_validate(data)

    assert spec.analysis_type == StatisticalAnalysisType.DESCRIPTIVE
    assert spec.exposure_variables == []


def test_statistical_specification_requires_identifier(example_data, copy_data):
    data = copy_data(example_data["statistical_specification"])
    del data["specification_id"]

    with pytest.raises(ValidationError):
        StatisticalSpecification.model_validate(data)

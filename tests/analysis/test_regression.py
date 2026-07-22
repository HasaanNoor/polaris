import pytest
from helpers import make_spec

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis


def test_known_ols_linear_relationship(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
            ),
            significance_threshold=0.05,
        )
    )
    regression = result.method_result

    assert regression.sample_size == 8
    assert regression.include_intercept is True
    assert regression.r_squared == pytest.approx(1.0)
    assert regression.coefficients[0].term == "intercept"
    assert regression.coefficients[0].estimate == pytest.approx(1.0)
    assert regression.coefficients[1].estimate == pytest.approx(2.0)
    assert regression.residual_sum_of_squares == pytest.approx(0.0, abs=1e-10)
    payload = result.model_dump_json().lower()
    assert "claim causation" not in payload
    assert "significant effect" not in payload
    assert "important predictor" not in payload


def test_ols_with_control_and_missing_exclusion(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
                covariates=["z"],
            ),
        )
    )

    assert result.method_result.sample_size == 7
    assert result.analysis_sample.excluded_row_numbers == (6, 7)


def test_singular_matrix_warns(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x", "x_duplicate"],
            ),
        )
    )

    assert result.method_result.warnings[0].code == "singular_design_matrix"


def test_deterministic_result_identifier(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="ordinary_least_squares",
            exposures=["x"],
        ),
    )

    assert run_analysis(request=request).result_id == run_analysis(request=request).result_id

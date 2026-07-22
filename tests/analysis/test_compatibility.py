import pytest
from helpers import make_spec

from polaris.analysis.errors import (
    AnalysisCompatibilityError,
    InsufficientSampleError,
    UnsupportedAnalysisMethodError,
    VariableNotFoundError,
    VariableTypeError,
)
from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis


def test_unknown_variable_rejected(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="ordinary_least_squares",
            exposures=["missing"],
        ),
    )

    with pytest.raises(VariableNotFoundError):
        run_analysis(request=request)


def test_duplicate_predictor_rejected(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="ordinary_least_squares",
            exposures=["x", "x"],
        ),
    )

    with pytest.raises(AnalysisCompatibilityError):
        run_analysis(request=request)


def test_dependent_variable_cannot_be_predictor(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="ordinary_least_squares",
            exposures=["y"],
        ),
    )

    with pytest.raises(AnalysisCompatibilityError):
        run_analysis(request=request)


def test_non_numeric_correlation_rejected(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="pearson_correlation",
            analysis_type="correlation",
            model_family="none",
            exposures=["category"],
        ),
    )

    with pytest.raises(VariableTypeError):
        run_analysis(request=request)


def test_unsupported_logistic_deferred(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="binary_logistic_regression",
            model_family="logistic",
            exposures=["x"],
        ),
    )

    with pytest.raises(UnsupportedAnalysisMethodError):
        run_analysis(request=request)


def test_unsupported_weighting_rejected(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="ordinary_least_squares",
            exposures=["x"],
            extra={"weighting": {"weight_variable": {"variable_id": "z"}, "description": "w"}},
        ),
    )

    with pytest.raises(UnsupportedAnalysisMethodError):
        run_analysis(request=request)


def test_insufficient_sample_rejected(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="ordinary_least_squares",
            exposures=["x", "z", "constant", "x_duplicate"],
        ),
    )

    with pytest.raises(InsufficientSampleError):
        run_analysis(request=request)

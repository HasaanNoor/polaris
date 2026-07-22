import math

import pytest
from helpers import make_spec
from pydantic import ValidationError

from polaris.analysis.models import AnalysisFinding, AnalysisRequest


def test_valid_request_is_immutable(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="ordinary_least_squares",
            exposures=["x"],
            covariates=[],
        ),
    )

    with pytest.raises(ValidationError):
        request.significance_threshold = 0.1


def test_request_rejects_unknown_field(analysis_ingestion):
    with pytest.raises(ValidationError):
        AnalysisRequest.model_validate(
            {
                "ingestion_result": analysis_ingestion,
                "statistical_specification": make_spec(
                    procedure="ordinary_least_squares",
                    exposures=["x"],
                ),
                "unknown": True,
            }
        )


def test_request_rejects_invalid_thresholds(analysis_ingestion):
    with pytest.raises(ValidationError):
        AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
            ),
            significance_threshold=1.0,
        )


def test_findings_reject_nan_and_infinity():
    with pytest.raises(ValidationError):
        AnalysisFinding(
            severity="warning",
            code="undefined_statistic",
            message="bad",
            statistic=math.nan,
        )

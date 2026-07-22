from helpers import make_spec

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis


def test_numeric_descriptive_statistics(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="descriptive_statistics",
                analysis_type="descriptive",
                model_family="none",
                outcome="x",
            ),
        )
    )
    summary = result.method_result.variables[0].numeric

    assert summary is not None
    assert summary.count == 9
    assert summary.mean == 5.0
    assert summary.minimum == 1.0
    assert summary.percentile_25 == 3.0
    assert summary.median == 5.0
    assert summary.percentile_75 == 7.0
    assert summary.maximum == 9.0


def test_categorical_descriptive_statistics(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="descriptive_statistics",
                analysis_type="descriptive",
                model_family="none",
                outcome="category",
            ),
        )
    )
    summary = result.method_result.variables[0].categorical

    assert summary is not None
    assert summary.count == 9
    assert summary.unique_count == 4
    assert summary.most_frequent_value == "B"
    assert summary.most_frequent_value_count == 3


def test_constant_variable_finding(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="descriptive_statistics",
                analysis_type="descriptive",
                model_family="none",
                outcome="constant",
            ),
        )
    )

    assert result.method_result.variables[0].findings[0].code == "constant_variable"

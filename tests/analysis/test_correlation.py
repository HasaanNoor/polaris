import pytest
from helpers import make_spec

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis


def test_perfect_positive_pearson(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="pearson_correlation",
                analysis_type="correlation",
                model_family="none",
                exposures=["x"],
            ),
        )
    )
    pair = result.method_result.pairs[0]

    assert pair.defined is True
    assert pair.correlation_coefficient == pytest.approx(1.0)
    assert pair.excluded_row_numbers == (6,)
    assert pair.warnings[0].code == "perfect_correlation"


def test_perfect_negative_pearson(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="pearson_correlation",
                analysis_type="correlation",
                model_family="none",
                outcome="y",
                exposures=["constant"],
            ),
        )
    )

    assert result.method_result.pairs[0].defined is False


def test_spearman_and_pair_order(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="spearman_correlation",
                analysis_type="correlation",
                model_family="none",
                outcome="y",
                exposures=["x", "z"],
            ),
        )
    )

    assert [(pair.variable_id_1, pair.variable_id_2) for pair in result.method_result.pairs] == [
        ("y", "x"),
        ("y", "z"),
        ("x", "z"),
    ]
    assert all(pair.method == "spearman" for pair in result.method_result.pairs)

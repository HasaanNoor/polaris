from helpers import make_spec

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.sample import build_analysis_sample


def test_complete_case_sample_preserves_order_and_rows(analysis_ingestion):
    sample, findings = build_analysis_sample(analysis_ingestion, ("y", "x", "z"))

    assert sample.included_row_numbers == (1, 2, 3, 4, 5, 8, 9)
    assert tuple(exclusion.row_number for exclusion in sample.exclusions) == (6, 7)
    assert sample.rows[0]["x"] == 1.0
    assert any(finding.code == "excluded_missing_rows" for finding in findings)


def test_zero_values_are_retained(analysis_ingestion):
    sample, _ = build_analysis_sample(analysis_ingestion, ("constant",))

    assert sample.sample_size == 9
    assert all(row["constant"] == 5.0 for row in sample.rows)


def test_boolean_not_required_for_numeric_methods(analysis_ingestion):
    request = AnalysisRequest(
        ingestion_result=analysis_ingestion,
        statistical_specification=make_spec(
            procedure="descriptive_statistics",
            analysis_type="descriptive",
            model_family="none",
            outcome="flag",
        ),
    )

    assert request.statistical_specification.outcome_variable.variable_id == "flag"

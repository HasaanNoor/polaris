from helpers import make_spec

from polaris.analysis.models import AnalysisRequest
from polaris.analysis.service import run_analysis


def test_ols_diagnostics_include_expected_names(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x", "z"],
            ),
        )
    )
    names = [diagnostic.name for diagnostic in result.diagnostics]

    assert "condition_number" in names
    assert "variance_inflation_factor" in names
    assert "residual_normality" in names
    assert "breusch_pagan" in names
    assert "maximum_leverage" in names
    assert "durbin_watson" in names
    assert any("multicollinearity" in diagnostic.warning_codes for diagnostic in result.diagnostics)


def test_insufficient_sample_diagnostic_statuses(analysis_ingestion):
    result = run_analysis(
        request=AnalysisRequest(
            ingestion_result=analysis_ingestion,
            statistical_specification=make_spec(
                procedure="ordinary_least_squares",
                exposures=["x"],
            ),
        )
    )

    normality = next(
        diagnostic for diagnostic in result.diagnostics if diagnostic.name == "residual_normality"
    )
    assert normality.status in {"calculated", "not_applicable"}

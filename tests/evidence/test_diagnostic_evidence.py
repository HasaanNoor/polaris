from evidence_helpers import run_fixture_analysis

from polaris.evidence.models import DiagnosticEvidenceRecord, LimitationCode
from polaris.evidence.service import extract_evidence


def test_ols_diagnostics_are_evidence_records(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="y",
        exposures=["x"],
        covariates=["z"],
    )

    artifact = extract_evidence(analysis_result=result)
    diagnostics = [
        record
        for record in artifact.evidence_records
        if isinstance(record, DiagnosticEvidenceRecord)
    ]
    names = {record.diagnostic_type for record in diagnostics}

    assert "condition_number" in names
    assert "variance_inflation_factor" in names
    assert "residual_normality" in names
    assert "breusch_pagan" in names
    assert "maximum_leverage" in names
    assert "durbin_watson" in names
    assert all(record.source_analysis_result_id == result.result_id for record in diagnostics)


def test_undefined_or_not_applicable_diagnostics_produce_limitations(evidence_ingestion):
    result = run_fixture_analysis(
        evidence_ingestion,
        procedure="ordinary_least_squares",
        analysis_type="regression",
        model_family="linear",
        outcome="y",
        exposures=["x"],
    )

    artifact = extract_evidence(analysis_result=result)
    diagnostics = [
        record
        for record in artifact.evidence_records
        if isinstance(record, DiagnosticEvidenceRecord)
    ]

    assert any(
        record.diagnostic_type == "variance_inflation_factor"
        and LimitationCode.UNDEFINED_DIAGNOSTIC in record.limitation_codes
        for record in diagnostics
    )

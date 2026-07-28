import pytest

from polaris.reporting.errors import ReportCompatibilityError, ReportValidationError
from polaris.reporting.service import build_research_report
from polaris.reporting.validation import validate_report, validate_report_request


def test_matching_lineage_accepted(report_request):
    validate_report_request(report_request)


def test_mismatched_synthesis_rejected(report_request, reporting_pipeline):
    bad_synthesis = reporting_pipeline["synthesis"].model_copy(
        update={"source_coordinated_assessment_id": "other"}
    )
    with pytest.raises(ReportCompatibilityError):
        validate_report_request(
            report_request.model_copy(update={"synthesis_artifact": bad_synthesis})
        )


def test_mismatched_evidence_artifact_rejected(report_request, reporting_pipeline):
    bad_evidence = reporting_pipeline["evidence"].model_copy(update={"artifact_id": "other"})
    with pytest.raises(ReportCompatibilityError):
        validate_report_request(
            report_request.model_copy(update={"evidence_artifact": bad_evidence})
        )


def test_mismatched_analysis_rejected(report_request, reporting_pipeline):
    bad_analysis = reporting_pipeline["analysis"].model_copy(update={"result_id": "other"})
    with pytest.raises(ReportCompatibilityError):
        validate_report_request(report_request.model_copy(update={"analysis_result": bad_analysis}))


def test_mismatched_dataset_id_rejected(report_request, reporting_pipeline):
    bad_analysis = reporting_pipeline["analysis"].model_copy(update={"dataset_id": "other"})
    with pytest.raises(ReportCompatibilityError):
        validate_report_request(report_request.model_copy(update={"analysis_result": bad_analysis}))


def test_mismatched_checksum_rejected(report_request, reporting_pipeline):
    bad_analysis = reporting_pipeline["analysis"].model_copy(
        update={"source_checksum_sha256": "0" * 64}
    )
    with pytest.raises(ReportCompatibilityError):
        validate_report_request(report_request.model_copy(update={"analysis_result": bad_analysis}))


def test_incompatible_schema_version_rejected(report_request, reporting_pipeline):
    bad_analysis = reporting_pipeline["analysis"].model_copy(update={"schema_version": "2.0.0"})
    with pytest.raises(ReportCompatibilityError):
        validate_report_request(report_request.model_copy(update={"analysis_result": bad_analysis}))


def test_causal_language_rejected(report_request):
    report = build_research_report(request=report_request)
    bad = report.model_copy(update={"executive_summary": "Female literacy causes fertility."})
    with pytest.raises(ReportValidationError):
        validate_report(bad, report_request)
